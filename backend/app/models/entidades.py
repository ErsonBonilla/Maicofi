from datetime import date, datetime
from decimal import Decimal
import enum
from typing import List, Optional
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class BaseDeclarativa(DeclarativeBase):
    """Clase base para los modelos relacionales de PostgreSQL."""
    pass


class RolUsuario(str, enum.Enum):
    """Identificadores internos en español; valores del contrato JWT en inglés."""
    CAFICULTOR = "farmer"
    COMPRADOR = "buyer"
    ADMINISTRADOR = "admin"


class MunicipioTolima(str, enum.Enum):
    PLANADAS = "Planadas"
    LIBANO = "Líbano"
    SANTA_ISABEL = "Santa Isabel"
    ANZOATEGUI = "Anzoátegui"
    HERRERA = "Herrera (Rioblanco)"
    IBAGUE = "Ibagué"
    CHAPARRAL = "Chaparral"
    ATACO = "Ataco"
    FRESNO = "Fresno"
    RONCESVALLES = "Roncesvalles"
    ORTEGA = "Ortega"
    CAJAMARCA = "Cajamarca"


class VariedadCafe(str, enum.Enum):
    CASTILLO = "Castillo"
    CATURRA = "Caturra"
    TABI = "Tabi"
    COLOMBIA = "Colombia"
    GEISHA = "Geisha"
    BOURBON_ROSADO = "Bourbon Rosado"
    TIPICA = "Típica"
    CATUAI = "Catuaí"


class ProcesoBeneficio(str, enum.Enum):
    LAVADO = "Lavado"
    NATURAL = "Natural"
    HONEY = "Honey"
    ANAEROBICO = "Fermentación Anaeróbica"


class EstadoGrano(str, enum.Enum):
    PERGAMINO_SECO = "Café Pergamino Seco"
    VERDE_TRILLADO = "Excelso Verde Trillado"
    TOSTADO_GRANO = "Tostado en Grano"
    TOSTADO_MOLIDO = "Tostado Molido"


class NivelTueste(str, enum.Enum):
    CLARO = "Claro"
    MEDIO = "Medio"
    MEDIO_OSCURO = "Medio-Oscuro"
    OSCURO = "Oscuro"


class TipoMolienda(str, enum.Enum):
    GRANO_ENTERO = "Grano entero"
    MOKA_ITALIANA = "Moka / Italiana"
    FILTRO_GOTEO = "Filtro / Goteo (V60 / Chemex)"
    PRENSA_FRANCESA = "Prensa Francesa"
    ESPRESSO = "Espresso"


class UnidadVenta(str, enum.Enum):
    GRAMOS_250 = "250g"   # 0.25 kg
    LIBRA = "libra"       # 0.50 kg (500g)
    GRAMOS_500 = "500g"   # 0.50 kg (1 libra)
    GRAMOS_1000 = "1000g" # 1.00 kg (2 libras)
    ARROBA = "arroba"     # 12.50 kg (25 libras)
    CARGA = "carga"       # 125.00 kg (10 arrobas / 250 libras)


class FrecuenciaSuscripcion(str, enum.Enum):
    SEMANAL = "semanal"
    QUINCENAL = "quincenal"
    MENSUAL = "mensual"


class EstadoSuscripcion(str, enum.Enum):
    ACTIVA = "active"
    PAUSADA = "paused"
    CANCELADA = "cancelled"


class EstadoPedido(str, enum.Enum):
    PENDIENTE = "PENDING"
    COMPLETADO = "COMPLETED"
    RECHAZADO = "REJECTED"
    PAGADO = "PAID"
    EN_PREPARACION = "processing"
    ENVIADO = "shipped"
    ENTREGADO = "delivered"
    CANCELADO = "cancelled"


class TipoDocumentoFiscal(str, enum.Enum):
    CC = "CC"
    NIT = "NIT"
    CE = "CE"
    PASAPORTE = "PASAPORTE"


class TipoPersonaFiscal(str, enum.Enum):
    NATURAL = "Natural"
    JURIDICA = "Jurídica"


class RegimenTributario(str, enum.Enum):
    NO_RESPONSABLE_IVA = "No Responsable de IVA"
    RESPONSABLE_IVA = "Responsable de IVA"
    REGIMEN_SIMPLE = "Régimen Simple de Tributación (RST)"
    GRAN_CONTRIBUYENTE = "Gran Contribuyente"


class EstadoDianFactura(str, enum.Enum):
    PENDIENTE = "PENDING"
    APROBADA = "APPROVED"
    RECHAZADA = "REJECTED"


