import asyncio
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import logging
from typing import Any, Dict, List, Optional
import uuid

import httpx
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.core.configuracion import configuracion
from app.db.conexion import SesionLocal
from app.models.entidades import (
    DatosFiscalesCliente,
    DetallePedido,
    EstadoDianFactura,
    EstadoGrano,
    FacturaElectronica,
    LoteCafe,
    Pedido,
    RegimenTributario,
    TipoDocumentoFiscal,
    TipoPersonaFiscal,
)
from app.schemas.dominio import calcular_digito_verificacion_nit_dian

registro_log = logging.getLogger("maicofi.facturacion_dian")


def obtener_porcentaje_iva_cafe(estado_grano: EstadoGrano) -> Decimal:
    """
    Aplica el Estatuto Tributario Colombiano (Art. 424 y Art. 468-1):
    - Café en grano sin tostar (Pergamino Seco o Excelso Verde): 0% IVA (Excluido).
    - Café tostado en grano o molido: 5% IVA (Tarifa diferencial bienes de la canasta cafetera).
    """
    if estado_grano in (EstadoGrano.PERGAMINO_SECO, EstadoGrano.VERDE_TRILLADO):
        return Decimal("0.00")
    return Decimal("5.00")


def calcular_cufe_dian_sha384(
    numero_factura: str,
    fecha_emision: str,
    hora_emision: str,
    valor_base_sin_impuestos: Decimal,
    valor_iva: Decimal,
    valor_total_con_impuestos: Decimal,
    nit_emisor: str,
    documento_adquirente: str,
    clave_tecnica: str,
    ambiente_pruebas: bool = True,
) -> str:
    """
    Calcula el Código Único de Facturación Electrónica (CUFE) con algoritmo SHA-384
    según el Anexo Técnico 1.9 de la DIAN Colombia.
    """
    tipo_ambiente = "2" if ambiente_pruebas else "1"
    nit_limpio = nit_emisor.split("-")[0].strip()
    cadena_cufe = (
        f"{numero_factura}"
        f"{fecha_emision}"
        f"{hora_emision}"
        f"{valor_base_sin_impuestos:.2f}"
        f"01{valor_iva:.2f}"
        f"040.00"
        f"030.00"
        f"{valor_total_con_impuestos:.2f}"
        f"{nit_limpio}"
        f"{documento_adquirente}"
        f"{clave_tecnica}"
        f"{tipo_ambiente}"
    )
    return hashlib.sha384(cadena_cufe.encode("utf-8")).hexdigest()


