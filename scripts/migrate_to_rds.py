"""Apply Alembic migrations and seed demo data against a remote RDS instance.

Usage (recommended when password contains @ or other special chars):

  PowerShell:
    $env:RDS_HOST="fieldintel-prod.cluster-xxxx.ap-southeast-2.rds.amazonaws.com"
    $env:RDS_USER="fieldintel"
    $env:RDS_PASSWORD=$passwordFromSecretsManager
    $env:RDS_DB="fieldintel"
    python scripts/migrate_to_rds.py --from-env --seed

Or pass flags (password still URL-encoded automatically):
    python scripts/migrate_to_rds.py --host HOST --user USER --password "p@ss" --seed

Do NOT paste the AWS Console presigned Connect URL into DATABASE_URL.

If you see "PAM authentication failed", the DB user requires IAM auth — use --iam-auth
(requires AWS CLI credentials with rds-db:connect), not the Secrets Manager password.

IAM auth checklist:
  - RDS_USER must match the IAM-enabled DB user (often "fieldintel", not your AWS login name)
  - RDS_HOST must be the same hostname used to generate the token (instance or cluster endpoint)
"""

from __future__ import annotations

import argparse
import getpass
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"


def _venv_dirs() -> list[Path]:
    """backend/.venv first, then repo-root .venv (common in CloudShell)."""
    dirs: list[Path] = []
    for path in (BACKEND_DIR / ".venv", ROOT / ".venv"):
        if path.is_dir() and path not in dirs:
            dirs.append(path)
    return dirs


def _venv_python(venv_dir: Path) -> Path:
    if sys.platform == "win32":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _ensure_venv_site_packages() -> None:
    for venv_dir in _venv_dirs():
        if sys.platform == "win32":
            site = venv_dir / "Lib" / "site-packages"
        else:
            import glob

            matches = glob.glob(str(venv_dir / "lib" / "python*/site-packages"))
            site = Path(matches[0]) if matches else venv_dir / "lib" / "site-packages"
        if site.is_dir() and str(site) not in sys.path:
            sys.path.insert(0, str(site))
            return


def generate_iam_auth_token(*, host: str, user: str, port: int, region: str) -> str:
    try:
        import boto3
    except ImportError:
        _ensure_venv_site_packages()
        import boto3

    client = boto3.client("rds", region_name=region)
    return client.generate_db_auth_token(
        DBHostname=host,
        Port=port,
        DBUsername=user,
        Region=region,
    )


def build_database_url(
    *,
    user: str,
    password: str,
    host: str,
    dbname: str,
    port: int = 5432,
) -> str:
    """Build a DATABASE_URL; SQLAlchemy encodes special chars safely (required for IAM tokens)."""
    try:
        from sqlalchemy.engine.url import URL
    except ImportError:
        _ensure_venv_site_packages()
        from sqlalchemy.engine.url import URL

    host = host.strip().removeprefix("https://").removeprefix("http://")
    if "/" in host:
        host = host.split("/")[0]
    url = URL.create(
        drivername="postgresql",
        username=user,
        password=password,
        host=host,
        port=port,
        database=dbname,
        query={"sslmode": "require"},
    )
    return url.render_as_string(hide_password=False)


def _backend_python() -> Path:
    for venv_dir in _venv_dirs():
        candidate = _venv_python(venv_dir)
        if candidate.is_file():
            return candidate
    try:
        import alembic  # noqa: F401

        return Path(sys.executable)
    except ImportError:
        pass
    print(
        "Backend venv not found. Create it under backend/ (recommended):\n"
        "  cd backend && python3 -m venv .venv && source .venv/bin/activate\n"
        "  pip install -r requirements.txt\n"
        "Or create .venv at the repo root and install backend/requirements.txt there.",
        file=sys.stderr,
    )
    sys.exit(1)


def _alembic_cmd(python: Path) -> list[str]:
    for venv_dir in _venv_dirs():
        if sys.platform == "win32":
            alembic_exe = venv_dir / "Scripts" / "alembic.exe"
        else:
            alembic_exe = venv_dir / "bin" / "alembic"
        if alembic_exe.is_file():
            return [str(alembic_exe)]
    return [str(python), "-m", "alembic"]


def _validate_database_url(url: str, *, built_from_parts: bool = False) -> None:
    # Console "Connect" links are https:// — never valid DATABASE_URL values.
    if url.startswith("https://") and "amazonaws.com" in url:
        print(
            "DATABASE_URL looks like an AWS Console presigned Connect URL.\n"
            "Use --from-env or --host/--user/--password instead.\n",
            file=sys.stderr,
        )
        sys.exit(1)
    if not built_from_parts and ("Action=connect" in url or "X-Amz-" in url):
        if not url.startswith("postgresql://") and not url.startswith("postgres://"):
            print(
                "DATABASE_URL looks like an AWS Console presigned URL.\n"
                "Use --from-env or --host/--user/--password instead.\n",
                file=sys.stderr,
            )
            sys.exit(1)
    if not url.startswith("postgresql://") and not url.startswith("postgres://"):
        print("DATABASE_URL must start with postgresql://", file=sys.stderr)
        sys.exit(1)
    # Common mistake: raw @ in password splits host incorrectly
    if ".amazonaws.com" in url and "@" in url.split("//", 1)[1].split(".amazonaws.com")[0]:
        tail = url.split("//", 1)[1]
        if tail.count("@") > 1:
            print(
                "DATABASE_URL looks malformed (password likely contains unencoded '@').\n"
                "Use: python scripts/migrate_to_rds.py --from-env --seed\n"
                "  with RDS_HOST, RDS_USER, RDS_PASSWORD, RDS_DB env vars.\n",
                file=sys.stderr,
            )
            sys.exit(1)


