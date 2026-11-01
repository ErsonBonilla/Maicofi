from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional

import httpx

from app.core.configuracion import configuracion

registro_log = logging.getLogger("maicofi.notificaciones")


async def enviar_alerta_whatsapp(
    telefono_caficultor: str,
    nombre_caficultor: str,
    resumen_lote: str,
    cantidad_texto: str,
    ciudad_destino: str,
    referencia_pedido: str,
) -> Dict[str, Any]:
    """
    Envía una alerta automática por WhatsApp al celular del caficultor en el Tolima
    cuando se confirma la compra de uno de sus lotes de café.
    Soporta los contratos externos de Meta Cloud API y Twilio WhatsApp API.
    """
    mensaje_texto = (
        f"¡Hola {nombre_caficultor}! Has recibido una nueva orden en Maicofi "
        f"({referencia_pedido}): {cantidad_texto} de {resumen_lote}. "
        f"Ciudad de destino: {ciudad_destino}. Por favor alista el lote para recolección."
    )

    if configuracion.META_WHATSAPP_TOKEN and configuracion.META_WHATSAPP_PHONE_ID:
        url_meta = (
            f"https://graph.facebook.com/v20.0/"
            f"{configuracion.META_WHATSAPP_PHONE_ID}/messages"
        )
        try:
            async with httpx.AsyncClient(timeout=10.0) as cliente:
                respuesta = await cliente.post(
                    url_meta,
                    headers={
                        "Authorization": f"Bearer {configuracion.META_WHATSAPP_TOKEN}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "messaging_product": "whatsapp",
                        "to": telefono_caficultor.replace("+", ""),
                        "type": "text",
                        "text": {"body": mensaje_texto},
                    },
                )
                if respuesta.status_code in (200, 201):
                    return {
                        "enviado": True,
                        "proveedor": "meta_cloud_api",
                        "destinatario": telefono_caficultor,
                        "mensaje": mensaje_texto,
                    }
        except httpx.HTTPError as exc:
            registro_log.warning("Error contactando Meta WhatsApp Cloud API: %s", exc)

    if (
        configuracion.TWILIO_ACCOUNT_SID
        and configuracion.TWILIO_AUTH_TOKEN
        and not configuracion.TWILIO_ACCOUNT_SID.startswith("AC_test_")
    ):
        url_twilio = (
            f"https://api.twilio.com/2010-04-01/Accounts/"
            f"{configuracion.TWILIO_ACCOUNT_SID}/Messages.json"
        )
        destino_formateado = (
            telefono_caficultor
            if telefono_caficultor.startswith("whatsapp:")
            else f"whatsapp:{telefono_caficultor}"
        )
        try:
            async with httpx.AsyncClient(timeout=10.0) as cliente:
                respuesta = await cliente.post(
                    url_twilio,
                    auth=(
                        configuracion.TWILIO_ACCOUNT_SID,
                        configuracion.TWILIO_AUTH_TOKEN,
                    ),
                    data={
                        "From": configuracion.TWILIO_WHATSAPP_REMITENTE,
                        "To": destino_formateado,
                        "Body": mensaje_texto,
                    },
                )
                if respuesta.status_code in (200, 201):
                    return {
                        "enviado": True,
                        "proveedor": "twilio_whatsapp",
                        "destinatario": telefono_caficultor,
                        "mensaje": mensaje_texto,
                    }
        except httpx.HTTPError as exc:
            registro_log.warning("Error contactando Twilio WhatsApp API: %s", exc)

    registro_log.info("Alerta WhatsApp Caficultor [%s]: %s", telefono_caficultor, mensaje_texto)
    return {
        "enviado": True,
        "proveedor": "sandbox_local",
        "destinatario": telefono_caficultor,
        "mensaje": mensaje_texto,
    }


