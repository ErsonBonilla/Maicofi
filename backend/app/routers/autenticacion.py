from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.configuracion import configuracion
from app.core.limitador_tasa import dependencia_limite_autenticacion
from app.core.seguridad import (
    autenticar_credenciales_tiempo_constante,
    crear_token_acceso,
    eliminar_cookie_sesion,
    establecer_cookie_sesion,
    generar_hash_contrasena,
    obtener_usuario_actual,
)
from app.db.conexion import obtener_bd
from app.models.entidades import RolUsuario, Usuario
from app.schemas.dominio import (
    CredencialesAccesoEsquema,
    RegistroUsuarioEsquema,
    RespuestaTokenEsquema,
    SolicitudAccesoDemoEsquema,
)

enrutador_autenticacion = APIRouter(prefix="/auth", tags=["Autenticación (/auth)"])


@enrutador_autenticacion.post(
    "/register",
    response_model=RespuestaTokenEsquema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(dependencia_limite_autenticacion)],
    summary="Registro simplificado de caficultor o comprador por celular o correo",
)
def registrar_usuario(
    datos_entrada: RegistroUsuarioEsquema,
    respuesta: Response,
    sesion_bd: Session = Depends(obtener_bd),
) -> RespuestaTokenEsquema:
    telefono_existente = sesion_bd.scalar(
        select(Usuario).where(Usuario.telefono == datos_entrada.telefono)
    )
    if telefono_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este número de celular ya se encuentra registrado en Maicofi.",
        )

    if datos_entrada.correo:
        correo_existente = sesion_bd.scalar(
            select(Usuario).where(Usuario.correo == datos_entrada.correo)
        )
        if correo_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este correo electrónico ya se encuentra registrado.",
            )

    nuevo_usuario = Usuario(
        nombre_completo=datos_entrada.nombre_completo,
        telefono=datos_entrada.telefono,
        correo=datos_entrada.correo,
        contrasena_hash=generar_hash_contrasena(datos_entrada.contrasena),
        rol=datos_entrada.rol,
    )
    sesion_bd.add(nuevo_usuario)
    sesion_bd.commit()
    sesion_bd.refresh(nuevo_usuario)

    token_jwt = crear_token_acceso(id_usuario=nuevo_usuario.id, rol=nuevo_usuario.rol)
    establecer_cookie_sesion(respuesta, token_jwt)

    return RespuestaTokenEsquema(
        token_acceso=token_jwt,
        rol=nuevo_usuario.rol,
        usuario_id=nuevo_usuario.id,
        nombre_completo=nuevo_usuario.nombre_completo,
    )


@enrutador_autenticacion.post(
    "/login",
    response_model=RespuestaTokenEsquema,
    dependencies=[Depends(dependencia_limite_autenticacion)],
    summary="Inicio de sesión seguro con tiempo constante y cookie HttpOnly",
)
def iniciar_sesion(
    credenciales: CredencialesAccesoEsquema,
    respuesta: Response,
    sesion_bd: Session = Depends(obtener_bd),
) -> RespuestaTokenEsquema:
    identificador_limpio = credenciales.identificador.strip()
    usuario_encontrado = sesion_bd.scalar(
        select(Usuario).where(
            (Usuario.telefono == identificador_limpio)
            | (Usuario.correo == identificador_limpio)
        )
    )

    usuario_autenticado = autenticar_credenciales_tiempo_constante(
        usuario_encontrado, credenciales.contrasena
    )
    if not usuario_autenticado:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Número de celular, correo o contraseña incorrectos.",
        )

    token_jwt = crear_token_acceso(
        id_usuario=usuario_autenticado.id, rol=usuario_autenticado.rol
    )
    establecer_cookie_sesion(respuesta, token_jwt)

    return RespuestaTokenEsquema(
        token_acceso=token_jwt,
        rol=usuario_autenticado.rol,
        usuario_id=usuario_autenticado.id,
        nombre_completo=usuario_autenticado.nombre_completo,
    )


@enrutador_autenticacion.post(
    "/demo-access",
    response_model=RespuestaTokenEsquema,
    dependencies=[Depends(dependencia_limite_autenticacion)],
    summary="Acceso rápido demostrativo (habilitado exclusivamente en entorno development)",
)
def iniciar_sesion_demostrativa(
    solicitud: SolicitudAccesoDemoEsquema,
    respuesta: Response,
    sesion_bd: Session = Depends(obtener_bd),
) -> RespuestaTokenEsquema:
    if configuracion.ES_PRODUCCION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El acceso demostrativo está deshabilitado en producción.",
        )

    telefono_objetivo = (
        configuracion.TELEFONO_CAFICULTOR_DEMO
        if solicitud.rol == RolUsuario.CAFICULTOR
        else configuracion.TELEFONO_COMPRADOR_DEMO
    )
    usuario = sesion_bd.scalar(
        select(Usuario).where(Usuario.telefono == telefono_objetivo, Usuario.activo.is_(True))
    )
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario demostrativo no encontrado. Ejecuta primero la semilla de datos.",
        )

    token_jwt = crear_token_acceso(id_usuario=usuario.id, rol=usuario.rol)
    establecer_cookie_sesion(respuesta, token_jwt)

    return RespuestaTokenEsquema(
        token_acceso=token_jwt,
        rol=usuario.rol,
        usuario_id=usuario.id,
        nombre_completo=usuario.nombre_completo,
    )


@enrutador_autenticacion.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Cerrar sesión y eliminar la cookie HttpOnly",
)
def cerrar_sesion(respuesta: Response) -> dict:
    eliminar_cookie_sesion(respuesta)
    return {"detail": "Sesión cerrada correctamente."}


@enrutador_autenticacion.get(
    "/me",
    response_model=RespuestaTokenEsquema,
    summary="Verificar sesión activa mediante Cookie HttpOnly o Bearer Token",
)
def obtener_sesion_actual(
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
) -> RespuestaTokenEsquema:
    token_renovado = crear_token_acceso(
        id_usuario=usuario_actual.id, rol=usuario_actual.rol
    )
    return RespuestaTokenEsquema(
        token_acceso=token_renovado,
        rol=usuario_actual.rol,
        usuario_id=usuario_actual.id,
        nombre_completo=usuario_actual.nombre_completo,
    )
