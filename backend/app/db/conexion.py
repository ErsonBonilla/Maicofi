from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.configuracion import configuracion

motor_bd = create_engine(
    configuracion.URL_BASE_DATOS,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SesionLocal = sessionmaker(autocommit=False, autoflush=False, bind=motor_bd)


def obtener_bd() -> Generator[Session, None, None]:
    """Generador de sesión de base de datos por petición HTTP."""
    sesion = SesionLocal()
    try:
        yield sesion
    finally:
        sesion.close()
