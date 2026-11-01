from decimal import Decimal
import hashlib
import hmac
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode
import uuid

import httpx

from app.core.configuracion import configuracion
from app.models.entidades import EstadoPedido


def generar_referencia_pago_unica(pedido_id: uuid.UUID) -> str:
    """Genera una referencia única trazable para la transacción en Wompi."""
    prefijo = str(pedido_id).split("-")[0].upper()
    sufijo = uuid.uuid4().hex[:6].upper()
    return f"MAICOFI-TOL-{prefijo}-{sufijo}"


def calcular_firma_integridad_wompi(
    referencia: str,
    monto_en_centavos: int,
    moneda: str = "COP",
    secreto_integridad: Optional[str] = None,
) -> str:
    """
    Calcula el hash SHA-256 exigido por Wompi Colombia para proteger la integridad del monto:
    SHA256('<Referencia><MontoEnCentavos><Moneda><SecretoIntegridad>')
    """
    secreto = secreto_integridad or configuracion.WOMPI_SECRETO_INTEGRIDAD
    cadena_integridad = f"{referencia}{monto_en_centavos}{moneda}{secreto}"
    return hashlib.sha256(cadena_integridad.encode("utf-8")).hexdigest()


def extraer_propiedad_anidada(diccionario: Dict[str, Any], ruta_punto: str) -> str:
    """Obtiene el valor de una ruta tipo 'transaction.id' dentro del objeto 'data' del evento."""
    actual: Any = diccionario
    for parte in ruta_punto.split("."):
        if isinstance(actual, dict):
            actual = actual.get(parte)
        else:
            return ""
    return "" if actual is None else str(actual)


def verificar_firma_webhook_wompi(
    evento_json: Dict[str, Any],
    checksum_cabecera: Optional[str] = None,
    secreto_eventos: Optional[str] = None,
) -> bool:
    """
    Verifica criptográficamente en tiempo constante la autenticidad del evento enviado
    por el Webhook de Wompi (TRANSACTION.UPDATED / transaction.updated).
    """
    secreto = secreto_eventos or configuracion.WOMPI_SECRETO_EVENTOS
    bloque_firma = evento_json.get("signature") or {}
    propiedades: List[str] = bloque_firma.get("properties") or [
        "transaction.id",
        "transaction.status",
        "transaction.amount_in_cents",
    ]
    checksum_esperado = (
        checksum_cabecera
        or bloque_firma.get("checksum")
        or ""
    ).strip().lower()

    if not checksum_esperado:
        return False

    datos_evento = evento_json.get("data") or {}
    valores_concatenados = "".join(
        extraer_propiedad_anidada(datos_evento, prop) for prop in propiedades
    )
    marca_tiempo = str(evento_json.get("timestamp") or "")
    cadena_verificacion = f"{valores_concatenados}{marca_tiempo}{secreto}"

    checksum_calculado = (
        hashlib.sha256(cadena_verificacion.encode("utf-8")).hexdigest().lower()
    )
    return hmac.compare_digest(checksum_calculado, checksum_esperado)


def mapear_estado_wompi_a_pedido(estado_wompi: str) -> EstadoPedido:
    """Traduce el estado de transacción de Wompi al estado de dominio del pedido en PostgreSQL."""
    normalizado = estado_wompi.strip().upper()
    if normalizado in {"APPROVED", "COMPLETED", "PAID"}:
        return EstadoPedido.COMPLETADO
    if normalizado in {"DECLINED", "REJECTED", "VOIDED", "ERROR"}:
        return EstadoPedido.RECHAZADO
    return EstadoPedido.PENDIENTE


def construir_sesion_checkout_wompi(
    pedido_id: uuid.UUID,
    referencia: str,
    monto_total_cop: Decimal,
    url_redireccion: str = "http://localhost:8000/?pago=completado",
) -> Dict[str, Any]:
    """
    Construye los parámetros firmados para inicializar el Widget o redirección a Wompi.
    Los parámetros query de la URL ('public-key', 'amount-in-cents', 'signature:integrity')
    se conservan en inglés por protocolo externo de Wompi; las claves internas van en español.
    """
    monto_en_centavos = int((monto_total_cop * Decimal("100")).quantize(Decimal("1")))
    moneda = "COP"
    firma_integridad = calcular_firma_integridad_wompi(
        referencia=referencia,
        monto_en_centavos=monto_en_centavos,
        moneda=moneda,
    )

    parametros_query_wompi = urlencode(
        {
            "public-key": configuracion.WOMPI_LLAVE_PUBLICA,
            "currency": moneda,
            "amount-in-cents": str(monto_en_centavos),
            "reference": referencia,
            "signature:integrity": firma_integridad,
            "redirect-url": url_redireccion,
        }
    )

    return {
        "pedido_id": pedido_id,
        "referencia": referencia,
        "monto_en_centavos": monto_en_centavos,
        "moneda": moneda,
        "llave_publica": configuracion.WOMPI_LLAVE_PUBLICA,
        "firma_integridad": firma_integridad,
        "url_checkout_wompi": f"{configuracion.WOMPI_URL_CHECKOUT}?{parametros_query_wompi}",
    }


async def consultar_transaccion_wompi(transaccion_id: str) -> Optional[Dict[str, Any]]:
    """Consulta directamente el estado de una transacción en la API REST de Wompi."""
    url = f"{configuracion.WOMPI_URL_API}/transactions/{transaccion_id}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as cliente:
            respuesta = await cliente.get(
                url,
                headers={"Authorization": f"Bearer {configuracion.WOMPI_LLAVE_PUBLICA}"},
            )
            if respuesta.status_code == 200:
                return respuesta.json().get("data")
    except httpx.HTTPError:
        return None
    return None