def construir_payload_proveedor_dian(
    pedido: Pedido,
    datos_fiscales: DatosFiscalesCliente,
    numero_consecutivo: int,
) -> Dict[str, Any]:
    """
    Transforma el pedido interno de Maicofi al formato JSON estandarizado en inglés
    exigido por el Proveedor Tecnológico autorizado por la DIAN (Dataico / Alegra API).
    """
    ahora_co = datetime.now(timezone.utc)
    fecha_str = ahora_co.strftime("%d/%m/%Y")

    lineas_json: List[Dict[str, Any]] = []
    base_gravable_total = Decimal("0.00")
    impuesto_iva_total = Decimal("0.00")

    for detalle in pedido.detalles:
        lote = detalle.lote_cafe
        estado_grano = (
            lote.estado_presentacion if lote else EstadoGrano.TOSTADO_GRANO
        )
        tasa_iva = obtener_porcentaje_iva_cafe(estado_grano)

        divisor_iva = Decimal("1.00") + (tasa_iva / Decimal("100.00"))
        precio_unitario_base = (detalle.precio_unitario_cop / divisor_iva).quantize(
            Decimal("0.01")
        )
        subtotal_base = (precio_unitario_base * Decimal(detalle.cantidad)).quantize(
            Decimal("0.01")
        )
        iva_linea = (detalle.subtotal_cop - subtotal_base).quantize(Decimal("0.01"))

        base_gravable_total += subtotal_base
        impuesto_iva_total += iva_linea

        lineas_json.append(
            {
                "sku": str(detalle.lote_cafe_id)[:8].upper(),
                "description": (
                    f"{lote.nombre if lote else 'Café Especial Tolima'} - "
                    f"{detalle.unidad_venta.value} ({detalle.tipo_molienda.value})"
                ),
                "quantity": detalle.cantidad,
                "price": float(precio_unitario_base),
                "taxes": [
                    {
                        "tax_category": "IVA",
                        "tax_rate": float(tasa_iva),
                        "tax_amount": float(iva_linea),
                    }
                ],
            }
        )

    if pedido.costo_envio_cop > 0:
        base_gravable_total += pedido.costo_envio_cop
        lineas_json.append(
            {
                "sku": "FLETE-NAC",
                "description": f"Servicio de Transporte Terrestre de Carga Cafetera ({pedido.ciudad_envio})",
                "quantity": 1,
                "price": float(pedido.costo_envio_cop),
                "taxes": [
                    {
                        "tax_category": "IVA",
                        "tax_rate": 0.0,
                        "tax_amount": 0.0,
                    }
                ],
            }
        )

    tipo_persona_dian = (
        "LEGAL_ENTITY"
        if datos_fiscales.tipo_persona == TipoPersonaFiscal.JURIDICA
        else "NATURAL_PERSON"
    )
    nivel_tributario_dian = (
        "COMUN"
        if datos_fiscales.regimen_tributario
        in (RegimenTributario.RESPONSABLE_IVA, RegimenTributario.GRAN_CONTRIBUYENTE)
        else "SIMPLIFICADO"
    )

    # Contrato JSON externo en inglés para el Proveedor Tecnológico (Dataico / Alegra)
    return {
        "actions": {
            "send_dian": True,
            "send_email": False,
        },
        "invoice": {
            "env": "PRUEBAS" if configuracion.MODO_PRUEBAS_DIAN else "PRODUCCION",
            "dataico_account_id": configuracion.NIT_EMPRESA_EMISORA,
            "number": numero_consecutivo,
            "issue_date": fecha_str,
            "payment_means_type": "CONTADO",
            "payment_means": "TRANSFERENCIA_DEBITO",
            "numbering": {
                "resolution_number": configuracion.RESOLUCION_DIAN,
                "prefix": configuracion.PREFIJO_FACTURA_DIAN,
                "flexible": True,
            },
            "customer": {
                "party_identification_type": datos_fiscales.tipo_documento.value,
                "party_identification": datos_fiscales.numero_documento,
                "check_digit": datos_fiscales.digito_verificacion or "",
                "party_type": tipo_persona_dian,
                "tax_level_code": nivel_tributario_dian,
                "regimen": datos_fiscales.regimen_tributario.value,
                "company_name": datos_fiscales.razon_social_o_nombre,
                "first_name": datos_fiscales.razon_social_o_nombre,
                "email": datos_fiscales.correo_facturacion,
                "phone": pedido.telefono_contacto,
                "address_line": datos_fiscales.direccion_fiscal,
                "city_code": datos_fiscales.codigo_municipio_dane,
                "country_code": "CO",
            },
            "items": lineas_json,
        },
        "_resumen_interno": {
            "base_gravable_cop": base_gravable_total,
            "iva_total_cop": impuesto_iva_total,
            "total_factura_cop": base_gravable_total + impuesto_iva_total,
        },
    }


