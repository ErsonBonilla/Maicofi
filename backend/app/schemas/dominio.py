from datetime import date, datetime
from decimal import Decimal
import re
from typing import List, Optional
from urllib.parse import urlparse
import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.models.entidades import (
    EstadoDianFactura,
    EstadoGrano,
    EstadoPedido,
    EstadoSuscripcion,
    FrecuenciaSuscripcion,
    MunicipioTolima,
    NivelTueste,
    ProcesoBeneficio,
    RegimenTributario,
    RolUsuario,
    TipoDocumentoFiscal,
    TipoMolienda,
    TipoPersonaFiscal,
    UnidadVenta,
    VariedadCafe,
)

FACTORES_PRIMO_DIAN = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71]


def calcular_digito_verificacion_nit_dian(numero_nit: str) -> str:
    """Calcula el Dígito de Verificación (DV) oficial de la DIAN mediante el algoritmo Módulo 11."""
    solo_digitos = "".join(c for c in numero_nit if c.isdigit())
    if not solo_digitos:
        return "0"
    acumulado = 0
    for indice, caracter in enumerate(reversed(solo_digitos)):
        if indice < len(FACTORES_PRIMO_DIAN):
            acumulado += int(caracter) * FACTORES_PRIMO_DIAN[indice]
    residuo = acumulado % 11
    return str(11 - residuo) if residuo > 1 else str(residuo)

PATRON_ETIQUETAS_PELIGROSAS = re.compile(r"[<>]|javascript:|data:|vbscript:", re.IGNORECASE)


def sanitizar_texto_seguro(valor: str) -> str:
    """Elimina caracteres de control, espacios extremos y patrones de inyección HTML/JS."""
    limpio = valor.strip()
    if PATRON_ETIQUETAS_PELIGROSAS.search(limpio):
        raise ValueError("El texto contiene caracteres o secuencias no permitidas por seguridad.")
    return limpio


def validar_url_segura_individual(url: str) -> str:
    url_limpia = url.strip()
    if len(url_limpia) > 500:
        raise ValueError("La dirección URL excede la longitud máxima permitida.")
    analizada = urlparse(url_limpia)
    es_https = analizada.scheme == "https" and bool(analizada.netloc)
    es_local = analizada.scheme == "http" and analizada.hostname in {"localhost", "127.0.0.1"}
    if not (es_https or es_local):
        raise ValueError("Las URLs de fotografías deben utilizar el protocolo seguro https://.")
    return url_limpia


def validar_lista_urls_seguras(urls: List[str]) -> List[str]:
    """Valida que las URLs de fotografías usen exclusivamente HTTPS (o localhost en desarrollo)."""
    if len(urls) > 5:
        raise ValueError("Solo se permiten máximo 5 fotografías por registro.")
    return [validar_url_segura_individual(u) for u in urls if u.strip()]


class EsquemaBaseMaicofi(BaseModel):
    """Configuración base: permite poblar por nombre en español o por alias del contrato externo en inglés."""

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )


# ==========================================
# ESQUEMAS DE AUTENTICACIÓN (/auth)
# ==========================================
class RegistroUsuarioEsquema(EsquemaBaseMaicofi):
    nombre_completo: str = Field(
        ...,
        alias="full_name",
        min_length=3,
        max_length=120,
        examples=["Don Albeiro Lozano"],
    )
    telefono: str = Field(
        ...,
        alias="phone",
        pattern=r"^\+?[0-9]{10,15}$",
        examples=["+573104528910"],
    )
    correo: Optional[EmailStr] = Field(default=None, alias="email")
    contrasena: str = Field(..., alias="password", min_length=8, max_length=128)
    rol: RolUsuario = Field(default=RolUsuario.CAFICULTOR, alias="role")

    @field_validator("nombre_completo")
    @classmethod
    def validar_nombre_completo(cls, valor: str) -> str:
        return sanitizar_texto_seguro(valor)

    @field_validator("rol")
    @classmethod
    def impedir_escalacion_administrador(cls, valor: RolUsuario) -> RolUsuario:
        if valor == RolUsuario.ADMINISTRADOR:
            raise ValueError(
                "No está permitido autoasignarse el rol de administrador en el registro público."
            )
        return valor

    @field_validator("contrasena")
    @classmethod
    def validar_fortaleza_contrasena(cls, valor: str) -> str:
        tiene_letra = any(c.isalpha() for c in valor)
        tiene_numero = any(c.isdigit() for c in valor)
        if not (tiene_letra and tiene_numero):
            raise ValueError("La contraseña debe incluir al menos una letra y un número.")
        return valor