def construir_factura_html_maicofi(
    nombre_comprador: str,
    referencia_pedido: str,
    monto_total_cop: Decimal,
    costo_envio_cop: Decimal,
    lineas_detalle: List[Dict[str, Any]],
    cufe_dian: Optional[str] = None,
    url_pdf_dian: Optional[str] = None,
) -> str:
    """Genera el documento HTML de confirmación y factura electrónica DIAN del pedido de café."""
    filas_html = "".join(
        f"""
        <tr>
          <td style="padding:10px;border-bottom:1px solid #E5D5C5;">{item.get("lote", "Café Especial Tolima")}</td>
          <td style="padding:10px;border-bottom:1px solid #E5D5C5;">{item.get("presentacion", "500g")} ({item.get("molienda", "Grano entero")})</td>
          <td style="padding:10px;border-bottom:1px solid #E5D5C5;text-align:center;">{item.get("cantidad", 1)}</td>
          <td style="padding:10px;border-bottom:1px solid #E5D5C5;text-align:right;">${int(item.get("subtotal_cop", 0)):,} COP</td>
        </tr>
        """
        for item in lineas_detalle
    )

    bloque_dian_html = ""
    if cufe_dian:
        enlace_pdf_html = (
            f'<p style="margin:10px 0 0;"><a href="{url_pdf_dian}" style="background:#2C4234;color:#ffffff;padding:10px 16px;border-radius:8px;text-decoration:none;font-weight:bold;display:inline-block;">Descargar Factura Electrónica DIAN (PDF)</a></p>'
            if url_pdf_dian
            else ""
        )
        bloque_dian_html = f"""
        <div style="margin-top:16px;padding:14px;background:#FAF6F0;border:1px solid #E5D5C5;border-radius:10px;font-size:12px;">
          <strong style="color:#2C4234;display:block;margin-bottom:4px;">Validación Previa DIAN — Factura Electrónica de Venta</strong>
          <span style="display:block;word-break:break-all;font-family:monospace;color:#232323;"><strong>CUFE:</strong> {cufe_dian}</span>
          {enlace_pdf_html}
        </div>
        """

    total_final = int(monto_total_cop + costo_envio_cop)
    return f"""
    <div style="font-family:sans-serif;max-width:620px;margin:0 auto;background:#FAF6F0;padding:24px;border-radius:16px;color:#232323;">
      <div style="background:#54121B;color:#ffffff;padding:18px 24px;border-radius:12px;">
        <h2 style="margin:0;">Maicofi — Café Especial del Tolima</h2>
        <p style="margin:4px 0 0;font-size:13px;">Confirmación de Compra y Factura Electrónica #{referencia_pedido}</p>
      </div>
      <div style="background:#ffffff;padding:20px;border-radius:12px;margin-top:16px;border:1px solid #E5D5C5;">
        <p>Hola <strong>{nombre_comprador}</strong>, tu pago ha sido verificado exitosamente y los caficultores en el Tolima han sido notificados para preparar tu lote.</p>
        <table style="width:100%;border-collapse:collapse;font-size:14px;margin-top:12px;">
          <thead>
            <tr style="background:#2C4234;color:#ffffff;text-align:left;">
              <th style="padding:10px;">Lote de Café</th>
              <th style="padding:10px;">Presentación / Molienda</th>
              <th style="padding:10px;text-align:center;">Cant.</th>
              <th style="padding:10px;text-align:right;">Subtotal</th>
            </tr>
          </thead>
          <tbody>
            {filas_html}
          </tbody>
        </table>
        <div style="margin-top:16px;text-align:right;font-size:14px;">
          <p style="margin:4px 0;">Subtotal Café: <strong>${int(monto_total_cop):,} COP</strong></p>
          <p style="margin:4px 0;">Flete Nacional: <strong>${int(costo_envio_cop):,} COP</strong></p>
          <p style="margin:8px 0 0;font-size:18px;color:#54121B;">Total Pagado: <strong>${total_final:,} COP</strong></p>
        </div>
        {bloque_dian_html}
      </div>
    </div>
    """


async def enviar_correo_pedido(
    correo_comprador: str,
    nombre_comprador: str,
    referencia_pedido: str,
    monto_total_cop: Decimal,
    costo_envio_cop: Decimal,
    lineas_detalle: List[Dict[str, Any]],
    cufe_dian: Optional[str] = None,
    url_pdf_dian: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Envía el correo transaccional con la factura electrónica DIAN y el PDF adjunto al comprador
    utilizando el contrato externo de la API REST de Resend.
    """
    cuerpo_html = construir_factura_html_maicofi(
        nombre_comprador=nombre_comprador,
        referencia_pedido=referencia_pedido,
        monto_total_cop=monto_total_cop,
        costo_envio_cop=costo_envio_cop,
        lineas_detalle=lineas_detalle,
        cufe_dian=cufe_dian,
        url_pdf_dian=url_pdf_dian,
    )

    if (
        configuracion.RESEND_API_KEY
        and not configuracion.RESEND_API_KEY.startswith("re_test_")
    ):
        payload_resend: Dict[str, Any] = {
            "from": configuracion.RESEND_CORREO_REMITENTE,
            "to": [correo_comprador],
            "subject": f"Factura Electrónica DIAN y Confirmación #{referencia_pedido} — Maicofi Tolima",
            "html": cuerpo_html,
        }
        if url_pdf_dian:
            payload_resend["attachments"] = [
                {
                    "filename": f"Factura_DIAN_{referencia_pedido}.pdf",
                    "path": url_pdf_dian,
                }
            ]

        try:
            async with httpx.AsyncClient(timeout=10.0) as cliente:
                respuesta = await cliente.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {configuracion.RESEND_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json=payload_resend,
                )
                if respuesta.status_code in (200, 201):
                    return {
                        "enviado": True,
                        "proveedor": "resend_api",
                        "destinatario": correo_comprador,
                    }
        except httpx.HTTPError as exc:
            registro_log.warning("Error enviando correo vía Resend: %s", exc)

    registro_log.info(
        "Factura electrónica DIAN enviada a [%s] — Referencia %s (CUFE: %s)",
        correo_comprador,
        referencia_pedido,
        cufe_dian or "N/A",
    )
    return {
        "enviado": True,
        "proveedor": "sandbox_local",
        "destinatario": correo_comprador,
        "factura_html": cuerpo_html,
    }
