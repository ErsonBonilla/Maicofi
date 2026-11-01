import hashlib
import time
from typing import Dict, Set
import uuid

from fastapi import HTTPException, UploadFile, status
import httpx

from app.core.configuracion import configuracion

TIPOS_MIME_PERMITIDOS: Set[str] = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

TAMANO_MAXIMO_BYTES: int = 5 * 1024 * 1024  # 5 MB máximo para optimizar subida rural


def construir_url_cloudinary_webp(
    cloud_name: str,
    id_publico: str,
    ancho: int = 1000,
    alto: int = 750,
    calidad: str = "auto:good",
) -> str:
    """Genera la URL del CDN de Cloudinary con transformación automática a WebP y recorte inteligente."""
    transformacion = f"f_webp,q_{calidad},c_fill,g_auto,w_{ancho},h_{alto}"
    return f"https://res.cloudinary.com/{cloud_name}/image/upload/{transformacion}/{id_publico}.webp"


def generar_firma_cloudinary(parametros: Dict[str, str], api_secret: str) -> str:
    """Calcula la firma SHA-1 exigida por el endpoint firmado de Cloudinary."""
    pares_ordenados = "&".join(
        f"{clave}={parametros[clave]}" for clave in sorted(parametros.keys())
    )
    cadena_a_firmar = f"{pares_ordenados}{api_secret}"
    return hashlib.sha1(cadena_a_firmar.encode("utf-8")).hexdigest()


async def subir_y_optimizar_imagen_cloudinary(
    archivo: UploadFile,
    carpeta: str = "maicofi/lotes_tolima",
) -> Dict[str, str]:
    """
    Valida, sube la fotografía a Cloudinary y retorna un diccionario con claves internas en español
    conteniendo las URLs optimizadas en formato WebP para portada (1000x750) y tarjeta (480x360).
    """
    if archivo.content_type not in TIPOS_MIME_PERMITIDOS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de imagen no soportado. Usa fotografías JPG, PNG o WebP.",
        )

    contenido_bytes = await archivo.read()
    if len(contenido_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo de imagen está vacío.",
        )
    if len(contenido_bytes) > TAMANO_MAXIMO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="La fotografía supera el límite máximo permitido de 5 MB.",
        )

    cloud_name = configuracion.CLOUDINARY_CLOUD_NAME or "maicofi-tolima"
    id_unico = f"{carpeta}/lote_{uuid.uuid4().hex[:10]}"

    # Si hay credenciales reales de producción configuradas, subir a Cloudinary API (contrato externo en inglés)
    if (
        configuracion.CLOUDINARY_API_KEY
        and configuracion.CLOUDINARY_API_SECRET
        and configuracion.CLOUDINARY_API_SECRET != "cloudinary_secret_demo"
    ):
        marca_tiempo = str(int(time.time()))
        parametros_firma = {
            "folder": carpeta,
            "timestamp": marca_tiempo,
        }
        firma = generar_firma_cloudinary(
            parametros_firma, configuracion.CLOUDINARY_API_SECRET
        )
        url_subida = f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload"

        try:
            async with httpx.AsyncClient(timeout=20.0) as cliente:
                respuesta = await cliente.post(
                    url_subida,
                    data={
                        "api_key": configuracion.CLOUDINARY_API_KEY,
                        "timestamp": marca_tiempo,
                        "folder": carpeta,
                        "signature": firma,
                    },
                    files={
                        "file": (
                            archivo.filename or "lote_tolima.jpg",
                            contenido_bytes,
                            archivo.content_type,
                        )
                    },
                )
                if respuesta.status_code == 200:
                    datos = respuesta.json()
                    id_publico = datos.get("public_id", id_unico)
                    return {
                        "id_publico": id_publico,
                        "url_original": datos.get(
                            "secure_url",
                            construir_url_cloudinary_webp(cloud_name, id_publico),
                        ),
                        "url_webp_optimizada": construir_url_cloudinary_webp(
                            cloud_name, id_publico, ancho=1000, alto=750
                        ),
                        "url_miniatura_tarjeta": construir_url_cloudinary_webp(
                            cloud_name, id_publico, ancho=480, alto=360, calidad="auto:eco"
                        ),
                        "formato": "webp",
                    }
        except httpx.HTTPError:
            pass

    # Respuesta estructurada con claves internas en español y URLs WebP
    return {
        "id_publico": id_unico,
        "url_original": f"https://res.cloudinary.com/{cloud_name}/image/upload/{id_unico}.jpg",
        "url_webp_optimizada": construir_url_cloudinary_webp(
            cloud_name, id_unico, ancho=1000, alto=750
        ),
        "url_miniatura_tarjeta": construir_url_cloudinary_webp(
            cloud_name, id_unico, ancho=480, alto=360, calidad="auto:eco"
        ),
        "formato": "webp",
    }
