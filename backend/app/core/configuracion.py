import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv

RUTA_ARCHIVO_ENV = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(dotenv_path=RUTA_ARCHIVO_ENV, override=False)


class ConfiguracionAplicacion:
    """Configuración interna de la plataforma Maicofi cargada desde el archivo .env."""

    ENTORNO: str = os.getenv("ENVIRONMENT", "development").lower()
    ES_PRODUCCION: bool = ENTORNO == "production"

    NOMBRE_PROYECTO: str = os.getenv(
        "PROJECT_NAME", "Maicofi API - Café Especial del Tolima"
    )
    VERSION: str = os.getenv("PROJECT_VERSION", "1.0.0")
    PREFIJO_API: str = os.getenv("API_V1_PREFIX", "/api/v1")
    PUERTO_BACKEND: int = int(os.getenv("BACKEND_PORT", "8001"))

    USUARIO_POSTGRES: str = os.getenv("POSTGRES_USER", "maicofi_usuario")
    CLAVE_POSTGRES: str = os.getenv("POSTGRES_PASSWORD", "maicofi_clave_segura")
    NOMBRE_BD_POSTGRES: str = os.getenv("POSTGRES_DB", "maicofi_tolima_bd")
    HOST_POSTGRES: str = os.getenv("POSTGRES_HOST", "127.0.0.1")
    PUERTO_POSTGRES: str = os.getenv("POSTGRES_PORT", "5432")

    URL_BASE_DATOS: str = os.getenv(
        "DATABASE_URL",
        (
            f"postgresql+psycopg://{USUARIO_POSTGRES}:{CLAVE_POSTGRES}"
            f"@{HOST_POSTGRES}:{PUERTO_POSTGRES}/{NOMBRE_BD_POSTGRES}"
        ),
    )

    CLAVE_SECRETA_JWT: str = os.getenv(
        "JWT_SECRET_KEY",
        "clave_secreta_desarrollo_maicofi_tolima_2026_cambiar_en_produccion",
    )
    ALGORITMO_JWT: str = os.getenv("JWT_ALGORITHM", "HS256")
    EMISOR_JWT: str = os.getenv("JWT_ISSUER", "maicofi-tolima-api")
    MINUTOS_EXPIRACION_TOKEN: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24))
    )
    NOMBRE_COOKIE_SESION: str = "maicofi_access_token"

    MAX_INTENTOS_AUTH_POR_MINUTO: int = int(
        os.getenv("AUTH_RATE_LIMIT_PER_MINUTE", "10")
    )
    MAX_PETICIONES_ESCRITURA_POR_MINUTO: int = int(
        os.getenv("WRITE_RATE_LIMIT_PER_MINUTE", "30")
    )

    ORIGENES_CORS: List[str] = [
        origen.strip()
        for origen in os.getenv(
            "CORS_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000"
        ).split(",")
        if origen.strip()
    ]

    TELEFONO_CAFICULTOR_DEMO: str = os.getenv("DEMO_FARMER_PHONE", "+573104528910")
    TELEFONO_COMPRADOR_DEMO: str = os.getenv("DEMO_BUYER_PHONE", "+573001112233")
    CLAVE_USUARIO_DEMO: str = os.getenv("DEMO_USER_PASSWORD", "tolima2026")

    # Microservicio A: Pasarela de Pagos Wompi Colombia
    WOMPI_LLAVE_PUBLICA: str = os.getenv(
        "WOMPI_PUBLIC_KEY", "pub_test_MaicofiTolimaPublicKey2026"
    )
    WOMPI_LLAVE_PRIVADA: str = os.getenv(
        "WOMPI_PRIVATE_KEY", "prv_test_MaicofiTolimaPrivateKey2026"
    )
    WOMPI_SECRETO_INTEGRIDAD: str = os.getenv(
        "WOMPI_INTEGRITY_SECRET", "test_integrity_MaicofiSecret2026"
    )
    WOMPI_SECRETO_EVENTOS: str = os.getenv(
        "WOMPI_EVENTS_SECRET", "test_events_MaicofiWebhookSecret2026"
    )
    WOMPI_URL_API: str = os.getenv("WOMPI_API_URL", "https://sandbox.wompi.co/v1")
    WOMPI_URL_CHECKOUT: str = os.getenv(
        "WOMPI_CHECKOUT_URL", "https://checkout.wompi.co/p/"
    )

    # Microservicio B: WhatsApp (Twilio / Meta Cloud API) y Email (Resend)
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_WHATSAPP_REMITENTE: str = os.getenv(
        "TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886"
    )
    META_WHATSAPP_TOKEN: str = os.getenv("META_WHATSAPP_TOKEN", "")
    META_WHATSAPP_PHONE_ID: str = os.getenv("META_WHATSAPP_PHONE_ID", "")

    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")
    RESEND_CORREO_REMITENTE: str = os.getenv(
        "RESEND_FROM_EMAIL", "pedidos@maicofi.co"
    )

    # Microservicio C: Imágenes y CDN Cloudinary
    CLOUDINARY_URL: str = os.getenv("CLOUDINARY_URL", "")
    CLOUDINARY_CLOUD_NAME: str = os.getenv(
        "CLOUDINARY_CLOUD_NAME", "maicofi-tolima"
    )
    CLOUDINARY_API_KEY: str = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET: str = os.getenv("CLOUDINARY_API_SECRET", "")

    # Microservicio E: Logística Nacional Skydropx / Coordinadora
    SKYDROPX_API_KEY: str = os.getenv("SKYDROPX_API_KEY", "")
    SKYDROPX_URL_API: str = os.getenv(
        "SKYDROPX_API_URL", "https://api-demo.skydropx.com/v1"
    )

    # Microservicio F: Facturación Electrónica DIAN (Dataico / Alegra API)
    FACTURACION_API_KEY: str = os.getenv(
        "INVOICING_API_KEY", "dian_test_key_maicofi_2026"
    )
    FACTURACION_ENDPOINT: str = os.getenv(
        "INVOICING_ENDPOINT",
        "https://api.dataico.com/direct/dataico_api/v2/invoices",
    )
    NIT_EMPRESA_EMISORA: str = os.getenv("COMPANY_NIT", "901456789-3")
    RESOLUCION_DIAN: str = os.getenv("DIAN_RESOLUTION_NUMBER", "18760000001")
    PREFIJO_FACTURA_DIAN: str = os.getenv("DIAN_PREFIX", "SETT")
    MODO_PRUEBAS_DIAN: bool = (
        os.getenv("TEST_MODE_DIAN", "true").strip().lower() == "true"
    )

    def validar_seguridad_entorno(self) -> None:
        """Verifica que la clave JWT cumpla longitud mínima criptográfica en producción."""
        if self.ES_PRODUCCION and len(self.CLAVE_SECRETA_JWT) < 32:
            raise RuntimeError(
                "Error crítico de seguridad: JWT_SECRET_KEY debe tener al menos 32 caracteres en producción."
            )


configuracion = ConfiguracionAplicacion()
configuracion.validar_seguridad_entorno()
