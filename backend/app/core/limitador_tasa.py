from collections import defaultdict, deque
from threading import Lock
import time
from typing import Deque, Dict

from fastapi import HTTPException, Request, status

from app.core.configuracion import configuracion


class LimitadorTasaPeticiones:
    """
    Limitador de tasa por ventana deslizante en memoria para mitigar ataques
    de fuerza bruta, enumeración de cuentas y abuso de endpoints de escritura.
    """

    def __init__(self, maximo_peticiones: int, ventana_segundos: int = 60) -> None:
        self.maximo_peticiones = maximo_peticiones
        self.ventana_segundos = ventana_segundos
        self._registro_ip: Dict[str, Deque[float]] = defaultdict(deque)
        self._candado = Lock()

    def _obtener_ip_cliente(self, peticion: Request) -> str:
        encabezado_reenvio = peticion.headers.get("x-forwarded-for")
        if encabezado_reenvio:
            return encabezado_reenvio.split(",")[0].strip()
        if peticion.client and peticion.client.host:
            return peticion.client.host
        return "ip_desconocida"

    def __call__(self, peticion: Request) -> None:
        ip_cliente = self._obtener_ip_cliente(peticion)
        ahora = time.monotonic()
        limite_inferior = ahora - self.ventana_segundos

        with self._candado:
            cola_tiempos = self._registro_ip[ip_cliente]
            while cola_tiempos and cola_tiempos[0] < limite_inferior:
                cola_tiempos.popleft()

            if len(cola_tiempos) >= self.maximo_peticiones:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=(
                        "Has superado el número máximo de intentos permitidos por minuto. "
                        "Por favor espera un momento antes de volver a intentarlo."
                    ),
                    headers={"Retry-After": str(self.ventana_segundos)},
                )

            cola_tiempos.append(ahora)


dependencia_limite_autenticacion = LimitadorTasaPeticiones(
    maximo_peticiones=configuracion.MAX_INTENTOS_AUTH_POR_MINUTO,
    ventana_segundos=60,
)

dependencia_limite_escritura = LimitadorTasaPeticiones(
    maximo_peticiones=configuracion.MAX_PETICIONES_ESCRITURA_POR_MINUTO,
    ventana_segundos=60,
)