class Usuario(BaseDeclarativa):
    __tablename__ = "usuarios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre_completo: Mapped[str] = mapped_column(String(120), nullable=False)
    telefono: Mapped[str] = mapped_column(String(25), unique=True, index=True, nullable=False)
    correo: Mapped[Optional[str]] = mapped_column(String(150), unique=True, index=True, nullable=True)
    contrasena_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[RolUsuario] = mapped_column(
        Enum(RolUsuario, name="rol_usuario_enum"),
        default=RolUsuario.COMPRADOR,
        nullable=False,
    )
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    finca: Mapped[Optional["Finca"]] = relationship("Finca", back_populates="propietario", uselist=False)
    pedidos: Mapped[List["Pedido"]] = relationship("Pedido", back_populates="comprador")
    suscripciones: Mapped[List["SuscripcionUsuario"]] = relationship(
        "SuscripcionUsuario", back_populates="comprador"
    )


class Finca(BaseDeclarativa):
    __tablename__ = "fincas"
    __table_args__ = (
        CheckConstraint("altura_msnm BETWEEN 800 AND 2600", name="ck_finca_altura_tolima"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    nombre_finca: Mapped[str] = mapped_column(String(150), nullable=False)
    municipio: Mapped[MunicipioTolima] = mapped_column(
        Enum(MunicipioTolima, name="municipio_tolima_enum"), index=True, nullable=False
    )
    vereda: Mapped[str] = mapped_column(String(120), nullable=False)
    altura_msnm: Mapped[int] = mapped_column(Integer, nullable=False)
    historia_productor: Mapped[str] = mapped_column(Text, nullable=False)
    foto_productor_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    latitud: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6), nullable=True)
    longitud: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6), nullable=True)
    urls_fotos: Mapped[list] = mapped_column(JSONB, default=list)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    propietario: Mapped["Usuario"] = relationship("Usuario", back_populates="finca")
    lotes_cafe: Mapped[List["LoteCafe"]] = relationship(
        "LoteCafe", back_populates="finca", cascade="all, delete-orphan"
    )

    @property
    def nombre_propietario(self) -> Optional[str]:
        return self.propietario.nombre_completo if self.propietario else None


class LoteCafe(BaseDeclarativa):
    __tablename__ = "lotes_cafe"
    __table_args__ = (
        CheckConstraint("puntaje_sca BETWEEN 80.0 AND 100.0", name="ck_lote_puntaje_sca"),
        CheckConstraint("stock_disponible_kg >= 0", name="ck_lote_stock_no_negativo"),
        Index(
            "ix_lotes_catalogo_filtros",
            "variedad",
            "proceso",
            "puntaje_sca",
            "precio_libra_cop",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    finca_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fincas.id", ondelete="CASCADE"), index=True, nullable=False
    )
    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    variedad: Mapped[VariedadCafe] = mapped_column(
        Enum(VariedadCafe, name="variedad_cafe_enum"), index=True, nullable=False
    )
    proceso: Mapped[ProcesoBeneficio] = mapped_column(
        Enum(ProcesoBeneficio, name="proceso_beneficio_enum"), index=True, nullable=False
    )
    estado_presentacion: Mapped[EstadoGrano] = mapped_column(
        Enum(EstadoGrano, name="estado_grano_enum"),
        default=EstadoGrano.TOSTADO_GRANO,
        nullable=False,
    )
    puntaje_sca: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    notas_cata: Mapped[List[str]] = mapped_column(ARRAY(String(60)), default=list)
    humedad_porcentaje: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)
    anio_cosecha: Mapped[int] = mapped_column(Integer, default=2026)
    fecha_tueste: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    valvula_desgasificadora: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Precios por unidad cafetera en pesos colombianos (COP)
    precio_libra_cop: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    precio_arroba_cop: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    precio_carga_cop: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)

    stock_disponible_kg: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    urls_fotos: Mapped[list] = mapped_column(JSONB, default=list)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    finca: Mapped["Finca"] = relationship("Finca", back_populates="lotes_cafe")
    perfil_sensorial: Mapped[Optional["PerfilSensorial"]] = relationship(
        "PerfilSensorial",
        back_populates="lote_cafe",
        uselist=False,
        cascade="all, delete-orphan",
    )
    detalles_pedido: Mapped[List["DetallePedido"]] = relationship(
        "DetallePedido", back_populates="lote_cafe"
    )
    suscripciones: Mapped[List["SuscripcionUsuario"]] = relationship(
        "SuscripcionUsuario", back_populates="lote_cafe"
    )

    @property
    def finca_nombre(self) -> Optional[str]:
        return self.finca.nombre_finca if self.finca else None

    @property
    def municipio(self) -> Optional[MunicipioTolima]:
        return self.finca.municipio if self.finca else None

    @property
    def altura_msnm(self) -> Optional[int]:
        return self.finca.altura_msnm if self.finca else None


