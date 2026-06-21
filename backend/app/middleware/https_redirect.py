from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.config import settings


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """Redirect HTTP to HTTPS in production (behind reverse proxy)."""

    async def dispatch(self, request: Request, call_next):
        if settings.is_production:
            forwarded_proto = request.headers.get("x-forwarded-proto", "")
            if forwarded_proto == "http":
                url = request.url.replace(scheme="https")
                return RedirectResponse(url, status_code=308)
        return await call_next(request)