async def enviar_factura_a_proveedor_dian(
    payload_json: Dict[str, Any],
    numero_factura: str,
    pedido_id: uuid.UUID,
    documento_adquirente: str,
) -> Dict[str, Any]:
    """
    Consume de forma asíncrona con reintentos la API del Proveedor Tecnológico (Dataico / Alegra)
    mediante httpx. Retorna un diccionario interno en español con CUFE, QR, PDF, XML y estado DIAN.
    """
    resumen = payload_json.pop("_resumen_interno")
    ahora = datetime.now(timezone.utc)
    fecha_iso = ahora.strftime("%Y-%m-%d")
    hora_iso = ahora.strftime("%H:%M:%S-05:00")

    cufe_generado = calcular_cufe_dian_sha384(
        numero_factura=numero_factura,
        fecha_emision=fecha_iso,
        hora_emision=hora_iso,
        valor_base_sin_impuestos=resumen["base_gravable_cop"],
        valor_iva=resumen["iva_total_cop"],
        valor_total_con_impuestos=resumen["total_factura_cop"],
        nit_emisor=configuracion.NIT_EMPRESA_EMISORA,
        documento_adquirente=documento_adquirente,
        clave_tecnica=configuracion.FACTURACION_API_KEY,
        ambiente_pruebas=configuracion.MODO_PRUEBAS_DIAN,
    )

    # Validación preventiva de negocio antes de transmitir a la DIAN
    if len(documento_adquirente.strip()) < 5:
        return {
            "estado_dian": EstadoDianFactura.RECHAZADA,
            "cufe": None,
            "url_codigo_qr": None,
            "url_pdf": None,
            "url_xml": None,
            "mensaje_error_dian": (
                "Rechazo Regla DIAN FAD09: El número de documento del adquirente es inválido."
            ),
        }

    # Si no estamos en modo pruebas local y hay llave real del proveedor tecnológico, transmitir por HTTP
    if (
        not configuracion.MODO_PRUEBAS_DIAN
        and configuracion.FACTURACION_API_KEY
        and configuracion.FACTURACION_API_KEY != "dian_test_key_maicofi_2026"
    ):
        ultimo_error = ""
        for intento in range(1, 3):
            try:
                async with httpx.AsyncClient(timeout=15.0) as cliente:
                    respuesta = await cliente.post(
                        configuracion.FACTURACION_ENDPOINT,
                        headers={
                            "Auth-token": configuracion.FACTURACION_API_KEY,
                            "Content-Type": "application/json",
                        },
                        json=payload_json,
                    )
                    if respuesta.status_code in (200, 201):
                        datos = respuesta.json()
                        cufe_remoto = datos.get("cufe") or cufe_generado
                        return {
                            "estado_dian": EstadoDianFactura.APROBADA,
                            "cufe": cufe_remoto,
                            "url_codigo_qr": datos.get(
                                "qrcode_url",
                                f"https://catalogo-vpfe.dian.gov.co/document/searchqr?documentkey={cufe_remoto}",
                            ),
                            "url_pdf": datos.get(
                                "pdf_url",
                                f"http://127.0.0.1:{configuracion.PUERTO_BACKEND}/api/v1/invoices/order/{pedido_id}/pdf",
                            ),
                            "url_xml": datos.get(
                                "xml_url",
                                f"http://127.0.0.1:{configuracion.PUERTO_BACKEND}/api/v1/invoices/order/{pedido_id}/xml",
                            ),
                            "mensaje_error_dian": None,
                        }
                    ultimo_error = (
                        f"HTTP {respuesta.status_code}: {respuesta.text[:300]}"
                    )
            except httpx.HTTPError as exc:
                ultimo_error = f"Error de red con proveedor tecnológico (intento {intento}): {exc}"
                await asyncio.sleep(1.0)

        registro_log.error(
            "Fallo en emisión de factura electrónica DIAN para pedido %s: %s",
            pedido_id,
            ultimo_error,
        )
        return {
            "estado_dian": EstadoDianFactura.RECHAZADA,
            "cufe": None,
            "url_codigo_qr": None,
            "url_pdf": None,
            "url_xml": None,
            "mensaje_error_dian": ultimo_error,
        }

    # Modo Habilitación / Pruebas DIAN (TEST_MODE_DIAN=true)
    url_base_local = f"http://127.0.0.1:{configuracion.PUERTO_BACKEND}{configuracion.PREFIJO_API}"
    return {
        "estado_dian": EstadoDianFactura.APROBADA,
        "cufe": cufe_generado,
        "url_codigo_qr": (
            f"https://catalogo-vpfe-hab.dian.gov.co/document/searchqr?documentkey={cufe_generado}"
        ),
        "url_pdf": f"{url_base_local}/invoices/order/{pedido_id}/pdf",
        "url_xml": f"{url_base_local}/invoices/order/{pedido_id}/xml",
        "mensaje_error_dian": None,
    }