class CredencialesAccesoEsquema(EsquemaBaseMaicofi):
    identificador: str = Field(
        ...,
        alias="identifier",
        min_length=3,
        max_length=150,
        description="Número de celular (+57...) o correo electrónico del usuario.",
    )
    contrasena: str = Field(..., alias="password", min_length=6, max_length=128)


class SolicitudAccesoDemoEsquema(EsquemaBaseMaicofi):
    rol: RolUsuario = Field(default=RolUsuario.CAFICULTOR, alias="role")


class RespuestaTokenEsquema(EsquemaBaseMaicofi):
    token_acceso: str = Field(..., alias="access_token")
    tipo_token: str = Field(default="bearer", alias="token_type")
    rol: RolUsuario = Field(..., alias="role")
    usuario_id: uuid.UUID = Field(..., alias="user_id")
    nombre_completo: str = Field(..., alias="full_name")


# ==========================================
# ESQUEMAS DE PERFIL SENSORIAL
# ==========================================
class PerfilSensorialEsquema(EsquemaBaseMaicofi):
    acidez: int = Field(default=4, alias="acidity", ge=1, le=5)
    cuerpo: int = Field(default=4, alias="body", ge=1, le=5)
    dulzura: int = Field(default=5, alias="sweetness", ge=1, le=5)
    nivel_tueste: NivelTueste = Field(default=NivelTueste.MEDIO, alias="roast_level")
    notas_principales: List[str] = Field(
        default_factory=list, alias="main_notes", max_length=10
    )


# ==========================================
# ESQUEMAS DE FINCAS Y TRAZABILIDAD (/producers y /farmers)
# ==========================================
class CrearFincaEsquema(EsquemaBaseMaicofi):
    nombre_finca: str = Field(
        ...,
        alias="farm_name",
        min_length=2,
        max_length=150,
        examples=["Finca El Mirador del Nevado"],
    )
    municipio: MunicipioTolima = Field(..., alias="municipality")
    vereda: str = Field(
        ...,
        alias="vereda",
        min_length=2,
        max_length=120,
        examples=["Vereda Gaitania"],
    )
    altura_msnm: int = Field(
        ...,
        alias="altitude_masl",
        ge=800,
        le=2600,
        description="Altura sobre el nivel del mar (m.s.n.m.) en el Tolima",
    )
    historia_productor: str = Field(
        ...,
        alias="farmer_story",
        min_length=20,
        max_length=2000,
    )
    foto_productor_url: Optional[str] = Field(default=None, alias="farmer_photo_url")
    latitud: Optional[Decimal] = Field(default=None, alias="latitude")
    longitud: Optional[Decimal] = Field(default=None, alias="longitude")
    urls_fotos: List[str] = Field(default_factory=list, alias="photos_urls")

    @field_validator("nombre_finca", "vereda", "historia_productor")
    @classmethod
    def sanitizar_campos_finca(cls, valor: str) -> str:
        return sanitizar_texto_seguro(valor)

    @field_validator("foto_productor_url")
    @classmethod
    def validar_foto_productor(cls, valor: Optional[str]) -> Optional[str]:
        if not valor:
            return None
        return validar_url_segura_individual(valor)

    @field_validator("urls_fotos")
    @classmethod
    def validar_fotos_finca(cls, urls: List[str]) -> List[str]:
        return validar_lista_urls_seguras(urls)


class LeerFincaEsquema(CrearFincaEsquema):
    id: uuid.UUID
    usuario_id: uuid.UUID = Field(..., alias="user_id")
    nombre_propietario: Optional[str] = Field(default=None, alias="owner_name")
    creado_en: datetime = Field(..., alias="created_at")


