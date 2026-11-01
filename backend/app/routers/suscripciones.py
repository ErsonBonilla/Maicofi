from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.limitador_tasa import dependencia_limite_escritura
from app.core.seguridad import obtener_usuario_actual
from app.db.conexion import obtener_bd
from app.models.entidades import (
    FrecuenciaSuscripcion,
    LoteCafe,
    PlanSuscripcion,
    SuscripcionUsuario,
    UnidadVenta,
    Usuario,
)
from app.schemas.dominio import (
    CrearSuscripcionUsuarioEsquema,
    LeerPlanSuscripcionEsquema,
    LeerSuscripcionUsuarioEsquema,
)

enrutador_suscripciones = APIRouter(
    prefix="/subscriptions", tags=["Suscripciones Recurrentes (/subscriptions)"]
)

DIAS_POR_FRECUENCIA: Dict[FrecuenciaSuscripcion, int] = {
    FrecuenciaSuscripcion.SEMANAL: 7,
    FrecuenciaSuscripcion.QUINCENAL: 15,
    FrecuenciaSuscripcion.MENSUAL: 30,
}

FACTOR_PRECIO_PRESENTACION: Dict[UnidadVenta, Decimal] = {
    UnidadVenta.GRAMOS_250: Decimal("0.55"),
    UnidadVenta.LIBRA: Decimal("1.00"),
    UnidadVenta.GRAMOS_500: Decimal("1.00"),
    UnidadVenta.GRAMOS_1000: Decimal("1.90"),
    UnidadVenta.ARROBA: Decimal("23.00"),
    UnidadVenta.CARGA: Decimal("212.50"),
}


def asegurar_planes_por_defecto(sesion_bd: Session) -> List[PlanSuscripcion]:
    planes = list(
        sesion_bd.scalars(
            select(PlanSuscripcion).where(PlanSuscripcion.activo.is_(True))
        ).all()
    )
    if planes:
        return planes

    planes_semilla = [
        PlanSuscripcion(
            codigo="SUB-SEMANAL-10",
            nombre="Suscripción Semanal Frescura de Origen",
            descripcion="Recibe café recién tostado del Tolima cada semana con 10% de descuento.",
            frecuencia=FrecuenciaSuscripcion.SEMANAL,
            porcentaje_descuento=Decimal("10.00"),
        ),
        PlanSuscripcion(
            codigo="SUB-QUINCENAL-10",
            nombre="Suscripción Quincenal Casa Cafetera",
            descripcion="Entrega cada 15 días directo de la finca con 10% de descuento permanente.",
            frecuencia=FrecuenciaSuscripcion.QUINCENAL,
            porcentaje_descuento=Decimal("10.00"),
        ),
        PlanSuscripcion(
            codigo="SUB-MENSUAL-10",
            nombre="Suscripción Mensual Reserva Tolima",
            descripcion="Entrega mensual programada con selección de molienda y 10% de descuento.",
            frecuencia=FrecuenciaSuscripcion.MENSUAL,
            porcentaje_descuento=Decimal("10.00"),
        ),
    ]
    sesion_bd.add_all(planes_semilla)
    sesion_bd.commit()
    return planes_semilla


@enrutador_suscripciones.get(
    "/plans",
    response_model=List[LeerPlanSuscripcionEsquema],
    summary="Listar planes de suscripción periódica con 10% de descuento",
)
def listar_planes_suscripcion(
    sesion_bd: Session = Depends(obtener_bd),
) -> List[PlanSuscripcion]:
    return asegurar_planes_por_defecto(sesion_bd)


@enrutador_suscripciones.post(
    "",
    response_model=LeerSuscripcionUsuarioEsquema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(dependencia_limite_escritura)],
    summary="Crear suscripción recurrente de café especial con 10% de descuento automático",
)
def crear_suscripcion_recurrente(
    datos_suscripcion: CrearSuscripcionUsuarioEsquema,
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
    sesion_bd: Session = Depends(obtener_bd),
) -> SuscripcionUsuario:
    lote = sesion_bd.scalar(
        select(LoteCafe).where(
            LoteCafe.id == datos_suscripcion.lote_cafe_id,
            LoteCafe.activo.is_(True),
        )
    )
    if not lote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El lote de café seleccionado para suscripción no está disponible.",
        )

    planes = asegurar_planes_por_defecto(sesion_bd)
    plan_seleccionado = next(
        (p for p in planes if p.frecuencia == datos_suscripcion.frecuencia),
        planes[0],
    )

    factor_peso = FACTOR_PRECIO_PRESENTACION.get(
        datos_suscripcion.presentacion_peso, Decimal("1.00")
    )
    precio_base_unitario = (lote.precio_libra_cop * factor_peso).quantize(Decimal("1"))
    factor_descuento = (
        Decimal("100.00") - plan_seleccionado.porcentaje_descuento
    ) / Decimal("100.00")
    precio_periodo_con_descuento = (
        precio_base_unitario * Decimal(datos_suscripcion.cantidad) * factor_descuento
    ).quantize(Decimal("1"))

    dias_ciclo = DIAS_POR_FRECUENCIA[datos_suscripcion.frecuencia]
    proxima_fecha = date.today() + timedelta(days=dias_ciclo)

    nueva_suscripcion = SuscripcionUsuario(
        comprador_id=usuario_actual.id,
        lote_cafe_id=lote.id,
        plan_id=plan_seleccionado.id,
        frecuencia=datos_suscripcion.frecuencia,
        presentacion_peso=datos_suscripcion.presentacion_peso,
        tipo_molienda=datos_suscripcion.tipo_molienda,
        cantidad=datos_suscripcion.cantidad,
        precio_periodo_cop=precio_periodo_con_descuento,
        porcentaje_descuento_aplicado=plan_seleccionado.porcentaje_descuento,
        proxima_entrega=proxima_fecha,
        direccion_envio=datos_suscripcion.direccion_envio,
        ciudad_envio=datos_suscripcion.ciudad_envio,
    )
    sesion_bd.add(nueva_suscripcion)
    sesion_bd.commit()
    sesion_bd.refresh(nueva_suscripcion)
    return nueva_suscripcion


@enrutador_suscripciones.get(
    "",
    response_model=List[LeerSuscripcionUsuarioEsquema],
    summary="Listar suscripciones activas del comprador autenticado",
)
def listar_mis_suscripciones(
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
    sesion_bd: Session = Depends(obtener_bd),
) -> List[SuscripcionUsuario]:
    consulta = (
        select(SuscripcionUsuario)
        .where(SuscripcionUsuario.comprador_id == usuario_actual.id)
        .order_by(SuscripcionUsuario.creado_en.desc())
    )
    return list(sesion_bd.scalars(consulta).all())
