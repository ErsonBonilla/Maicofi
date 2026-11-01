from decimal import Decimal
from typing import Dict, List, Tuple
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.limitador_tasa import dependencia_limite_escritura
from app.core.seguridad import obtener_usuario_actual
from app.db.conexion import obtener_bd
from app.models.entidades import (
    DatosFiscalesCliente,
    DetallePedido,
    LoteCafe,
    Pedido,
    RolUsuario,
    TipoMolienda,
    UnidadVenta,
    Usuario,
)
from app.schemas.dominio import CrearPedidoEsquema, LeerPedidoEsquema

enrutador_pedidos = APIRouter(prefix="/orders", tags=["Pedidos y Checkout (/orders)"])

EQUIVALENCIA_UNIDAD_A_KG: Dict[UnidadVenta, Decimal] = {
    UnidadVenta.GRAMOS_250: Decimal("0.25"),
    UnidadVenta.LIBRA: Decimal("0.50"),
    UnidadVenta.GRAMOS_500: Decimal("0.50"),
    UnidadVenta.GRAMOS_1000: Decimal("1.00"),
    UnidadVenta.ARROBA: Decimal("12.50"),
    UnidadVenta.CARGA: Decimal("125.00"),
}


def calcular_precio_unitario_cop(lote: LoteCafe, unidad: UnidadVenta) -> Decimal:
    """Obtiene el precio en COP según la presentación seleccionada (250g, 500g/libra, 1000g, arroba o carga)."""
    if unidad == UnidadVenta.GRAMOS_250:
        return (lote.precio_libra_cop * Decimal("0.55")).quantize(Decimal("1"))
    if unidad in (UnidadVenta.LIBRA, UnidadVenta.GRAMOS_500):
        return lote.precio_libra_cop
    if unidad == UnidadVenta.GRAMOS_1000:
        return (lote.precio_libra_cop * Decimal("1.90")).quantize(Decimal("1"))
    if unidad == UnidadVenta.ARROBA:
        return lote.precio_arroba_cop or (lote.precio_libra_cop * Decimal("25"))
    return lote.precio_carga_cop or (lote.precio_libra_cop * Decimal("250"))


@enrutador_pedidos.post(
    "",
    response_model=LeerPedidoEsquema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(dependencia_limite_escritura)],
    summary="Crear pedido de compra directa con datos fiscales DIAN y bloqueo determinista",
)
def crear_pedido(
    datos_pedido: CrearPedidoEsquema,
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
    sesion_bd: Session = Depends(obtener_bd),
) -> Pedido:
    cantidades_consolidadas: Dict[Tuple[uuid.UUID, UnidadVenta, TipoMolienda], int] = {}
    for item_entrada in datos_pedido.detalles:
        clave = (
            item_entrada.lote_cafe_id,
            item_entrada.unidad_venta,
            item_entrada.tipo_molienda,
        )
        cantidades_consolidadas[clave] = (
            cantidades_consolidadas.get(clave, 0) + item_entrada.cantidad
        )

    ids_lotes_ordenados = sorted(
        {lote_id for (lote_id, _, _) in cantidades_consolidadas.keys()}
    )
    lotes_bloqueados: Dict[uuid.UUID, LoteCafe] = {}
    for lote_id in ids_lotes_ordenados:
        lote = sesion_bd.scalar(
            select(LoteCafe)
            .where(LoteCafe.id == lote_id)
            .with_for_update()
        )
        if not lote or not lote.activo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"El lote con ID {lote_id} no está disponible.",
            )
        lotes_bloqueados[lote_id] = lote

    monto_total_cop = Decimal("0")
    lista_detalles: List[DetallePedido] = []

    for (
        lote_id,
        unidad_venta,
        tipo_molienda,
    ), cantidad_total in cantidades_consolidadas.items():
        lote = lotes_bloqueados[lote_id]
        kilos_requeridos = (
            EQUIVALENCIA_UNIDAD_A_KG[unidad_venta] * Decimal(cantidad_total)
        )
        if lote.stock_disponible_kg < kilos_requeridos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Inventario insuficiente para '{lote.nombre}'. "
                    f"Disponible: {lote.stock_disponible_kg} kg; solicitado: {kilos_requeridos} kg."
                ),
            )

        precio_unitario = calcular_precio_unitario_cop(lote, unidad_venta)
        subtotal = precio_unitario * Decimal(cantidad_total)
        monto_total_cop += subtotal

        lote.stock_disponible_kg -= kilos_requeridos

        lista_detalles.append(
            DetallePedido(
                lote_cafe_id=lote.id,
                unidad_venta=unidad_venta,
                tipo_molienda=tipo_molienda,
                cantidad=cantidad_total,
                equivalente_kg=kilos_requeridos,
                precio_unitario_cop=precio_unitario,
                subtotal_cop=subtotal,
            )
        )

    nuevo_pedido = Pedido(
        comprador_id=usuario_actual.id,
        monto_total_cop=monto_total_cop,
        direccion_envio=datos_pedido.direccion_envio,
        ciudad_envio=datos_pedido.ciudad_envio,
        departamento_envio=datos_pedido.departamento_envio,
        telefono_contacto=datos_pedido.telefono_contacto,
        notas=datos_pedido.notas,
        detalles=lista_detalles,
    )
    sesion_bd.add(nuevo_pedido)
    sesion_bd.flush()

    if datos_pedido.datos_fiscales:
        atributos_fiscales = datos_pedido.datos_fiscales.model_dump(by_alias=False)
        registro_fiscal = DatosFiscalesCliente(
            pedido_id=nuevo_pedido.id,
            usuario_id=usuario_actual.id,
            **atributos_fiscales,
        )
        sesion_bd.add(registro_fiscal)

    sesion_bd.commit()

    pedido_recargado = sesion_bd.scalar(
        select(Pedido)
        .options(
            joinedload(Pedido.detalles),
            joinedload(Pedido.datos_fiscales),
            joinedload(Pedido.factura_electronica),
        )
        .where(Pedido.id == nuevo_pedido.id)
    )
    return pedido_recargado or nuevo_pedido


@enrutador_pedidos.get(
    "",
    response_model=List[LeerPedidoEsquema],
    summary="Listar los pedidos realizados por el usuario autenticado",
)
def listar_mis_pedidos(
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
    sesion_bd: Session = Depends(obtener_bd),
) -> List[Pedido]:
    consulta = (
        select(Pedido)
        .options(
            joinedload(Pedido.detalles),
            joinedload(Pedido.datos_fiscales),
            joinedload(Pedido.factura_electronica),
        )
        .where(Pedido.comprador_id == usuario_actual.id)
        .order_by(Pedido.creado_en.desc())
    )
    return list(sesion_bd.scalars(consulta).unique().all())


@enrutador_pedidos.get(
    "/{pedido_id}",
    response_model=LeerPedidoEsquema,
    summary="Obtener detalle de un pedido incluyendo datos fiscales y factura electrónica DIAN",
)
def obtener_detalle_pedido(
    pedido_id: uuid.UUID,
    sesion_bd: Session = Depends(obtener_bd),
) -> Pedido:
    pedido = sesion_bd.scalar(
        select(Pedido)
        .options(
            joinedload(Pedido.detalles),
            joinedload(Pedido.datos_fiscales),
            joinedload(Pedido.factura_electronica),
        )
        .where(Pedido.id == pedido_id)
    )
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El pedido solicitado no fue encontrado.",
        )
    return pedido