# ==========================================
# ESQUEMAS DE LOTES DE CAFÉ DE ESPECIALIDAD (/products)
# ==========================================
class CrearLoteCafeEsquema(EsquemaBaseMaicofi):
    slug: Optional[str] = Field(default=None, alias="slug", max_length=180)
    nombre: str = Field(
        ...,
        alias="name",
        min_length=3,
        max_length=150,
        examples=["Microlote Tabi Lavado - Cosecha Mitaca"],
    )
    variedad: VariedadCafe = Field(..., alias="variety")
    proceso: ProcesoBeneficio = Field(..., alias="process")
    estado_presentacion: EstadoGrano = Field(
        default=EstadoGrano.TOSTADO_GRANO, alias="presentation_state"
    )
    puntaje_sca: Decimal = Field(
        ...,
        alias="sca_score",
        ge=Decimal("80.0"),
        le=Decimal("100.0"),
        examples=[Decimal("86.50")],
    )
    notas_cata: List[str] = Field(
        ...,
        alias="tasting_notes",
        min_length=1,
        max_length=10,
        examples=[["Panela", "Mora", "Cítrico Naranja"]],
    )
    humedad_porcentaje: Optional[Decimal] = Field(
        default=Decimal("11.0"),
        alias="humidity_pct",
        ge=Decimal("9.0"),
        le=Decimal("13.5"),
    )
    anio_cosecha: int = Field(default=2026, alias="harvest_year", ge=2024, le=2030)
    fecha_tueste: Optional[date] = Field(default=None, alias="roast_date")
    valvula_desgasificadora: bool = Field(default=True, alias="degassing_valve")

    precio_libra_cop: Decimal = Field(
        ..., alias="price_per_lb_cop", gt=0, le=Decimal("500000")
    )
    precio_arroba_cop: Optional[Decimal] = Field(
        default=None, alias="price_per_arroba_cop", gt=0, le=Decimal("12500000")
    )
    precio_carga_cop: Optional[Decimal] = Field(
        default=None, alias="price_per_carga_cop", gt=0, le=Decimal("125000000")
    )
    stock_disponible_kg: Decimal = Field(
        ..., alias="available_stock_kg", gt=0, le=Decimal("50000")
    )
    urls_fotos: List[str] = Field(default_factory=list, alias="photos_urls")
    perfil_sensorial: Optional[PerfilSensorialEsquema] = Field(
        default=None, alias="sensory_profile"
    )

    @field_validator("nombre")
    @classmethod
    def validar_nombre_lote(cls, valor: str) -> str:
        return sanitizar_texto_seguro(valor)

    @field_validator("notas_cata")
    @classmethod
    def validar_notas_sensoriales(cls, notas: List[str]) -> List[str]:
        if len(notas) > 10:
            raise ValueError("Se permiten máximo 10 notas de cata por lote.")
        limpias: List[str] = []
        for nota in notas:
            nota_limpia = sanitizar_texto_seguro(nota)
            if not (2 <= len(nota_limpia) <= 40):
                raise ValueError("Cada nota de cata debe tener entre 2 y 40 caracteres.")
            limpias.append(nota_limpia)
        return limpias

    @field_validator("urls_fotos")
    @classmethod
    def validar_fotos_lote(cls, urls: List[str]) -> List[str]:
        return validar_lista_urls_seguras(urls)


class ResumenLoteProductorEsquema(EsquemaBaseMaicofi):
    id: uuid.UUID
    slug: str
    nombre: str = Field(..., alias="name")
    variedad: VariedadCafe = Field(..., alias="variety")
    proceso: ProcesoBeneficio = Field(..., alias="process")
    puntaje_sca: Decimal = Field(..., alias="sca_score")
    precio_libra_cop: Decimal = Field(..., alias="price_per_lb_cop")
    notas_cata: List[str] = Field(..., alias="tasting_notes")


class LeerLoteCafeEsquema(CrearLoteCafeEsquema):
    id: uuid.UUID
    slug: str
    finca_id: uuid.UUID = Field(..., alias="farm_id")
    finca_nombre: Optional[str] = Field(default=None, alias="farm_name")
    municipio: Optional[MunicipioTolima] = Field(default=None, alias="municipality")
    altura_msnm: Optional[int] = Field(default=None, alias="altitude_masl")
    activo: bool = Field(..., alias="is_active")
    creado_en: datetime = Field(..., alias="created_at")
    finca: LeerFincaEsquema = Field(..., alias="farm")


