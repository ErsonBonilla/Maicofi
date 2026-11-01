from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.configuracion import configuracion
from app.core.middleware_seguridad import MiddlewareCabecerasSeguridad
from app.routers.autenticacion import enrutador_autenticacion
from app.routers.integraciones import enrutador_integraciones
from app.routers.pedidos import enrutador_pedidos
from app.routers.productores import enrutador_caficultores, enrutador_productores
from app.routers.productos import enrutador_productos
from app.routers.suscripciones import enrutador_suscripciones

app = FastAPI(
    title=configuracion.NOMBRE_PROYECTO,
    description=(
        "Plataforma de comercio electrónico directo para caficultores de café especial "
        "del departamento del Tolima (Planadas, Líbano, Santa Isabel, Anzoátegui, Herrera, Ibagué)."
    ),
    version=configuracion.VERSION,
    docs_url=None if configuracion.ES_PRODUCCION else "/docs",
    redoc_url=None if configuracion.ES_PRODUCCION else "/redoc",
    openapi_url=None if configuracion.ES_PRODUCCION else "/openapi.json",
)

app.add_middleware(MiddlewareCabecerasSeguridad)

app.add_middleware(
    CORSMiddleware,
    allow_origins=configuracion.ORIGENES_CORS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

app.include_router(enrutador_autenticacion, prefix=configuracion.PREFIJO_API)
app.include_router(enrutador_productores, prefix=configuracion.PREFIJO_API)
app.include_router(enrutador_caficultores, prefix=configuracion.PREFIJO_API)
app.include_router(enrutador_productos, prefix=configuracion.PREFIJO_API)
app.include_router(enrutador_suscripciones, prefix=configuracion.PREFIJO_API)
app.include_router(enrutador_pedidos, prefix=configuracion.PREFIJO_API)
app.include_router(enrutador_integraciones, prefix=configuracion.PREFIJO_API)


@app.get("/health", tags=["Estado del Servicio"])
def verificar_salud_servicio() -> dict:
    return {
        "status": "ok",
        "service": configuracion.NOMBRE_PROYECTO,
        "region": "Tolima, Colombia",
    }
