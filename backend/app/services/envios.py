from decimal import Decimal
from typing import Any, Dict, Set

import httpx

from app.core.configuracion import configuracion
from app.models.entidades import MunicipioTolima

MUNICIPIOS_CORDILLERA_SUR: Set[MunicipioTolima] = {
    MunicipioTolima.PLANADAS,
    MunicipioTolima.HERRERA,
    MunicipioTolima.ATACO,
    MunicipioTolima.RONCESVALLES,
    MunicipioTolima.SANTA_ISABEL,
    MunicipioTolima.ANZOATEGUI,
}

CIUDADES_PRINCIPALES_COLOMBIA: Set[str] = {
    "bogota",
    "bogotá",
    "medellin",
    "medellín",
    "cali",
    "pereira",
    "armenia",
    "manizales",
    "bucaramanga",
    "barranquilla",
    "cartagena",
}


async def cotizar_envio_nacional(
    municipio_origen: MunicipioTolima,
    ciudad_destino: str,
    departamento_destino: str,
    peso_total_kg: Decimal,
) -> Dict[str, Any]:
    """
    Calcula la tarifa de flete nacional consultando Skydropx / Coordinadora API (contrato externo en inglés)
    y retorna un diccionario con claves internas en español.
    """
    peso_facturable_kg = max(
        Decimal("0.50"), (peso_total_kg * Decimal("1.10")).quantize(Decimal("0.01"))
    )

    # 1. Consultar API externa de Skydropx si está configurada con llave real
    if (
        configuracion.SKYDROPX_API_KEY
        and configuracion.SKYDROPX_API_KEY != "skydropx_test_key_maicofi"
    ):
        try:
            async with httpx.AsyncClient(timeout=8.0) as cliente:
                respuesta = await cliente.post(
                    f"{configuracion.SKYDROPX_URL_API}/quotations",
                    headers={
                        "Authorization": f"Token token={configuracion.SKYDROPX_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "address_from": {
                            "province": "Tolima",
                            "city": municipio_origen.value,
                            "country": "CO",
                        },
                        "address_to": {
                            "province": departamento_destino,
                            "city": ciudad_destino,
                            "country": "CO",
                        },
                        "parcels": [
                            {
                                "weight": float(peso_facturable_kg),
                                "distance_unit": "CM",
                                "mass_unit": "KG",
                                "height": 20,
                                "width": 20,
                                "length": 25,
                            }
                        ],
                    },
                )
                if respuesta.status_code in (200, 201):
                    cotizaciones = respuesta.json()
                    if isinstance(cotizaciones, list) and len(cotizaciones) > 0:
                        mejor = cotizaciones[0]
                        return {
                            "transportadora": mejor.get("provider", "Coordinadora Mercantil"),
                            "nivel_servicio": mejor.get(
                                "service_level_name", "Terrestre Especial Café"
                            ),
                            "municipio_origen": municipio_origen.value,
                            "ciudad_destino": ciudad_destino,
                            "peso_facturable_kg": peso_facturable_kg,
                            "costo_flete_cop": Decimal(
                                str(mejor.get("total_pricing", "14500"))
                            ),
                            "dias_habiles_estimados": int(mejor.get("days", 3)),
                        }
        except httpx.HTTPError:
            pass

    # 2. Matriz tarifaria logística del Tolima
    destino_normalizado = ciudad_destino.strip().lower()
    depto_normalizado = departamento_destino.strip().lower()

    es_destino_tolima = depto_normalizado == "tolima" or destino_normalizado in {
        "ibague",
        "ibagué",
        "libano",
        "líbano",
        "espinal",
        "honda",
        "chaparral",
        "melgar",
    }
    es_ciudad_principal = destino_normalizado in CIUDADES_PRINCIPALES_COLOMBIA

    if es_destino_tolima:
        tarifa_base_cop = Decimal("9500")
        tarifa_por_kg_adicional = Decimal("1800")
        dias_estimados = 2
    elif es_ciudad_principal:
        tarifa_base_cop = Decimal("14500")
        tarifa_por_kg_adicional = Decimal("2600")
        dias_estimados = 3
    else:
        tarifa_base_cop = Decimal("18500")
        tarifa_por_kg_adicional = Decimal("3400")
        dias_estimados = 4

    recargo_origen_cop = (
        Decimal("3500")
        if municipio_origen in MUNICIPIOS_CORDILLERA_SUR
        else Decimal("0")
    )
    if municipio_origen in MUNICIPIOS_CORDILLERA_SUR:
        dias_estimados += 1

    kilos_adicionales = max(Decimal("0"), peso_facturable_kg - Decimal("1.00"))

    if peso_facturable_kg >= Decimal("12.50"):
        tarifa_por_kg_adicional = (tarifa_por_kg_adicional * Decimal("0.65")).quantize(
            Decimal("1")
        )

    costo_total_flete = (
        tarifa_base_cop
        + recargo_origen_cop
        + (kilos_adicionales * tarifa_por_kg_adicional)
    ).quantize(Decimal("100"))

    transportadora = (
        "CoordinadoraCarga Mayorista"
        if peso_facturable_kg >= Decimal("25.00")
        else "Coordinadora / Interrapidisimo"
    )

    return {
        "transportadora": transportadora,
        "nivel_servicio": (
            "Carga Cafetera Asegurada"
            if peso_facturable_kg >= Decimal("12.50")
            else "Paquetería Café Fresco"
        ),
        "municipio_origen": municipio_origen.value,
        "ciudad_destino": ciudad_destino,
        "peso_facturable_kg": peso_facturable_kg,
        "costo_flete_cop": costo_total_flete,
        "dias_habiles_estimados": dias_estimados,
    }