class HistoriaCaficultorEsquema(EsquemaBaseMaicofi):
    """Respuesta del endpoint /farmers/{id}/story para Storytelling y Trazabilidad."""
    finca_id: uuid.UUID = Field(..., alias="farm_id")
    nombre_finca: str = Field(..., alias="farm_name")
    nombre_productor: Optional[str] = Field(default=None, alias="farmer_name")
    foto_productor_url: Optional[str] = Field(default=None, alias="farmer_photo_url")
    municipio: MunicipioTolima = Field(..., alias="municipality")
    vereda: str = Field(..., alias="vereda")
    altura_msnm: int = Field(..., alias="altitude_masl")
    latitud: Optional[Decimal] = Field(default=None, alias="latitude")
    longitud: Optional[Decimal] = Field(default=None, alias="longitude")
    historia_productor: str = Field(..., alias="farmer_story")
    urls_fotos_finca: List[str] = Field(default_factory=list, alias="farm_photos_urls")
    otros_lotes: List[ResumenLoteProductorEsquema] = Field(
        default_factory=list, alias="other_lots"
    )


# ==========================================
# ESQUEMAS DE SUSCRIPCIONES RECURRENTES (/subscriptions)
# ==========================================
class LeerPlanSuscripcionEsquema(EsquemaBaseMaicofi):
    id: uuid.UUID
    codigo: str = Field(..., alias="code")
    nombre: str = Field(..., alias="name")
    descripcion: str = Field(..., alias="description")
    frecuencia: FrecuenciaSuscripcion = Field(..., alias="frequency")
    porcentaje_descuento: Decimal = Field(..., alias="discount_pct")


class CrearSuscripcionUsuarioEsquema(EsquemaBaseMaicofi):
    lote_cafe_id: uuid.UUID = Field(..., alias="coffee_lot_id")
    frecuencia: FrecuenciaSuscripcion = Field(..., alias="frequency")
    presentacion_peso: UnidadVenta = Field(
        default=UnidadVenta.GRAMOS_500, alias="weight_presentation"
    )
    tipo_molienda: TipoMolienda = Field(
        default=TipoMolienda.GRANO_ENTERO, alias="grind_type"
    )
    cantidad: int = Field(default=1, alias="quantity", gt=0, le=50)
    direccion_envio: str = Field(
        ..., alias="shipping_address", min_length=5, max_length=250
    )
    ciudad_envio: str = Field(
        default="Ibagué", alias="shipping_city", min_length=2, max_length=100
    )

    @field_validator("direccion_envio", "ciudad_envio")
    @classmethod
    def sanitizar_envio_suscripcion(cls, valor: str) -> str:
        return sanitizar_texto_seguro(valor)


class LeerSuscripcionUsuarioEsquema(EsquemaBaseMaicofi):
    id: uuid.UUID
    comprador_id: uuid.UUID = Field(..., alias="buyer_id")
    lote_cafe_id: uuid.UUID = Field(..., alias="coffee_lot_id")
    plan_id: uuid.UUID = Field(..., alias="plan_id")
    frecuencia: FrecuenciaSuscripcion = Field(..., alias="frequency")
    presentacion_peso: UnidadVenta = Field(..., alias="weight_presentation")
    tipo_molienda: TipoMolienda = Field(..., alias="grind_type")
    cantidad: int = Field(..., alias="quantity")
    precio_periodo_cop: Decimal = Field(..., alias="period_price_cop")
    porcentaje_descuento_aplicado: Decimal = Field(..., alias="applied_discount_pct")
    proxima_entrega: date = Field(..., alias="next_delivery_date")
    direccion_envio: str = Field(..., alias="shipping_address")
    ciudad_envio: str = Field(..., alias="shipping_city")
    estado: EstadoSuscripcion = Field(..., alias="status")
    creado_en: datetime = Field(..., alias="created_at")


