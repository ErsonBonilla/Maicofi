from decimal import Decimal
from typing import Any, Dict, List, Optional
import uuid

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Header,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.limitador_tasa import dependencia_limite_escritura
from app.core.seguridad import obtener_usuario_actual, requerir_roles
from app.db.conexion import obtener_bd
from app.models.entidades import (
    DetallePedido,
    EstadoPedido,
    FacturaElectronica,
    Finca,
    LoteCafe,
    MunicipioTolima,
    Pedido,
    RolUsuario,
    Usuario,
)
from app.schemas.dominio import (
    LeerFacturaElectronicaEsquema,
    RespuestaCotizacionEnvioEsquema,
    RespuestaSesionPagoWompiEsquema,
    RespuestaSubidaImagenEsquema,
    SolicitudCotizacionEnvioEsquema,
    SolicitudSesionPagoWompiEsquema,
)
from app.services.cloudinary import subir_y_optimizar_imagen_cloudinary
from app.services.envios import cotizar_envio_nacional
from app.services.facturacion import emitir_factura_electronica_dian
from app.services.notificaciones import (
    construir_factura_html_maicofi,
    enviar_alerta_whatsapp,
    enviar_correo_pedido,
)
from app.services.wompi import (
    construir_sesion_checkout_wompi,
    generar_referencia_pago_unica,
    mapear_estado_wompi_a_pedido,
    verificar_firma_webhook_wompi,
)

enrutador_integraciones = APIRouter(tags=["Microservicios e Integraciones Externas"])


async def procesar_facturacion_y_notificaciones_post_pago(
    pedido_id: uuid.UUID,
    alertas_caficultores: List[Dict[str, str]],
    datos_correo_comprador: Dict[str, Any],
) -> None:
    """
    Tarea asíncrona en segundo plano disparada tras un pago aprobado en Wompi:
    1. Emite la Factura Electrónica ante la DIAN (Dataico / Alegra API).
    2. Envía las alertas de WhatsApp a cada caficultor del Tolima.
    3. Envía el correo de confirmación al comprador adjuntando el PDF y el CUFE de la DIAN.
    """
    resultado_factura = await emitir_factura_electronica_dian(pedido_id=pedido_id)

    for alerta in alertas_caficultores:
        await enviar_alerta_whatsapp(
            telefono_caficultor=alerta["telefono"],
            nombre_caficultor=alerta["nombre"],
            resumen_lote=alerta["lote"],
            cantidad_texto=alerta["cantidad_texto"],
            ciudad_destino=alerta["ciudad_destino"],
            referencia_pedido=alerta["referencia"],
        )

    if datos_correo_comprador.get("correo"):
        await enviar_correo_pedido(
            correo_comprador=datos_correo_comprador["correo"],
            nombre_comprador=datos_correo_comprador["nombre"],
            referencia_pedido=datos_correo_comprador["referencia"],
            monto_total_cop=datos_correo_comprador["monto_subtotal_cop"],
            costo_envio_cop=datos_correo_comprador["costo_envio_cop"],
            lineas_detalle=datos_correo_comprador["lineas"],
            cufe_dian=resultado_factura.get("cufe") if resultado_factura else None,
            url_pdf_dian=resultado_factura.get("url_pdf") if resultado_factura else None,
        )