class PerfilSensorial(BaseDeclarativa):
    __tablename__ = "perfiles_sensoriales"
    __table_args__ = (
        CheckConstraint("acidez BETWEEN 1 AND 5", name="ck_sensorial_acidez"),
        CheckConstraint("cuerpo BETWEEN 1 AND 5", name="ck_sensorial_cuerpo"),
        CheckConstraint("dulzura BETWEEN 1 AND 5", name="ck_sensorial_dulzura"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lote_cafe_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("lotes_cafe.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    acidez: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    cuerpo: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    dulzura: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    nivel_tueste: Mapped[NivelTueste] = mapped_column(
        Enum(NivelTueste, name="nivel_tueste_enum"),
        default=NivelTueste.MEDIO,
        nullable=False,
    )
    notas_principales: Mapped[List[str]] = mapped_column(ARRAY(String(60)), default=list)

    lote_cafe: Mapped["LoteCafe"] = relationship("LoteCafe", back_populates="perfil_sensorial")


class PlanSuscripcion(BaseDeclarativa):
    """Modelo relacional para planes de suscripción recurrente (SubscriptionPlan)."""
    __tablename__ = "planes_suscripcion"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    descripcion: Mapped[str] = mapped_column(String(255), nullable=False)
    frecuencia: Mapped[FrecuenciaSuscripcion] = mapped_column(
        Enum(FrecuenciaSuscripcion, name="frecuencia_suscripcion_enum"), nullable=False
    )
    porcentaje_descuento: Mapped[Decimal] = mapped_column(
        Numeric(4, 2), default=Decimal("10.00"), nullable=False
    )
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    suscripciones: Mapped[List["SuscripcionUsuario"]] = relationship(
        "SuscripcionUsuario", back_populates="plan"
    )


class SuscripcionUsuario(BaseDeclarativa):
    """Modelo relacional para suscripciones activas de compradores (UserSubscription)."""
    __tablename__ = "suscripciones_usuarios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    comprador_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), index=True, nullable=False
    )
    lote_cafe_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("lotes_cafe.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("planes_suscripcion.id", ondelete="RESTRICT"), nullable=False
    )
    frecuencia: Mapped[FrecuenciaSuscripcion] = mapped_column(
        Enum(FrecuenciaSuscripcion, name="frecuencia_suscripcion_enum"), nullable=False
    )
    presentacion_peso: Mapped[UnidadVenta] = mapped_column(
        Enum(UnidadVenta, name="unidad_venta_enum"), nullable=False
    )
    tipo_molienda: Mapped[TipoMolienda] = mapped_column(
        Enum(TipoMolienda, name="tipo_molienda_enum"),
        default=TipoMolienda.GRANO_ENTERO,
        nullable=False,
    )
    cantidad: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    precio_periodo_cop: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    porcentaje_descuento_aplicado: Mapped[Decimal] = mapped_column(
        Numeric(4, 2), default=Decimal("10.00"), nullable=False
    )
    proxima_entrega: Mapped[date] = mapped_column(Date, nullable=False)
    direccion_envio: Mapped[str] = mapped_column(String(250), nullable=False)
    ciudad_envio: Mapped[str] = mapped_column(String(100), nullable=False)
    estado: Mapped[EstadoSuscripcion] = mapped_column(
        Enum(EstadoSuscripcion, name="estado_suscripcion_enum"),
        default=EstadoSuscripcion.ACTIVA,
        nullable=False,
    )
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    comprador: Mapped["Usuario"] = relationship("Usuario", back_populates="suscripciones")
    lote_cafe: Mapped["LoteCafe"] = relationship("LoteCafe", back_populates="suscripciones")
    plan: Mapped["PlanSuscripcion"] = relationship("PlanSuscripcion", back_populates="suscripciones")


class Pedido(BaseDeclarativa):
    __tablename__ = "pedidos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    comprador_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    estado: Mapped[EstadoPedido] = mapped_column(
        Enum(EstadoPedido, name="estado_pedido_enum"),
        default=EstadoPedido.PENDIENTE,
        nullable=False,
    )
    monto_total_cop: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    costo_envio_cop: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    referencia_pago: Mapped[Optional[str]] = mapped_column(
        String(120), unique=True, index=True, nullable=True
    )
    transaccion_pasarela_id: Mapped[Optional[str]] = mapped_column(
        String(120), unique=True, index=True, nullable=True
    )
    metodo_pago: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    direccion_envio: Mapped[str] = mapped_column(String(255), nullable=False)
    ciudad_envio: Mapped[str] = mapped_column(String(100), nullable=False)
    departamento_envio: Mapped[str] = mapped_column(String(100), default="Tolima")
    telefono_contacto: Mapped[str] = mapped_column(String(25), nullable=False)
    notas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    comprador: Mapped["Usuario"] = relationship("Usuario", back_populates="pedidos")
    detalles: Mapped[List["DetallePedido"]] = relationship(
        "DetallePedido", back_populates="pedido", cascade="all, delete-orphan"
    )
    datos_fiscales: Mapped[Optional["DatosFiscalesCliente"]] = relationship(
        "DatosFiscalesCliente",
        back_populates="pedido",
        uselist=False,
        cascade="all, delete-orphan",
    )
    factura_electronica: Mapped[Optional["FacturaElectronica"]] = relationship(
        "FacturaElectronica",
        back_populates="pedido",
        uselist=False,
        cascade="all, delete-orphan",
    )


