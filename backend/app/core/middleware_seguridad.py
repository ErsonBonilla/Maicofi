from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.configuracion import configuracion


class MiddlewareCabecerasSeguridad(BaseHTTPMiddleware):
    """
    Inyecta cabeceras HTTP de endurecimiento de seguridad en todas las respuestas
    de la API de Maicofi para mitigar XSS, Clickjacking, MIME-sniffing y filtrado de sesión.
    """

    async def dispatch(
        self, peticion: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        respuesta = await call_next(peticion)

        respuesta.headers["X-Content-Type-Options"] = "nosniff"
        respuesta.headers["X-Frame-Options"] = "DENY"
        respuesta.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        respuesta.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=()"
        )

        if configuracion.ES_PRODUCCION:
            respuesta.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        ruta = peticion.url.path
        if "/auth" in ruta or "/orders" in ruta:
            respuesta.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            respuesta.headers["Pragma"] = "no-cache"

        return respuesta