# ==========================================
# ESQUEMAS DE FACTURACIÓN ELECTRÓNICA DIAN E INFORMACIÓN FISCAL
# ==========================================
class DatosFiscalesClienteEsquema(EsquemaBaseMaicofi):
    tipo_documento: TipoDocumentoFiscal = Field(
        default=TipoDocumentoFiscal.CC, alias="document_type"
    )
    numero_documento: str = Field(
        ...,
        alias="document_number",
        min_length=5,
        max_length=20,
        pattern=r"^[0-9A-Za-z\-]{5,20}$",
    )
    digito_verificacion: Optional[str] = Field(
        default=None, alias="verification_digit", max_length=2
    )
    razon_social_o_nombre: str = Field(
        ..., alias="tax_name", min_length=3, max_length=180
    )
    correo_facturacion: EmailStr = Field(..., alias="billing_email")
    tipo_persona: TipoPersonaFiscal = Field(
        default=TipoPersonaFiscal.NATURAL, alias="person_type"
    )
    regimen_tributario: RegimenTributario = Field(
        default=RegimenTributario.NO_RESPONSABLE_IVA, alias="tax_regime"
    )
    direccion_fiscal: str = Field(
        ..., alias="tax_address", min_length=5, max_length=250
    )
    codigo_municipio_dane: str = Field(
        default="73001",
        alias="municipality_code",
        pattern=r"^[0-9]{5}$",
        description="Código DANE de 5 dígitos del municipio (ej. 73001 Ibagué, 73555 Planadas, 73411 Líbano)",
    )

    @field_validator("razon_social_o_nombre", "direccion_fiscal")
    @classmethod
    def sanitizar_textos_fiscales(cls, valor: str) -> str:
        return sanitizar_texto_seguro(valor)

    @model_validator(mode="after")
    def validar_y_completar_dv_nit(self) -> "DatosFiscalesClienteEsquema":
        if self.tipo_documento == TipoDocumentoFiscal.NIT:
            dv_calculado = calcular_digito_verificacion_nit_dian(self.numero_documento)
            if not self.digito_verificacion:
                self.digito_verificacion = dv_calculado
        return self


class LeerDatosFiscalesClienteEsquema(DatosFiscalesClienteEsquema):
    id: uuid.UUID
    pedido_id: uuid.UUID = Field(..., alias="order_id")
    creado_en: datetime = Field(..., alias="created_at")


class LeerFacturaElectronicaEsquema(EsquemaBaseMaicofi):
    id: uuid.UUID
    pedido_id: uuid.UUID = Field(..., alias="order_id")
    numero_factura: str = Field(..., alias="invoice_number")
    cufe: Optional[str] = Field(default=None, alias="cufe")
    url_codigo_qr: Optional[str] = Field(default=None, alias="qr_code_url")
    url_pdf: Optional[str] = Field(default=None, alias="pdf_url")
    url_xml: Optional[str] = Field(default=None, alias="xml_url")
    estado_dian: EstadoDianFactura = Field(..., alias="dian_status")
    mensaje_error_dian: Optional[str] = Field(default=None, alias="dian_error_message")
    creado_en: datetime = Field(..., alias="created_at")


# ==========================================
# ESQUEMAS DE PEDIDOS (/orders)
# ==========================================
class CrearDetallePedidoEsquema(EsquemaBaseMaicofi):
    lote_cafe_id: uuid.UUID = Field(..., alias="coffee_lot_id")
    unidad_venta: UnidadVenta = Field(..., alias="unit_type")
    tipo_molienda: TipoMolienda = Field(
        default=TipoMolienda.GRANO_ENTERO, alias="grind_type"
    )
    cantidad: int = Field(..., alias="quantity", gt=0, le=500)


class CrearPedidoEsquema(EsquemaBaseMaicofi):
    direccion_envio: str = Field(
        ..., alias="shipping_address", min_length=5, max_length=250
    )
    ciudad_envio: str = Field(..., alias="shipping_city", min_length=2, max_length=100)
    departamento_envio: str = Field(
        default="Tolima", alias="shipping_department", min_length=2, max_length=100
    )
    telefono_contacto: str = Field(
        ..., alias="contact_phone", pattern=r"^\+?[0-9]{7,15}$"
    )
    notas: Optional[str] = Field(default=None, alias="notes", max_length=500)
    datos_fiscales: Optional[DatosFiscalesClienteEsquema] = Field(
        default=None, alias="tax_data"
    )
    detalles: List[CrearDetallePedidoEsquema] = Field(
        ..., alias="items", min_length=1, max_length=25
    )

    @field_validator("direccion_envio", "ciudad_envio", "departamento_envio")
    @classmethod
    def validar_campos_envio(cls, valor: str) -> str:
        return sanitizar_texto_seguro(valor)

    @field_validator("notas")
    @classmethod
    def validar_notas_pedido(cls, valor: Optional[str]) -> Optional[str]:
        if valor is None:
            return None
        return sanitizar_texto_seguro(valor)


class LeerDetallePedidoEsquema(EsquemaBaseMaicofi):
    id: uuid.UUID
    lote_cafe_id: uuid.UUID = Field(..., alias="coffee_lot_id")
    unidad_venta: UnidadVenta = Field(..., alias="unit_type")
    tipo_molienda: TipoMolienda = Field(..., alias="grind_type")
    cantidad: int = Field(..., alias="quantity")
    equivalente_kg: Decimal = Field(..., alias="equivalent_kg")
    precio_unitario_cop: Decimal = Field(..., alias="unit_price_cop")
    subtotal_cop: Decimal = Field(..., alias="subtotal_cop")


