from datetime import datetime, timedelta, timezone
from typing import Callable, List, Optional
import uuid

import bcrypt
from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.configuracion import configuracion
from app.db.conexion import obtener_bd
from app.models.entidades import RolUsuario, Usuario

esquema_portador_http = HTTPBearer(auto_error=False)


def generar_hash_contrasena(contrasena_plana: str) -> str:
    """
    Genera un hash seguro con bcrypt nativo (compatible con Python 3.12+)
    para almacenar en PostgreSQL 18.
    """
    bytes_contrasena = contrasena_plana.encode("utf-8")[:72]
    sal = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(bytes_contrasena, sal).decode("utf-8")


def verificar_contrasena(contrasena_plana: str, contrasena_hash: str) -> bool:
    """Compara una contraseña en texto plano con su hash bcrypt almacenado."""
    try:
        bytes_contrasena = contrasena_plana.encode("utf-8")[:72]
        bytes_hash = contrasena_hash.encode("utf-8")
        return bcrypt.checkpw(bytes_contrasena, bytes_hash)
    except ValueError:
        return False


# Hash bcrypt precalculado al inicio para igualar tiempos de respuesta (Anti-Timing Attack)
HASH_SENUELO_TIEMPO_CONSTANTE: str = generar_hash_contrasena(
    "contrasena_senuelo_tiempo_constante_maicofi_2026"
)


def autenticar_credenciales_tiempo_constante(
    usuario: Optional[Usuario], contrasena_plana: str
) -> Optional[Usuario]:
    """
    Ejecuta siempre la verificación bcrypt incluso si el usuario no existe en la base de datos,
    impidiendo la enumeración de teléfonos o correos mediante ataques de tiempo (Timing Attacks).
    """
    if usuario is None:
        verificar_contrasena(contrasena_plana, HASH_SENUELO_TIEMPO_CONSTANTE)
        return None

    if not verificar_contrasena(contrasena_plana, usuario.contrasena_hash):
        return None

    if not usuario.activo:
        return None

    return usuario


def crear_token_acceso(
    id_usuario: uuid.UUID,
    rol: RolUsuario,
    minutos_expiracion: Optional[int] = None,
) -> str:
    """
    Crea un token JWT endurecido con claims estándar RFC 7519 ('sub', 'role', 'iat', 'exp', 'iss', 'jti').
    """
    ahora = datetime.now(timezone.utc)
    tiempo_expiracion = ahora + timedelta(
        minutes=minutos_expiracion or configuracion.MINUTOS_EXPIRACION_TOKEN
    )
    carga_util_jwt = {
        "sub": str(id_usuario),
        "role": rol.value,
        "iat": int(ahora.timestamp()),
        "exp": tiempo_expiracion,
        "iss": configuracion.EMISOR_JWT,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(
        carga_util_jwt,
        configuracion.CLAVE_SECRETA_JWT,
        algorithm=configuracion.ALGORITMO_JWT,
    )


def establecer_cookie_sesion(respuesta: Response, token_jwt: str) -> None:
    """Configura la cookie HttpOnly protegida contra lectura por scripts XSS."""
    max_age_segundos = configuracion.MINUTOS_EXPIRACION_TOKEN * 60
    respuesta.set_cookie(
        key=configuracion.NOMBRE_COOKIE_SESION,
        value=token_jwt,
        httponly=True,
        secure=configuracion.ES_PRODUCCION,
        samesite="lax",
        max_age=max_age_segundos,
        path="/",
    )


def eliminar_cookie_sesion(respuesta: Response) -> None:
    """Elimina la cookie HttpOnly al cerrar sesión."""
    respuesta.delete_cookie(
        key=configuracion.NOMBRE_COOKIE_SESION,
        httponly=True,
        secure=configuracion.ES_PRODUCCION,
        samesite="lax",
        path="/",
    )


def obtener_usuario_actual(
    peticion: Request,
    credenciales: Optional[HTTPAuthorizationCredentials] = Depends(esquema_portador_http),
    sesion_bd: Session = Depends(obtener_bd),
) -> Usuario:
    """
    Extrae y valida el token JWT desde el encabezado Authorization Bearer
    o desde la cookie HttpOnly 'maicofi_access_token'.
    """
    token_crudo: Optional[str] = None
    if credenciales and credenciales.credentials:
        token_crudo = credenciales.credentials
    else:
        token_crudo = peticion.cookies.get(configuracion.NOMBRE_COOKIE_SESION)

    if not token_crudo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se proporcionó sesión activa ni token de autenticación.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        carga_util = jwt.decode(
            token_crudo,
            configuracion.CLAVE_SECRETA_JWT,
            algorithms=[configuracion.ALGORITMO_JWT],
            issuer=configuracion.EMISOR_JWT,
        )
        identificador_sub: Optional[str] = carga_util.get("sub")
        if not identificador_sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: identificador de usuario ausente.",
            )
        id_usuario = uuid.UUID(identificador_sub)
    except (JWTError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de sesión inválido o expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    usuario = sesion_bd.scalar(
        select(Usuario).where(Usuario.id == id_usuario, Usuario.activo.is_(True))
    )
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El usuario asociado al token no existe o está inactivo.",
        )
    return usuario


def requerir_roles(roles_permitidos: List[RolUsuario]) -> Callable[[Usuario], Usuario]:
    """Genera una dependencia de FastAPI para validar el rol del usuario autenticado."""

    def validador_rol(usuario_actual: Usuario = Depends(obtener_usuario_actual)) -> Usuario:
        if usuario_actual.rol not in roles_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos suficientes para realizar esta operación.",
            )
        return usuario_actual

    return validador_rol