def _run(cmd: list[str], *, env: dict[str, str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=BACKEND_DIR, env=env, check=True)


def _build_rds_env(args: argparse.Namespace) -> dict[str, str]:
    """Return env vars for alembic/seed subprocesses."""
    if args.from_env or args.iam_auth or any([args.host, args.user, args.password is not None]):
        host = args.host or os.environ.get("RDS_HOST", "").strip()
        user = args.user or os.environ.get("RDS_USER", "").strip()
        dbname = args.dbname or os.environ.get("RDS_DB", "postgres").strip()
        port = args.port or int(os.environ.get("RDS_PORT", "5432"))
        region = args.region or os.environ.get("AWS_REGION", "ap-southeast-2").strip()

        if not host or not user:
            print(
                "Missing RDS connection details.\n"
                "Set RDS_HOST and RDS_USER (and RDS_DB=postgres if unsure).\n"
                "For IAM auth add --iam-auth (needs aws configure / env credentials).",
                file=sys.stderr,
            )
            sys.exit(1)

        if "localhost" in host or host.startswith("127."):
            print("RDS_HOST looks local — did you mean to point at RDS?", file=sys.stderr)
            sys.exit(1)

        if args.iam_auth:
            print(f"Generating IAM auth token for {user} @ {host} ({region})...")
            print(
                "Note: token hostname must match connection hostname exactly "
                "(use the instance endpoint from RDS Connect if unsure)."
            )
            try:
                token = generate_iam_auth_token(
                    host=host, user=user, port=port, region=region
                )
            except Exception as exc:
                print(
                    f"Failed to generate IAM token: {exc}\n"
                    "Run `aws configure` or set AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY.\n"
                    "Your IAM user needs rds-db:connect on this database user.",
                    file=sys.stderr,
                )
                sys.exit(1)
            print("IAM token generated (valid ~15 minutes)")
            print(f"Connecting to {host}, database {dbname} (token passed directly, not via URL)")
            return {
                "RDS_IAM_TOKEN": token,
                "RDS_HOST": host,
                "RDS_USER": user,
                "RDS_DB": dbname,
                "RDS_PORT": str(port),
            }

        password = (
            args.password
            if args.password is not None
            else os.environ.get("RDS_PASSWORD", "")
        )
        if not password:
            print(
                "Missing RDS_PASSWORD, or use --iam-auth if this user is IAM-only.",
                file=sys.stderr,
            )
            sys.exit(1)

        url = build_database_url(
            user=user,
            password=password,
            host=host,
            dbname=dbname,
            port=port,
        )
        print(f"Built DATABASE_URL for host {host}, database {dbname}")
        return {"DATABASE_URL": url}

    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url:
        print(
            "Set DATABASE_URL or use --from-env with RDS_* variables.\n\n"
            "Example:\n"
            "  $env:RDS_HOST='your-cluster.region.rds.amazonaws.com'\n"
            "  $env:RDS_USER='fieldintel'\n"
            "  $env:RDS_PASSWORD=$yourPasswordVariable\n"
            "  python scripts/migrate_to_rds.py --from-env --seed",
            file=sys.stderr,
        )
        sys.exit(1)
    return {"DATABASE_URL": database_url}


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate and optionally seed RDS")
    parser.add_argument("--seed", action="store_true")
    parser.add_argument(
        "--from-env",
        action="store_true",
        help="Build DATABASE_URL from RDS_HOST, RDS_USER, RDS_PASSWORD, RDS_DB",
    )
    parser.add_argument(
        "--iam-auth",
        action="store_true",
        help="Use IAM DB auth token instead of RDS_PASSWORD (fixes PAM authentication failed)",
    )
    parser.add_argument("--region", default=None, help="AWS region (default: ap-southeast-2)")
    parser.add_argument("--host", help="RDS endpoint hostname")
    parser.add_argument("--user", help="Database username")
    parser.add_argument("--password", help="Database password (URL-encoded automatically)")
    parser.add_argument("--dbname", default=None, help="Database name (default: postgres)")
    parser.add_argument("--port", type=int, default=None, help="Port (default: 5432)")
    args = parser.parse_args()

    if args.password is None and args.from_env and not args.iam_auth and not os.environ.get("RDS_PASSWORD"):
        args.password = getpass.getpass("RDS password: ")

    rds_env = _build_rds_env(args)
    built_from_parts = bool(
        args.from_env
        or args.iam_auth
        or any([args.host, args.user, args.password is not None])
    )
    if "DATABASE_URL" in rds_env:
        _validate_database_url(rds_env["DATABASE_URL"], built_from_parts=built_from_parts)
        if "localhost" in rds_env["DATABASE_URL"] or "127.0.0.1" in rds_env["DATABASE_URL"]:
            print("DATABASE_URL looks local — did you mean to point at RDS?", file=sys.stderr)
            sys.exit(1)

    env = os.environ.copy()
    if "RDS_IAM_TOKEN" in rds_env:
        env.pop("DATABASE_URL", None)
    env.update(rds_env)

    python = _backend_python()
    _run([*_alembic_cmd(python), "upgrade", "head"], env=env)

    if args.seed:
        _run([str(python), str(ROOT / "scripts" / "seed_users.py"), "--force"], env=env)
        _run([str(python), str(ROOT / "scripts" / "seed_data.py"), "--force"], env=env)

    print("\nRDS migration complete.")
    if not args.seed:
        print("Run with --seed to load demo users and visits.")


if __name__ == "__main__":
    main()
