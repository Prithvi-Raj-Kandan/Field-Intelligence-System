const API_BASE = import.meta.env.VITE_API_URL ?? "";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export function mediaUrl(path: string): string {
  if (path.startsWith("http")) {
    try {
      const url = new URL(path);
      return url.pathname;
    } catch {
      return path;
    }
  }
  return `/media/${path.replace(/^\//, "")}`;
}

async function parseError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail)) {
      return data.detail.map((d: { msg?: string }) => d.msg ?? "Error").join(", ");
    }
  } catch {
    /* ignore */
  }
  return res.statusText || "Request failed";
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    credentials: "include",
  });
  if (!res.ok) {
    throw new ApiError(await parseError(res), res.status);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export async function fetchMediaBlob(path: string): Promise<Blob> {
  const url = mediaUrl(path);
  const res = await fetch(`${API_BASE}${url}`, { credentials: "include" });
  if (!res.ok) {
    throw new ApiError("Failed to load media", res.status);
  }
  return res.blob();
}

export async function downloadCsv(path: string, filename: string): Promise<void> {
  const res = await fetch(`${API_BASE}${path}`, { credentials: "include" });
  if (!res.ok) {
    throw new ApiError(await parseError(res), res.status);
  }
  const blob = await res.blob();
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(objectUrl);
}

/** @deprecated Token is stored in httpOnly cookie — kept for API test scripts only. */
export function setToken(_token: string) {
  /* no-op: auth cookie set by server */
}

export function clearToken() {
  /* no-op: use logout endpoint */
}

export function saveUser(_user: object) {
  /* no-op: user profile loaded from /auth/me */
}

export function loadUser<T>(): T | null {
  return null;
}