@enrutador_integraciones.post(
    "/payments/checkout-session",
    response_model=RespuestaSesionPagoWompiEsquema,
    dependencies=[Depends(dependencia_limite_escritura)],
    summary="Generar sesión de pago y firma criptográfica SHA-256 para Wompi Colombia",
)
async def crear_sesion_checkout_wompi(
    solicitud: SolicitudSesionPagoWompiEsquema,
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
    sesion_bd: Session = Depends(obtener_bd),
) -> RespuestaSesionPagoWompiEsquema:
    pedido = sesion_bd.scalar(
        select(Pedido)
        .options(
            joinedload(Pedido.detalles)
            .joinedload(DetallePedido.lote_cafe)
            .joinedload(LoteCafe.finca)
        )
        .where(Pedido.id == solicitud.pedido_id)
    )
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El pedido indicado no existe.",
        )

    if (
        usuario_actual.rol != RolUsuario.ADMINISTRADOR
        and pedido.comprador_id != usuario_actual.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para generar el pago de este pedido.",
        )

    peso_total_kg = sum(
        (d.equivalente_kg for d in pedido.detalles), start=Decimal("0.50")
    )
    municipio_origen = MunicipioTolima.PLANADAS
    if pedido.detalles and pedido.detalles[0].lote_cafe and pedido.detalles[0].lote_cafe.finca:
        municipio_origen = pedido.detalles[0].lote_cafe.finca.municipio

    cotizacion = await cotizar_envio_nacional(
        municipio_origen=municipio_origen,
        ciudad_destino=pedido.ciudad_envio,
        departamento_destino=pedido.departamento_envio,
        peso_total_kg=peso_total_kg,
    )
    costo_envio = cotizacion["costo_flete_cop"]

    if not pedido.referencia_pago:
        pedido.referencia_pago = generar_referencia_pago_unica(pedido.id)
    pedido.costo_envio_cop = costo_envio
    sesion_bd.commit()
    sesion_bd.refresh(pedido)

    monto_final_con_envio = pedido.monto_total_cop + pedido.costo_envio_cop
    datos_wompi = construir_sesion_checkout_wompi(
        pedido_id=pedido.id,
        referencia=pedido.referencia_pago,
        monto_total_cop=monto_final_con_envio,
        url_redireccion=solicitud.url_redireccion
        or f"http://localhost:8000/orders/{pedido.id}",
    )

    return RespuestaSesionPagoWompiEsquema(
        **datos_wompi,
        costo_envio_cop=pedido.costo_envio_cop,
        monto_total_con_envio_cop=monto_final_con_envio,
    )


@enrutador_integraciones.post(
    "/payments/webhook",
    status_code=status.HTTP_200_OK,
    summary="Webhook seguro e idempotente de Wompi que dispara facturación electrónica DIAN",
)
async def procesar_webhook_wompi(
    peticion: Request,
    tareas_fondo: BackgroundTasks,
    x_event_checksum: Optional[str] = Header(default=None),
    sesion_bd: Session = Depends(obtener_bd),
) -> Dict[str, Any]:
    try:
        evento_json: Dict[str, Any] = await peticion.json()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cuerpo JSON del webhook inválido.",
        ) from exc

    if not verificar_firma_webhook_wompi(
        evento_json=evento_json, checksum_cabecera=x_event_checksum
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firma criptográfica del webhook de Wompi inválida.",
        )

    tipo_evento = str(evento_json.get("event") or "").upper()
    if tipo_evento != "TRANSACTION.UPDATED":
        return {"status": "ignored", "event": tipo_evento}

    transaccion = (evento_json.get("data") or {}).get("transaction") or {}
    transaccion_id = str(transaccion.get("id") or "").strip()
    referencia = str(transaccion.get("reference") or "").strip()
    estado_wompi = str(transaccion.get("status") or "PENDING")
    metodo_pago = str(transaccion.get("payment_method_type") or "WOMPI")

    if not referencia or not transaccion_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El evento no contiene referencia o ID de transacción.",
        )

    pedido = sesion_bd.scalar(
        select(Pedido)
        .options(
            joinedload(Pedido.comprador),
            joinedload(Pedido.detalles)
            .joinedload(DetallePedido.lote_cafe)
            .joinedload(LoteCafe.finca)
            .joinedload(Finca.propietario),
        )
        .where(Pedido.referencia_pago == referencia)
        .with_for_update()
    )
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe pedido asociado a la referencia {referencia}.",
        )

    nuevo_estado = mapear_estado_wompi_a_pedido(estado_wompi)
    if estado_wompi.strip().upper() == "APPROVED":
        nuevo_estado = EstadoPedido.PAGADO

    if (
        pedido.transaccion_pasarela_id == transaccion_id
        and pedido.estado == nuevo_estado
    ):
        return {
            "status": "already_processed",
            "order_id": str(pedido.id),
            "order_status": pedido.estado.value,
        }

    pedido.transaccion_pasarela_id = transaccion_id
    pedido.metodo_pago = metodo_pago
    pedido.estado = nuevo_estado
    sesion_bd.commit()

    if nuevo_estado in (EstadoPedido.PAGADO, EstadoPedido.COMPLETADO):
        alertas_caficultores: List[Dict[str, str]] = []
        lineas_factura: List[Dict[str, Any]] = []

        for detalle in pedido.detalles:
            lote = detalle.lote_cafe
            finca = lote.finca if lote else None
            propietario = finca.propietario if finca else None

            if propietario and propietario.telefono:
                alertas_caficultores.append(
                    {
                        "telefono": propietario.telefono,
                        "nombre": propietario.nombre_completo,
                        "lote": f"{lote.nombre} ({lote.variedad.value})",
                        "cantidad_texto": f"{detalle.cantidad} x {detalle.unidad_venta.value} ({detalle.tipo_molienda.value})",
                        "ciudad_destino": f"{pedido.ciudad_envio}, {pedido.departamento_envio}",
                        "referencia": referencia,
                    }
                )

            lineas_factura.append(
                {
                    "lote": lote.nombre if lote else "Café Especial Tolima",
                    "presentacion": detalle.unidad_venta.value,
                    "molienda": detalle.tipo_molienda.value,
                    "cantidad": detalle.cantidad,
                    "subtotal_cop": detalle.subtotal_cop,
                }
            )

        datos_correo = {
            "correo": (
                pedido.comprador.correo
                if pedido.comprador and pedido.comprador.correo
                else "comprador@maicofi.co"
            ),
            "nombre": (
                pedido.comprador.nombre_completo
                if pedido.comprador
                else "Cliente Maicofi"
            ),
            "referencia": referencia,
            "monto_subtotal_cop": pedido.monto_total_cop,
            "costo_envio_cop": pedido.costo_envio_cop,
            "lineas": lineas_factura,
        }

        tareas_fondo.add_task(
            procesar_facturacion_y_notificaciones_post_pago,
            pedido.id,
            alertas_caficultores,
            datos_correo,
        )

    return {
        "status": "processed",
        "order_id": str(pedido.id),
        "reference": referencia,
        "order_status": pedido.estado.value,
    }