async def emitir_factura_electronica_dian(
    pedido_id: uuid.UUID,
) -> Optional[Dict[str, Any]]:
    """
    Orquesta en segundo plano la creación, transmisión a la DIAN y persistencia en PostgreSQL
    de la Factura Electrónica asociada a un pedido pagado, sin bloquear ni revertir el pago.
    """
    with SesionLocal() as sesion:
        pedido = sesion.scalar(
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
            return None

        if (
            pedido.factura_electronica
            and pedido.factura_electronica.estado_dian == EstadoDianFactura.APROBADA
        ):
            return {
                "numero_factura": pedido.factura_electronica.numero_factura,
                "cufe": pedido.factura_electronica.cufe,
                "url_pdf": pedido.factura_electronica.url_pdf,
                "url_xml": pedido.factura_electronica.url_xml,
                "url_codigo_qr": pedido.factura_electronica.url_codigo_qr,
                "estado_dian": pedido.factura_electronica.estado_dian.value,
            }

        # Si el comprador no diligenció datos fiscales explícitos, crear perfil fiscal por defecto (Consumidor Final / Comprador)
        datos_fiscales = pedido.datos_fiscales
        if not datos_fiscales:
            nombre_adquirente = (
                pedido.comprador.nombre_completo
                if pedido.comprador
                else "Consumidor Final"
            )
            correo_adquirente = (
                pedido.comprador.correo
                if pedido.comprador and pedido.comprador.correo
                else "facturacion@maicofi.co"
            )
            datos_fiscales = DatosFiscalesCliente(
                pedido_id=pedido.id,
                usuario_id=pedido.comprador_id,
                tipo_documento=TipoDocumentoFiscal.CC,
                numero_documento="222222222222",
                digito_verificacion=calcular_digito_verificacion_nit_dian("222222222222"),
                razon_social_o_nombre=nombre_adquirente,
                correo_facturacion=correo_adquirente,
                tipo_persona=TipoPersonaFiscal.NATURAL,
                regimen_tributario=RegimenTributario.NO_RESPONSABLE_IVA,
                direccion_fiscal=pedido.direccion_envio,
                codigo_municipio_dane="73001",
            )
            sesion.add(datos_fiscales)
            sesion.flush()

        consecutivo = int(str(pedido.id.int)[:6])
        numero_factura = f"{configuracion.PREFIJO_FACTURA_DIAN}-{consecutivo}"

        payload_dian = construir_payload_proveedor_dian(
            pedido=pedido,
            datos_fiscales=datos_fiscales,
            numero_consecutivo=consecutivo,
        )

        resultado_dian = await enviar_factura_a_proveedor_dian(
            payload_json=payload_dian,
            numero_factura=numero_factura,
            pedido_id=pedido.id,
            documento_adquirente=datos_fiscales.numero_documento,
        )

        if pedido.factura_electronica:
            factura = pedido.factura_electronica
            factura.cufe = resultado_dian["cufe"]
            factura.url_codigo_qr = resultado_dian["url_codigo_qr"]
            factura.url_pdf = resultado_dian["url_pdf"]
            factura.url_xml = resultado_dian["url_xml"]
            factura.estado_dian = resultado_dian["estado_dian"]
            factura.mensaje_error_dian = resultado_dian["mensaje_error_dian"]
        else:
            factura = FacturaElectronica(
                pedido_id=pedido.id,
                numero_factura=numero_factura,
                cufe=resultado_dian["cufe"],
                url_codigo_qr=resultado_dian["url_codigo_qr"],
                url_pdf=resultado_dian["url_pdf"],
                url_xml=resultado_dian["url_xml"],
                estado_dian=resultado_dian["estado_dian"],
                mensaje_error_dian=resultado_dian["mensaje_error_dian"],
            )
            sesion.add(factura)

        sesion.commit()
        sesion.refresh(factura)

        return {
            "numero_factura": factura.numero_factura,
            "cufe": factura.cufe,
            "url_pdf": factura.url_pdf,
            "url_xml": factura.url_xml,
            "url_codigo_qr": factura.url_codigo_qr,
            "estado_dian": factura.estado_dian.value,
        }
