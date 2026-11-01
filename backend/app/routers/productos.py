from datetime import date
from decimal import Decimal
import re
from typing import List, Optional
import unicodedata
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.limitador_tasa import dependencia_limite_escritura
from app.core.seguridad import requerir_roles
from app.db.conexion import obtener_bd
from app.models.entidades import (
    Finca,
    LoteCafe,
    MunicipioTolima,
    NivelTueste,
    PerfilSensorial,
    ProcesoBeneficio,
    RolUsuario,
    Usuario,
    VariedadCafe,
)
from app.schemas.dominio import CrearLoteCafeEsquema, LeerLoteCafeEsquema

enrutador_productos = APIRouter(prefix="/products", tags=["Catálogo y Lotes de Café (/products)"])


def generar_slug_unico(texto: str) -> str:
    normalizado = (
        unicodedata.normalize("NFKD", texto)
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )
    base = re.sub(r"[^a-z0-9]+", "-", normalizado).strip("-")
    sufijo = uuid.uuid4().hex[:6]
    return f"{base}-{sufijo}" if base else f"lote-tolima-{sufijo}"


@enrutador_productos.get(
    "",
    response_model=List[LeerLoteCafeEsquema],
    summary="Catálogo filtrable de lotes de café especial del Tolima",
)
def listar_lotes_cafe(
    municipio: Optional[MunicipioTolima] = Query(
        None, alias="municipality", description="Municipio productor del Tolima"
    ),
    variedad: Optional[VariedadCafe] = Query(
        None, alias="variety", description="Variedad arábica sembrada"
    ),
    proceso: Optional[ProcesoBeneficio] = Query(
        None, alias="process", description="Proceso de beneficio del café"
    ),
    puntaje_sca_minimo: Optional[Decimal] = Query(
        None, alias="min_sca", ge=Decimal("80.0"), le=Decimal("100.0")
    ),
    precio_maximo_libra: Optional[Decimal] = Query(
        None, alias="max_price_lb", gt=0
    ),
    finca_id: Optional[uuid.UUID] = Query(
        None, alias="farm_id", description="Filtrar lotes de una finca específica"
    ),
    busqueda: Optional[str] = Query(
        None, alias="search", description="Buscar por nombre de lote o finca"
    ),
    sesion_bd: Session = Depends(obtener_bd),
) -> List[LoteCafe]:
    consulta = (
        select(LoteCafe)
        .join(LoteCafe.finca)
        .options(
            joinedload(LoteCafe.finca).joinedload(Finca.propietario),
            joinedload(LoteCafe.perfil_sensorial),
        )
        .where(LoteCafe.activo.is_(True), LoteCafe.stock_disponible_kg > 0)
    )

    if municipio:
        consulta = consulta.where(Finca.municipio == municipio)
    if variedad:
        consulta = consulta.where(LoteCafe.variedad == variedad)
    if proceso:
        consulta = consulta.where(LoteCafe.proceso == proceso)
    if puntaje_sca_minimo is not None:
        consulta = consulta.where(LoteCafe.puntaje_sca >= puntaje_sca_minimo)
    if precio_maximo_libra is not None:
        consulta = consulta.where(LoteCafe.precio_libra_cop <= precio_maximo_libra)
    if finca_id is not None:
        consulta = consulta.where(LoteCafe.finca_id == finca_id)
    if busqueda:
        patron = f"%{busqueda.strip()}%"
        consulta = consulta.where(
            (LoteCafe.nombre.ilike(patron)) | (Finca.nombre_finca.ilike(patron))
        )

    consulta = consulta.order_by(LoteCafe.puntaje_sca.desc(), LoteCafe.creado_en.desc())
    return list(sesion_bd.scalars(consulta).all())


@enrutador_productos.get(
    "/{identificador}",
    response_model=LeerLoteCafeEsquema,
    summary="Obtener ficha técnica completa, perfil sensorial e historia del productor por UUID o Slug",
)
def obtener_detalle_lote(
    identificador: str,
    sesion_bd: Session = Depends(obtener_bd),
) -> LoteCafe:
    consulta_base = select(LoteCafe).options(
        joinedload(LoteCafe.finca).joinedload(Finca.propietario),
        joinedload(LoteCafe.perfil_sensorial),
    )

    try:
        lote_uuid = uuid.UUID(identificador)
        consulta = consulta_base.where(LoteCafe.id == lote_uuid)
    except ValueError:
        consulta = consulta_base.where(LoteCafe.slug == identificador)

    lote = sesion_bd.scalar(consulta)
    if not lote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El lote de café consultado no existe.",
        )
    return lote


