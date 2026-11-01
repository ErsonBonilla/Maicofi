from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.limitador_tasa import dependencia_limite_escritura
from app.core.seguridad import requerir_roles
from app.db.conexion import obtener_bd
from app.models.entidades import Finca, LoteCafe, MunicipioTolima, RolUsuario, Usuario
from app.schemas.dominio import (
    CrearFincaEsquema,
    HistoriaCaficultorEsquema,
    LeerFincaEsquema,
    ResumenLoteProductorEsquema,
)

enrutador_productores = APIRouter(prefix="/producers", tags=["Productores y Fincas (/producers)"])
enrutador_caficultores = APIRouter(prefix="/farmers", tags=["Storytelling y Trazabilidad (/farmers)"])


@enrutador_productores.get(
    "",
    response_model=List[LeerFincaEsquema],
    summary="Listar fincas cafeteras del Tolima",
)
def listar_fincas_productoras(
    municipio: Optional[MunicipioTolima] = Query(
        None, alias="municipality", description="Filtrar por municipio del Tolima"
    ),
    sesion_bd: Session = Depends(obtener_bd),
) -> List[Finca]:
    consulta = select(Finca).options(joinedload(Finca.propietario))
    if municipio:
        consulta = consulta.where(Finca.municipio == municipio)
    consulta = consulta.order_by(Finca.nombre_finca.asc())
    return list(sesion_bd.scalars(consulta).all())


@enrutador_productores.get(
    "/{finca_id}",
    response_model=LeerFincaEsquema,
    summary="Obtener detalle de una finca cafetera",
)
def obtener_finca_por_id(
    finca_id: uuid.UUID,
    sesion_bd: Session = Depends(obtener_bd),
) -> Finca:
    consulta = (
        select(Finca)
        .options(joinedload(Finca.propietario))
        .where(Finca.id == finca_id)
    )
    finca = sesion_bd.scalar(consulta)
    if not finca:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró la finca solicitada.",
        )
    return finca


@enrutador_caficultores.get(
    "/{finca_id}/story",
    response_model=HistoriaCaficultorEsquema,
    summary="Obtener historia familiar, geolocalización y otros lotes del productor",
)
@enrutador_productores.get(
    "/{finca_id}/story",
    response_model=HistoriaCaficultorEsquema,
    summary="Obtener historia familiar, geolocalización y otros lotes del productor",
)
def obtener_historia_trazabilidad_productor(
    finca_id: uuid.UUID,
    sesion_bd: Session = Depends(obtener_bd),
) -> HistoriaCaficultorEsquema:
    finca = sesion_bd.scalar(
        select(Finca)
        .options(
            joinedload(Finca.propietario),
            joinedload(Finca.lotes_cafe),
        )
        .where(Finca.id == finca_id)
    )
    if not finca:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró el perfil del caficultor solicitado.",
        )

    lotes_activos: List[LoteCafe] = [
        lote for lote in finca.lotes_cafe if lote.activo and lote.stock_disponible_kg > 0
    ]

    return HistoriaCaficultorEsquema(
        finca_id=finca.id,
        nombre_finca=finca.nombre_finca,
        nombre_productor=finca.nombre_propietario,
        foto_productor_url=finca.foto_productor_url,
        municipio=finca.municipio,
        vereda=finca.vereda,
        altura_msnm=finca.altura_msnm,
        latitud=finca.latitud,
        longitud=finca.longitud,
        historia_productor=finca.historia_productor,
        urls_fotos_finca=finca.urls_fotos or [],
        otros_lotes=[
            ResumenLoteProductorEsquema.model_validate(lote) for lote in lotes_activos
        ],
    )


@enrutador_productores.post(
    "/farm",
    response_model=LeerFincaEsquema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(dependencia_limite_escritura)],
    summary="Crear o actualizar el perfil de la finca del caficultor autenticado",
)
def guardar_perfil_finca(
    datos_finca: CrearFincaEsquema,
    usuario_actual: Usuario = Depends(
        requerir_roles([RolUsuario.CAFICULTOR, RolUsuario.ADMINISTRADOR])
    ),
    sesion_bd: Session = Depends(obtener_bd),
) -> Finca:
    finca_existente = sesion_bd.scalar(
        select(Finca)
        .options(joinedload(Finca.propietario))
        .where(Finca.usuario_id == usuario_actual.id)
    )

    valores_finca = datos_finca.model_dump(by_alias=False)
    if finca_existente:
        for campo, valor in valores_finca.items():
            setattr(finca_existente, campo, valor)
        finca_objetivo = finca_existente
    else:
        finca_objetivo = Finca(usuario_id=usuario_actual.id, **valores_finca)
        sesion_bd.add(finca_objetivo)

    sesion_bd.commit()
    sesion_bd.refresh(finca_objetivo)
    return finca_objetivo