@enrutador_integraciones.post(
    "/invoices/order/{pedido_id}/emit",
    response_model=LeerFacturaElectronicaEsquema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(dependencia_limite_escritura)],
    summary="Emitir o reintentar Factura Electrónica DIAN para un pedido",
)
async def emitir_o_reintentar_factura_dian(
    pedido_id: uuid.UUID,
    sesion_bd: Session = Depends(obtener_bd),
) -> FacturaElectronica:
    await emitir_factura_electronica_dian(pedido_id=pedido_id)
    factura = sesion_bd.scalar(
        select(FacturaElectronica).where(FacturaElectronica.pedido_id == pedido_id)
    )
    if not factura:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No fue posible generar la factura electrónica para el pedido indicado.",
        )
    return factura


@enrutador_integraciones.get(
    "/invoices/order/{pedido_id}",
    response_model=LeerFacturaElectronicaEsquema,
    summary="Consultar Factura Electrónica DIAN y CUFE por ID de pedido",
)
async def obtener_factura_electronica_pedido(
    pedido_id: uuid.UUID,
    sesion_bd: Session = Depends(obtener_bd),
) -> FacturaElectronica:
    factura = sesion_bd.scalar(
        select(FacturaElectronica).where(FacturaElectronica.pedido_id == pedido_id)
    )
    if not factura:
        await emitir_factura_electronica_dian(pedido_id=pedido_id)
        factura = sesion_bd.scalar(
            select(FacturaElectronica).where(FacturaElectronica.pedido_id == pedido_id)
        )
    if not factura:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Factura electrónica no encontrada para este pedido.",
        )
    return factura