class LeerPedidoEsquema(EsquemaBaseMaicofi):
    id: uuid.UUID
    comprador_id: uuid.UUID = Field(..., alias="buyer_id")
    estado: EstadoPedido = Field(..., alias="status")
    monto_total_cop: Decimal = Field(..., alias="total_amount_cop")
    costo_envio_cop: Decimal = Field(default=Decimal("0.00"), alias="shipping_cost_cop")
    referencia_pago: Optional[str] = Field(default=None, alias="payment_reference")
    transaccion_pasarela_id: Optional[str] = Field(
        default=None, alias="gateway_transaction_id"
    )
    metodo_pago: Optional[str] = Field(default=None, alias="payment_method")
    direccion_envio: str = Field(..., alias="shipping_address")
    ciudad_envio: str = Field(..., alias="shipping_city")
    departamento_envio: str = Field(..., alias="shipping_department")
    telefono_contacto: str = Field(..., alias="contact_phone")
    notas: Optional[str] = Field(default=None, alias="notes")
    creado_en: datetime = Field(..., alias="created_at")
    detalles: List[LeerDetallePedidoEsquema] = Field(..., alias="items")
    datos_fiscales: Optional[LeerDatosFiscalesClienteEsquema] = Field(
        default=None, alias="tax_data"
    )
    factura_electronica: Optional[LeerFacturaElectronicaEsquema] = Field(
        default=None, alias="electronic_invoice"
    )


# ==========================================
# ESQUEMAS DE MICROSERVICIOS (PAGOS, ENVÍOS, CLOUDINARY)
# ==========================================
class SolicitudSesionPagoWompiEsquema(EsquemaBaseMaicofi):
    pedido_id: uuid.UUID = Field(..., alias="order_id")
    url_redireccion: Optional[str] = Field(
        default="http://localhost:8000/?pago=completado", alias="redirect_url"
    )


class RespuestaSesionPagoWompiEsquema(EsquemaBaseMaicofi):
    pedido_id: uuid.UUID = Field(..., alias="order_id")
    referencia: str = Field(..., alias="reference")
    monto_en_centavos: int = Field(..., alias="amount_in_cents")
    moneda: str = Field(default="COP", alias="currency")
    llave_publica: str = Field(..., alias="public_key")
    firma_integridad: str = Field(..., alias="signature_integrity")
    url_checkout_wompi: str = Field(..., alias="checkout_url")
    costo_envio_cop: Decimal = Field(..., alias="shipping_cost_cop")
    monto_total_con_envio_cop: Decimal = Field(..., alias="total_with_shipping_cop")


class SolicitudCotizacionEnvioEsquema(EsquemaBaseMaicofi):
    municipio_origen: MunicipioTolima = Field(
        default=MunicipioTolima.PLANADAS, alias="origin_municipality"
    )
    ciudad_destino: str = Field(
        ..., alias="destination_city", min_length=2, max_length=100
    )
    departamento_destino: str = Field(
        default="Tolima", alias="destination_department", min_length=2, max_length=100
    )
    peso_total_kg: Decimal = Field(..., alias="total_weight_kg", gt=0, le=50000)


class RespuestaCotizacionEnvioEsquema(EsquemaBaseMaicofi):
    transportadora: str = Field(..., alias="carrier")
    nivel_servicio: str = Field(..., alias="service_level")
    municipio_origen: str = Field(..., alias="origin_municipality")
    ciudad_destino: str = Field(..., alias="destination_city")
    peso_facturable_kg: Decimal = Field(..., alias="billable_weight_kg")
    costo_flete_cop: Decimal = Field(..., alias="shipping_cost_cop")
    dias_habiles_estimados: int = Field(..., alias="estimated_business_days")


class RespuestaSubidaImagenEsquema(EsquemaBaseMaicofi):
    id_publico: str = Field(..., alias="public_id")
    url_original: str = Field(..., alias="original_url")
    url_webp_optimizada: str = Field(..., alias="optimized_webp_url")
    url_miniatura_tarjeta: str = Field(..., alias="card_thumbnail_url")
    formato: str = Field(default="webp", alias="format")
