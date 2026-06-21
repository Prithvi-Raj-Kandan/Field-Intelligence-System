from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.config import settings
from app.middleware.auth import get_current_user
from app.middleware.https_redirect import HTTPSRedirectMiddleware
from app.models.user import User
from app.routers import auth, insights, media, visits, workers
from app.schemas.auth import UserResponse

app = FastAPI(
    title="Field Intelligence System",
    description="NGO field visit debrief API",
    version="0.1.0",
    # Avoid 307 redirects on /workers vs /workers/ when proxied through Vercel.
    redirect_slashes=False,
)

# Trust X-Forwarded-* from App Platform / load balancers so redirects use HTTPS.
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

if settings.is_production:
    app.add_middleware(HTTPSRedirectMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(media.router)
app.include_router(visits.router)
app.include_router(insights.router)
app.include_router(workers.router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/auth/me", tags=["auth"], response_model=UserResponse, deprecated=True)
def read_current_user_legacy(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Legacy route — prefer GET /auth/me on auth router."""
    return UserResponse.model_validate(current_user)