@enrutador_integraciones.get(
    "/invoices/order/{pedido_id}/pdf",
    response_class=HTMLResponse,
    summary="Visualizar y descargar Representación Gráfica de Factura Electrónica DIAN",
)
async def descargar_representacion_grafica_dian(
    pedido_id: uuid.UUID,
    sesion_bd: Session = Depends(obtener_bd),
) -> HTMLResponse:
    pedido = sesion_bd.scalar(
        select(Pedido)
        .options(
            joinedload(Pedido.comprador),
            joinedload(Pedido.datos_fiscales),
            joinedload(Pedido.factura_electronica),
            joinedload(Pedido.detalles).joinedload(DetallePedido.lote_cafe),
        )
        .where(Pedido.id == pedido_id)
    )
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado.",
        )

    if not pedido.factura_electronica:
        await emitir_factura_electronica_dian(pedido_id=pedido.id)
        sesion_bd.expire_all()
        pedido = sesion_bd.scalar(
            select(Pedido)
            .options(
                joinedload(Pedido.comprador),
                joinedload(Pedido.datos_fiscales),
                joinedload(Pedido.factura_electronica),
                joinedload(Pedido.detalles).joinedload(DetallePedido.lote_cafe),
            )
            .where(Pedido.id == pedido_id)
        )

    lineas = [
        {
            "lote": d.lote_cafe.nombre if d.lote_cafe else "Café Especial Tolima",
            "presentacion": d.unidad_venta.value,
            "molienda": d.tipo_molienda.value,
            "cantidad": d.cantidad,
            "subtotal_cop": d.subtotal_cop,
        }
        for d in (pedido.detalles if pedido else [])
    ]
    factura = pedido.factura_electronica if pedido else None
    datos_fiscales = pedido.datos_fiscales if pedido else None
    nombre_cliente = (
        datos_fiscales.razon_social_o_nombre
        if datos_fiscales
        else (pedido.comprador.nombre_completo if pedido and pedido.comprador else "Adquirente")
    )

    html = construir_factura_html_maicofi(
        nombre_comprador=nombre_cliente,
        referencia_pedido=factura.numero_factura if factura else str(pedido_id)[:8],
        monto_total_cop=pedido.monto_total_cop if pedido else Decimal("0"),
        costo_envio_cop=pedido.costo_envio_cop if pedido else Decimal("0"),
        lineas_detalle=lineas,
        cufe_dian=factura.cufe if factura else None,
        url_pdf_dian=None,
    )
    return HTMLResponse(content=html)


@enrutador_integraciones.get(
    "/invoices/order/{pedido_id}/xml",
    summary="Descargar AttachedDocument XML UBL 2.1 firmado para la DIAN",
)
async def descargar_xml_ubl_dian(
    pedido_id: uuid.UUID,
    sesion_bd: Session = Depends(obtener_bd),
) -> Response:
    factura = sesion_bd.scalar(
        select(FacturaElectronica).where(FacturaElectronica.pedido_id == pedido_id)
    )
    cufe = factura.cufe if factura and factura.cufe else "CUFE-PENDIENTE"
    numero = factura.numero_factura if factura else "SETT-0000"
    xml_ubl = f"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
  <cbc:UBLVersionID>UBL 2.1</cbc:UBLVersionID>
  <cbc:CustomizationID>10</cbc:CustomizationID>
  <cbc:ProfileID>DIAN 2.1: Factura Electrónica de Venta</cbc:ProfileID>
  <cbc:ID>{numero}</cbc:ID>
  <cbc:UUID schemeName="CUFE-SHA384">{cufe}</cbc:UUID>
  <cbc:DocumentCurrencyCode>COP</cbc:DocumentCurrencyCode>
</Invoice>"""
    return Response(
        content=xml_ubl,
        media_type="application/xml",
        headers={
            "Content-Disposition": f'attachment; filename="Factura_DIAN_{numero}.xml"'
        },
    )


@enrutador_integraciones.post(
    "/shipping/quote",
    response_model=RespuestaCotizacionEnvioEsquema,
    summary="Cotizar flete nacional desde un municipio del Tolima según peso volumétrico",
)
async def calcular_cotizacion_envio(
    solicitud: SolicitudCotizacionEnvioEsquema,
) -> RespuestaCotizacionEnvioEsquema:
    resultado = await cotizar_envio_nacional(
        municipio_origen=solicitud.municipio_origen,
        ciudad_destino=solicitud.ciudad_destino,
        departamento_destino=solicitud.departamento_destino,
        peso_total_kg=solicitud.peso_total_kg,
    )
    return RespuestaCotizacionEnvioEsquema(**resultado)


@enrutador_integraciones.post(
    "/media/upload",
    response_model=RespuestaSubidaImagenEsquema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(dependencia_limite_escritura)],
    summary="Subir fotografía de finca o lote a Cloudinary con conversión automática a WebP",
)
async def subir_imagen_finca_o_lote(
    archivo: UploadFile = File(..., alias="file"),
    _usuario_actual: Usuario = Depends(
        requerir_roles([RolUsuario.CAFICULTOR, RolUsuario.ADMINISTRADOR])
    ),
) -> RespuestaSubidaImagenEsquema:
    datos_cloudinary = await subir_y_optimizar_imagen_cloudinary(archivo=archivo)
    return RespuestaSubidaImagenEsquema(**datos_cloudinary)