@enrutador_productos.post(
    "",
    response_model=LeerLoteCafeEsquema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(dependencia_limite_escritura)],
    summary="Publicar un nuevo lote de cosecha con ficha técnica y perfil sensorial",
)
def publicar_lote_cafe(
    datos_lote: CrearLoteCafeEsquema,
    usuario_actual: Usuario = Depends(
        requerir_roles([RolUsuario.CAFICULTOR, RolUsuario.ADMINISTRADOR])
    ),
    sesion_bd: Session = Depends(obtener_bd),
) -> LoteCafe:
    finca = sesion_bd.scalar(select(Finca).where(Finca.usuario_id == usuario_actual.id))
    if not finca:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Primero debes registrar el perfil de tu finca cafetera antes de publicar un lote.",
        )

    atributos = datos_lote.model_dump(by_alias=False, exclude={"perfil_sensorial"})
    if not atributos.get("slug"):
        atributos["slug"] = generar_slug_unico(datos_lote.nombre)
    if not atributos.get("fecha_tueste"):
        atributos["fecha_tueste"] = date.today()

    if not atributos.get("precio_arroba_cop"):
        atributos["precio_arroba_cop"] = (
            datos_lote.precio_libra_cop * Decimal("25") * Decimal("0.92")
        ).quantize(Decimal("1"))
    if not atributos.get("precio_carga_cop"):
        atributos["precio_carga_cop"] = (
            datos_lote.precio_libra_cop * Decimal("250") * Decimal("0.85")
        ).quantize(Decimal("1"))

    nuevo_lote = LoteCafe(finca_id=finca.id, **atributos)
    sesion_bd.add(nuevo_lote)
    sesion_bd.flush()

    datos_sensoriales = datos_lote.perfil_sensorial
    nuevo_perfil = PerfilSensorial(
        lote_cafe_id=nuevo_lote.id,
        acidez=datos_sensoriales.acidez if datos_sensoriales else 4,
        cuerpo=datos_sensoriales.cuerpo if datos_sensoriales else 4,
        dulzura=datos_sensoriales.dulzura if datos_sensoriales else 5,
        nivel_tueste=(
            datos_sensoriales.nivel_tueste if datos_sensoriales else NivelTueste.MEDIO
        ),
        notas_principales=(
            datos_sensoriales.notas_principales
            if datos_sensoriales and datos_sensoriales.notas_principales
            else datos_lote.notas_cata
        ),
    )
    sesion_bd.add(nuevo_perfil)
    sesion_bd.commit()

    lote_recargado = sesion_bd.scalar(
        select(LoteCafe)
        .options(
            joinedload(LoteCafe.finca).joinedload(Finca.propietario),
            joinedload(LoteCafe.perfil_sensorial),
        )
        .where(LoteCafe.id == nuevo_lote.id)
    )
    return lote_recargado or nuevo_lote


@enrutador_productos.put(
    "/{lote_id}",
    response_model=LeerLoteCafeEsquema,
    dependencies=[Depends(dependencia_limite_escritura)],
    summary="Editar un lote de café existente del productor",
)
def actualizar_lote_cafe(
    lote_id: uuid.UUID,
    datos_lote: CrearLoteCafeEsquema,
    usuario_actual: Usuario = Depends(
        requerir_roles([RolUsuario.CAFICULTOR, RolUsuario.ADMINISTRADOR])
    ),
    sesion_bd: Session = Depends(obtener_bd),
) -> LoteCafe:
    lote = sesion_bd.scalar(
        select(LoteCafe)
        .options(
            joinedload(LoteCafe.finca).joinedload(Finca.propietario),
            joinedload(LoteCafe.perfil_sensorial),
        )
        .where(LoteCafe.id == lote_id)
    )
    if not lote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lote de café no encontrado.",
        )
    if (
        usuario_actual.rol != RolUsuario.ADMINISTRADOR
        and lote.finca.usuario_id != usuario_actual.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo puedes editar los lotes pertenecientes a tu finca.",
        )

    for campo, valor in datos_lote.model_dump(
        by_alias=False, exclude={"perfil_sensorial", "slug"}
    ).items():
        setattr(lote, campo, valor)

    if datos_lote.perfil_sensorial:
        if lote.perfil_sensorial:
            lote.perfil_sensorial.acidez = datos_lote.perfil_sensorial.acidez
            lote.perfil_sensorial.cuerpo = datos_lote.perfil_sensorial.cuerpo
            lote.perfil_sensorial.dulzura = datos_lote.perfil_sensorial.dulzura
            lote.perfil_sensorial.nivel_tueste = datos_lote.perfil_sensorial.nivel_tueste
            lote.perfil_sensorial.notas_principales = (
                datos_lote.perfil_sensorial.notas_principales or datos_lote.notas_cata
            )
        else:
            sesion_bd.add(
                PerfilSensorial(
                    lote_cafe_id=lote.id,
                    **datos_lote.perfil_sensorial.model_dump(by_alias=False),
                )
            )

    sesion_bd.commit()
    sesion_bd.refresh(lote)
    return lote