class DetallePedido(BaseDeclarativa):
    __tablename__ = "detalles_pedido"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pedido_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pedidos.id", ondelete="CASCADE"), index=True, nullable=False
    )
    lote_cafe_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("lotes_cafe.id", ondelete="RESTRICT"), nullable=False
    )
    unidad_venta: Mapped[UnidadVenta] = mapped_column(
        Enum(UnidadVenta, name="unidad_venta_enum"), nullable=False
    )
    tipo_molienda: Mapped[TipoMolienda] = mapped_column(
        Enum(TipoMolienda, name="tipo_molienda_enum"),
        default=TipoMolienda.GRANO_ENTERO,
        nullable=False,
    )
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    equivalente_kg: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    precio_unitario_cop: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    subtotal_cop: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    pedido: Mapped["Pedido"] = relationship("Pedido", back_populates="detalles")
    lote_cafe: Mapped["LoteCafe"] = relationship("LoteCafe", back_populates="detalles_pedido")


class DatosFiscalesCliente(BaseDeclarativa):
    """Datos fiscales del comprador para facturación electrónica DIAN (CustomerTaxData)."""
    __tablename__ = "datos_fiscales_clientes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pedido_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pedidos.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    usuario_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), index=True, nullable=True
    )
    tipo_documento: Mapped[TipoDocumentoFiscal] = mapped_column(
        Enum(TipoDocumentoFiscal, name="tipo_documento_fiscal_enum"),
        default=TipoDocumentoFiscal.CC,
        nullable=False,
    )
    numero_documento: Mapped[str] = mapped_column(String(25), index=True, nullable=False)
    digito_verificacion: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    razon_social_o_nombre: Mapped[str] = mapped_column(String(180), nullable=False)
    correo_facturacion: Mapped[str] = mapped_column(String(150), nullable=False)
    tipo_persona: Mapped[TipoPersonaFiscal] = mapped_column(
        Enum(TipoPersonaFiscal, name="tipo_persona_fiscal_enum"),
        default=TipoPersonaFiscal.NATURAL,
        nullable=False,
    )
    regimen_tributario: Mapped[RegimenTributario] = mapped_column(
        Enum(RegimenTributario, name="regimen_tributario_enum"),
        default=RegimenTributario.NO_RESPONSABLE_IVA,
        nullable=False,
    )
    direccion_fiscal: Mapped[str] = mapped_column(String(250), nullable=False)
    codigo_municipio_dane: Mapped[str] = mapped_column(
        String(10), default="73001", nullable=False
    )
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    pedido: Mapped["Pedido"] = relationship("Pedido", back_populates="datos_fiscales")


class FacturaElectronica(BaseDeclarativa):
    """Entidad de Factura Electrónica DIAN con CUFE, QR, PDF y XML (Invoice)."""
    __tablename__ = "facturas_electronicas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pedido_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pedidos.id", ondelete="RESTRICT"), unique=True, index=True, nullable=False
    )
    numero_factura: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    cufe: Mapped[Optional[str]] = mapped_column(String(128), unique=True, index=True, nullable=True)
    url_codigo_qr: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    url_pdf: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    url_xml: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    estado_dian: Mapped[EstadoDianFactura] = mapped_column(
        Enum(EstadoDianFactura, name="estado_dian_factura_enum"),
        default=EstadoDianFactura.PENDIENTE,
        nullable=False,
    )
    mensaje_error_dian: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    pedido: Mapped["Pedido"] = relationship("Pedido", back_populates="factura_electronica")
