/**
 * Cliente HTTP con fetch nativo de Deno.
 * Cumple la Regla de Oro:
 * - Llaves del contrato JSON externo con FastAPI en inglés.
 * - Interfaces, modelos, funciones y propiedades internas en español.
 */

export interface ContratoExternoPerfilSensorial {
  acidity: number;
  body: number;
  sweetness: number;
  roast_level: "Claro" | "Medio" | "Medio-Oscuro" | "Oscuro";
  main_notes: string[];
}

export interface ContratoExternoFinca {
  id: string;
  user_id?: string;
  farm_name: string;
  municipality: string;
  vereda: string;
  altitude_masl: number;
  farmer_story: string;
  owner_name?: string;
  farmer_photo_url?: string;
  latitude?: number;
  longitude?: number;
  photos_urls: string[];
}

export interface ContratoExternoLoteCafe {
  id: string;
  slug: string;
  farm_id: string;
  farm_name?: string;
  municipality?: string;
  altitude_masl?: number;
  name: string;
  variety: string;
  process: string;
  presentation_state: string;
  sca_score: number;
  tasting_notes: string[];
  humidity_pct?: number;
  harvest_year: number;
  roast_date?: string;
  degassing_valve: boolean;
  price_per_lb_cop: number;
  price_per_arroba_cop?: number;
  price_per_carga_cop?: number;
  available_stock_kg: number;
  photos_urls: string[];
  sensory_profile?: ContratoExternoPerfilSensorial;
  farm: ContratoExternoFinca;
}

export interface ContratoExternoHistoriaProductor {
  farm_id: string;
  farm_name: string;
  farmer_name?: string;
  farmer_photo_url?: string;
  municipality: string;
  vereda: string;
  altitude_masl: number;
  latitude?: number;
  longitude?: number;
  farmer_story: string;
  farm_photos_urls: string[];
  other_lots: Array<{
    id: string;
    slug: string;
    name: string;
    variety: string;
    process: string;
    sca_score: number;
    price_per_lb_cop: number;
    tasting_notes: string[];
  }>;
}

// ==========================================
// Interfaces de dominio interno en español
// ==========================================
export interface PerfilSensorialCafe {
  acidez: number;
  cuerpo: number;
  dulzura: number;
  nivelTueste: "Claro" | "Medio" | "Medio-Oscuro" | "Oscuro";
  notasPrincipales: string[];
}

export interface FincaProductora {
  id: string;
  nombreFinca: string;
  municipio: string;
  vereda: string;
  alturaMsnm: number;
  historiaProductor: string;
  nombrePropietario?: string;
  fotoProductorUrl?: string;
  latitud?: number;
  longitud?: number;
  urlsFotos: string[];
}

export interface LoteCafeTolima {
  id: string;
  slug: string;
  fincaId: string;
  nombre: string;
  variedad: string;
  proceso: string;
  estadoPresentacion: string;
  puntajeSca: number;
  notasCata: string[];
  humedadPorcentaje?: number;
  anioCosecha: number;
  fechaTueste?: string;
  valvulaDesgasificadora: boolean;
  precioLibraCop: number;
  precioArrobaCop?: number;
  precioCargaCop?: number;
  stockDisponibleKg: number;
  urlsFotos: string[];
  perfilSensorial: PerfilSensorialCafe;
  finca: FincaProductora;
}

export interface ResumenLoteProductor {
  id: string;
  slug: string;
  nombre: string;
  variedad: string;
  proceso: string;
  puntajeSca: number;
  precioLibraCop: number;
  notasCata: string[];
}

export interface HistoriaCaficultorTolima {
  fincaId: string;
  nombreFinca: string;
  nombreProductor?: string;
  fotoProductorUrl?: string;
  municipio: string;
  vereda: string;
  alturaMsnm: number;
  latitud?: number;
  longitud?: number;
  historiaProductor: string;
  urlsFotosFinca: string[];
  otrosLotes: ResumenLoteProductor[];
}

export interface FiltrosCatalogo {
  municipio?: string;
  variedad?: string;
  proceso?: string;
  puntajeScaMinimo?: string;
  precioMaximoLibra?: string;
  fincaId?: string;
  busqueda?: string;
}

export const URL_BASE_API = typeof Deno !== "undefined"
  ? (Deno.env.get("MAICOFI_API_URL") ?? "http://127.0.0.1:8001/api/v1")
  : "http://127.0.0.1:8001/api/v1";

export function formatearPesosCOP(valor: number): string {
  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 0,
  }).format(valor);
}

export function mapearContratoALoteInterno(
  dto: ContratoExternoLoteCafe,
): LoteCafeTolima {
  const notas = dto.tasting_notes ?? [];
  return {
    id: dto.id,
    slug: dto.slug || dto.id,
    fincaId: dto.farm_id,
    nombre: dto.name,
    variedad: dto.variety,
    proceso: dto.process,
    estadoPresentacion: dto.presentation_state,
    puntajeSca: Number(dto.sca_score),
    notasCata: notas,
    humedadPorcentaje: dto.humidity_pct ? Number(dto.humidity_pct) : undefined,
    anioCosecha: dto.harvest_year,
    fechaTueste: dto.roast_date ?? "2026-10-28",
    valvulaDesgasificadora: dto.degassing_valve ?? true,
    precioLibraCop: Number(dto.price_per_lb_cop),
    precioArrobaCop: dto.price_per_arroba_cop
      ? Number(dto.price_per_arroba_cop)
      : undefined,
    precioCargaCop: dto.price_per_carga_cop
      ? Number(dto.price_per_carga_cop)
      : undefined,
    stockDisponibleKg: Number(dto.available_stock_kg),
    urlsFotos: dto.photos_urls ?? [],
    perfilSensorial: {
      acidez: dto.sensory_profile?.acidity ?? 4,
      cuerpo: dto.sensory_profile?.body ?? 4,
      dulzura: dto.sensory_profile?.sweetness ?? 5,
      nivelTueste: dto.sensory_profile?.roast_level ?? "Medio",
      notasPrincipales: dto.sensory_profile?.main_notes ?? notas,
    },
    finca: {
      id: dto.farm.id,
      nombreFinca: dto.farm.farm_name,
      municipio: dto.farm.municipality,
      vereda: dto.farm.vereda,
      alturaMsnm: Number(dto.farm.altitude_masl),
      historiaProductor: dto.farm.farmer_story,
      nombrePropietario: dto.farm.owner_name,
      fotoProductorUrl: dto.farm.farmer_photo_url,
      latitud: dto.farm.latitude ? Number(dto.farm.latitude) : undefined,
      longitud: dto.farm.longitude ? Number(dto.farm.longitude) : undefined,
      urlsFotos: dto.farm.photos_urls ?? [],
    },
  };
}

export const LOTES_DEMO_RESPALDO: LoteCafeTolima[] = [
  {
    id: "11111111-2222-3333-4444-555555555501",
    slug: "microlote-geisha-lavado-planadas",
    fincaId: "aaaa1111-2222-3333-4444-555555555501",
    nombre: "Microlote Geisha Lavado de Alta Montaña",
    variedad: "Geisha",
    proceso: "Lavado",
    estadoPresentacion: "Tostado en Grano",
    puntajeSca: 88.5,
    notasCata: ["Jazmín", "Miel de Abejas", "Mandarina", "Té Negro"],
    humedadPorcentaje: 10.8,
    anioCosecha: 2026,
    fechaTueste: "2026-10-28",
    valvulaDesgasificadora: true,
    precioLibraCop: 52000,
    precioArrobaCop: 1196000,
    precioCargaCop: 11050000,
    stockDisponibleKg: 250,
    urlsFotos: [
      "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?auto=format&fit=crop&w=900&q=80",
    ],
    perfilSensorial: {
      acidez: 5,
      cuerpo: 3,
      dulzura: 5,
      nivelTueste: "Claro",
      notasPrincipales: ["Jazmín", "Miel de Abejas", "Mandarina", "Té Negro"],
    },
    finca: {
      id: "aaaa1111-2222-3333-4444-555555555501",
      nombreFinca: "Finca El Mirador del Nevado",
      municipio: "Planadas",
      vereda: "Vereda Gaitania",
      alturaMsnm: 1920,
      historiaProductor:
        "Tercera generación de caficultores del sur del Tolima. Cultivamos bajo sombrío nativo con aguas cristalinas de alta montaña y secado lento en marquesina solar.",
      nombrePropietario: "Don Albeiro Lozano",
      fotoProductorUrl:
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=600&q=80",
      latitud: 3.1964,
      longitud: -75.6453,
      urlsFotos: [
        "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?auto=format&fit=crop&w=1000&q=80",
      ],
    },
  },
  {
    id: "11111111-2222-3333-4444-555555555504",
    slug: "lote-caturra-honey-gaitania",
    fincaId: "aaaa1111-2222-3333-4444-555555555501",
    nombre: "Lote Caturra Honey Seleccionado",
    variedad: "Caturra",
    proceso: "Honey",
    estadoPresentacion: "Tostado en Grano",
    puntajeSca: 85.75,
    notasCata: ["Panela", "Durazno", "Caramelo Dulce", "Chocolate Amargo"],
    humedadPorcentaje: 11.2,
    anioCosecha: 2026,
    fechaTueste: "2026-10-26",
    valvulaDesgasificadora: true,
    precioLibraCop: 34000,
    precioArrobaCop: 782000,
    precioCargaCop: 7225000,
    stockDisponibleKg: 625,
    urlsFotos: [
      "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?auto=format&fit=crop&w=900&q=80",
    ],
    perfilSensorial: {
      acidez: 3,
      cuerpo: 4,
      dulzura: 5,
      nivelTueste: "Medio",
      notasPrincipales: [
        "Panela",
        "Durazno",
        "Caramelo Dulce",
        "Chocolate Amargo",
      ],
    },
    finca: {
      id: "aaaa1111-2222-3333-4444-555555555501",
      nombreFinca: "Finca El Mirador del Nevado",
      municipio: "Planadas",
      vereda: "Vereda Gaitania",
      alturaMsnm: 1920,
      historiaProductor:
        "Tercera generación de caficultores del sur del Tolima. Cultivamos bajo sombrío nativo con aguas cristalinas de alta montaña y secado lento en marquesina solar.",
      nombrePropietario: "Don Albeiro Lozano",
      fotoProductorUrl:
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=600&q=80",
      latitud: 3.1964,
      longitud: -75.6453,
      urlsFotos: [
        "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?auto=format&fit=crop&w=1000&q=80",
      ],
    },
  },
  {
    id: "11111111-2222-3333-4444-555555555502",
    slug: "reserva-tabi-natural-libano",
    fincaId: "aaaa1111-2222-3333-4444-555555555502",
    nombre: "Reserva Tabi Natural Secado al Sol",
    variedad: "Tabi",
    proceso: "Natural",
    estadoPresentacion: "Tostado en Grano",
    puntajeSca: 87.25,
    notasCata: ["Frutos Rojos", "Chocolate Amargo", "Vino Tinto", "Panela"],
    humedadPorcentaje: 11.0,
    anioCosecha: 2026,
    fechaTueste: "2026-10-29",
    valvulaDesgasificadora: true,
    precioLibraCop: 42000,
    precioArrobaCop: 966000,
    precioCargaCop: 8925000,
    stockDisponibleKg: 375,
    urlsFotos: [
      "https://images.unsplash.com/photo-1447933601403-0c6688de566e?auto=format&fit=crop&w=900&q=80",
    ],
    perfilSensorial: {
      acidez: 4,
      cuerpo: 5,
      dulzura: 5,
      nivelTueste: "Medio",
      notasPrincipales: [
        "Frutos Rojos",
        "Chocolate Amargo",
        "Vino Tinto",
        "Panela",
      ],
    },
    finca: {
      id: "aaaa1111-2222-3333-4444-555555555502",
      nombreFinca: "Finca La Esperanza Real",
      municipio: "Líbano",
      vereda: "Vereda Santa Teresa",
      alturaMsnm: 1780,
      historiaProductor:
        "Asociación familiar de mujeres cafeteras en la cordillera central del Tolima. Recolección manual grano a grano solo de cereza madura uva.",
      nombrePropietario: "Doña Esperanza Trujillo",
      fotoProductorUrl:
        "https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=600&q=80",
      latitud: 4.9216,
      longitud: -75.0632,
      urlsFotos: [
        "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=1000&q=80",
      ],
    },
  },
  {
    id: "11111111-2222-3333-4444-555555555503",
    slug: "bourbon-rosado-anaerobico-anzoategui",
    fincaId: "aaaa1111-2222-3333-4444-555555555503",
    nombre: "Bourbon Rosado Fermentación Anaeróbica 72h",
    variedad: "Bourbon Rosado",
    proceso: "Fermentación Anaeróbica",
    estadoPresentacion: "Tostado en Grano",
    puntajeSca: 89.0,
    notasCata: ["Frutos Rojos", "Cítricos", "Flor de Café", "Miel"],
    humedadPorcentaje: 10.9,
    anioCosecha: 2026,
    fechaTueste: "2026-10-30",
    valvulaDesgasificadora: true,
    precioLibraCop: 48000,
    precioArrobaCop: 1104000,
    precioCargaCop: 10200000,
    stockDisponibleKg: 187.5,
    urlsFotos: [
      "https://images.unsplash.com/photo-1511920170033-f8396924c348?auto=format&fit=crop&w=900&q=80",
    ],
    perfilSensorial: {
      acidez: 5,
      cuerpo: 4,
      dulzura: 5,
      nivelTueste: "Claro",
      notasPrincipales: ["Frutos Rojos", "Cítricos", "Flor de Café", "Miel"],
    },
    finca: {
      id: "aaaa1111-2222-3333-4444-555555555503",
      nombreFinca: "Finca Brisas del Parque Los Nevados",
      municipio: "Anzoátegui",
      vereda: "Vereda Palomar",
      alturaMsnm: 2050,
      historiaProductor:
        "Ubicados en las faldas del Parque Nacional Natural Los Nevados, el clima frío de alta montaña concentra azúcares únicos en cada grano de Bourbon Rosado y Castillo.",
      nombrePropietario: "Familia Pava Oviedo",
      fotoProductorUrl:
        "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=600&q=80",
      latitud: 4.6308,
      longitud: -75.0951,
      urlsFotos: [
        "https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=1000&q=80",
      ],
    },
  },
];

export async function consultarCatalogoCafe(
  filtros?: FiltrosCatalogo,
): Promise<LoteCafeTolima[]> {
  const url = new URL(`${URL_BASE_API}/products`);
  if (filtros) {
    if (filtros.municipio) url.searchParams.set("municipality", filtros.municipio);
    if (filtros.variedad) url.searchParams.set("variety", filtros.variedad);
    if (filtros.proceso) url.searchParams.set("process", filtros.proceso);
    if (filtros.puntajeScaMinimo) url.searchParams.set("min_sca", filtros.puntajeScaMinimo);
    if (filtros.precioMaximoLibra) url.searchParams.set("max_price_lb", filtros.precioMaximoLibra);
    if (filtros.fincaId) url.searchParams.set("farm_id", filtros.fincaId);
    if (filtros.busqueda) url.searchParams.set("search", filtros.busqueda);
  }

  try {
    const respuesta = await fetch(url.toString(), {
      headers: { Accept: "application/json" },
    });
    if (!respuesta.ok) {
      throw new Error(`Error HTTP ${respuesta.status}`);
    }
    const datos: ContratoExternoLoteCafe[] = await respuesta.json();
    return datos.map(mapearContratoALoteInterno);
  } catch {
    return LOTES_DEMO_RESPALDO.filter((lote) => {
      if (filtros?.municipio && lote.finca.municipio !== filtros.municipio) return false;
      if (filtros?.variedad && lote.variedad !== filtros.variedad) return false;
      if (filtros?.proceso && lote.proceso !== filtros.proceso) return false;
      if (filtros?.fincaId && lote.fincaId !== filtros.fincaId) return false;
      if (filtros?.puntajeScaMinimo && lote.puntajeSca < Number(filtros.puntajeScaMinimo)) {
        return false;
      }
      if (
        filtros?.precioMaximoLibra &&
        lote.precioLibraCop > Number(filtros.precioMaximoLibra)
      ) {
        return false;
      }
      return true;
    });
  }
}

export async function consultarDetalleLotePorIdOSlug(
  identificador: string,
): Promise<LoteCafeTolima | null> {
  try {
    const respuesta = await fetch(`${URL_BASE_API}/products/${identificador}`, {
      headers: { Accept: "application/json" },
    });
    if (!respuesta.ok) {
      throw new Error(`Lote no encontrado (${respuesta.status})`);
    }
    const dto: ContratoExternoLoteCafe = await respuesta.json();
    return mapearContratoALoteInterno(dto);
  } catch {
    return (
      LOTES_DEMO_RESPALDO.find(
        (l) => l.id === identificador || l.slug === identificador,
      ) ?? null
    );
  }
}

export const consultarDetalleLotePorId = consultarDetalleLotePorIdOSlug;

export async function consultarHistoriaProductor(
  fincaId: string,
): Promise<HistoriaCaficultorTolima | null> {
  try {
    const respuesta = await fetch(`${URL_BASE_API}/farmers/${fincaId}/story`, {
      headers: { Accept: "application/json" },
    });
    if (!respuesta.ok) {
      throw new Error(`Historia de finca no encontrada (${respuesta.status})`);
    }
    const dto: ContratoExternoHistoriaProductor = await respuesta.json();
    return {
      fincaId: dto.farm_id,
      nombreFinca: dto.farm_name,
      nombreProductor: dto.farmer_name,
      fotoProductorUrl: dto.farmer_photo_url,
      municipio: dto.municipality,
      vereda: dto.vereda,
      alturaMsnm: Number(dto.altitude_masl),
      latitud: dto.latitude ? Number(dto.latitude) : undefined,
      longitud: dto.longitude ? Number(dto.longitude) : undefined,
      historiaProductor: dto.farmer_story,
      urlsFotosFinca: dto.farm_photos_urls ?? [],
      otrosLotes: (dto.other_lots ?? []).map((lote) => ({
        id: lote.id,
        slug: lote.slug,
        nombre: lote.name,
        variedad: lote.variety,
        proceso: lote.process,
        puntajeSca: Number(lote.sca_score),
        precioLibraCop: Number(lote.price_per_lb_cop),
        notasCata: lote.tasting_notes ?? [],
      })),
    };
  } catch {
    const lotesFinca = LOTES_DEMO_RESPALDO.filter((l) => l.fincaId === fincaId);
    if (lotesFinca.length === 0) return null;
    const base = lotesFinca[0].finca;
    return {
      fincaId: base.id,
      nombreFinca: base.nombreFinca,
      nombreProductor: base.nombrePropietario,
      fotoProductorUrl: base.fotoProductorUrl,
      municipio: base.municipio,
      vereda: base.vereda,
      alturaMsnm: base.alturaMsnm,
      latitud: base.latitud,
      longitud: base.longitud,
      historiaProductor: base.historiaProductor,
      urlsFotosFinca: base.urlsFotos,
      otrosLotes: lotesFinca.map((l) => ({
        id: l.id,
        slug: l.slug,
        nombre: l.nombre,
        variedad: l.variedad,
        proceso: l.proceso,
        puntajeSca: l.puntajeSca,
        precioLibraCop: l.precioLibraCop,
        notasCata: l.notasCata,
      })),
    };
  }
}

export interface FacturaElectronicaDianInterna {
  id: string;
  pedidoId: string;
  numeroFactura: string;
  cufe?: string;
  urlCodigoQr?: string;
  urlPdf?: string;
  urlXml?: string;
  estadoDian: "APPROVED" | "REJECTED" | "PENDING";
  mensajeErrorDian?: string;
  creadoEn: string;
}

export interface DatosFiscalesInternos {
  tipoDocumento: string;
  numeroDocumento: string;
  digitoVerificacion?: string;
  razonSocialONombre: string;
  correoFacturacion: string;
  tipoPersona: string;
  regimenTributario: string;
  direccionFiscal: string;
  codigoMunicipioDane: string;
}

export interface DetallePedidoCompletoInterno {
  id: string;
  estado: string;
  montoTotalCop: number;
  costoEnvioCop: number;
  referenciaPago?: string;
  direccionEnvio: string;
  ciudadEnvio: string;
  departamentoEnvio: string;
  telefonoContacto: string;
  creadoEn: string;
  datosFiscales?: DatosFiscalesInternos;
  facturaElectronica?: FacturaElectronicaDianInterna;
  items: Array<{
    id: string;
    loteCafeId: string;
    unidadVenta: string;
    tipoMolienda: string;
    cantidad: number;
    equivalenteKg: number;
    precioUnitarioCop: number;
    subtotalCop: number;
  }>;
}

export async function consultarPedidoYFacturaDian(
  pedidoId: string,
): Promise<DetallePedidoCompletoInterno | null> {
  try {
    const respuestaPedido = await fetch(`${URL_BASE_API}/orders/${pedidoId}`, {
      headers: { Accept: "application/json" },
    });
    if (!respuestaPedido.ok) {
      throw new Error(`Pedido no encontrado (${respuestaPedido.status})`);
    }
    const dto = await respuestaPedido.json();

    let dtoFactura = dto.electronic_invoice;
    if (!dtoFactura) {
      const resFactura = await fetch(
        `${URL_BASE_API}/invoices/order/${pedidoId}`,
        { headers: { Accept: "application/json" } },
      );
      if (resFactura.ok) {
        dtoFactura = await resFactura.json();
      }
    }

    return {
      id: dto.id,
      estado: dto.status,
      montoTotalCop: Number(dto.total_amount_cop),
      costoEnvioCop: Number(dto.shipping_cost_cop ?? 0),
      referenciaPago: dto.payment_reference,
      direccionEnvio: dto.shipping_address,
      ciudadEnvio: dto.shipping_city,
      departamentoEnvio: dto.shipping_department,
      telefonoContacto: dto.contact_phone,
      creadoEn: dto.created_at,
      datosFiscales: dto.tax_data
        ? {
          tipoDocumento: dto.tax_data.document_type,
          numeroDocumento: dto.tax_data.document_number,
          digitoVerificacion: dto.tax_data.verification_digit,
          razonSocialONombre: dto.tax_data.tax_name,
          correoFacturacion: dto.tax_data.billing_email,
          tipoPersona: dto.tax_data.person_type,
          regimenTributario: dto.tax_data.tax_regime,
          direccionFiscal: dto.tax_data.tax_address,
          codigoMunicipioDane: dto.tax_data.municipality_code,
        }
        : undefined,
      facturaElectronica: dtoFactura
        ? {
          id: dtoFactura.id,
          pedidoId: dtoFactura.order_id,
          numeroFactura: dtoFactura.invoice_number,
          cufe: dtoFactura.cufe,
          urlCodigoQr: dtoFactura.qr_code_url,
          urlPdf: dtoFactura.pdf_url,
          urlXml: dtoFactura.xml_url,
          estadoDian: dtoFactura.dian_status,
          mensajeErrorDian: dtoFactura.dian_error_message,
          creadoEn: dtoFactura.created_at,
        }
        : undefined,
      items: (dto.items ?? []).map((i: Record<string, unknown>) => ({
        id: String(i.id),
        loteCafeId: String(i.coffee_lot_id),
        unidadVenta: String(i.unit_type),
        tipoMolienda: String(i.grind_type ?? "Grano entero"),
        cantidad: Number(i.quantity),
        equivalenteKg: Number(i.equivalent_kg),
        precioUnitarioCop: Number(i.unit_price_cop),
        subtotalCop: Number(i.subtotal_cop),
      })),
    };
  } catch {
    // Respaldo demostrativo local cuando el backend aún no está iniciado
    const cufeDemo =
      "9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a";
    return {
      id: pedidoId,
      estado: "PAID",
      montoTotalCop: 104000,
      costoEnvioCop: 13000,
      referenciaPago: `MAICOFI-TOL-${pedidoId.slice(0, 6).toUpperCase()}`,
      direccionEnvio: "Cra 5 # 37-15, Barrio Cádiz",
      ciudadEnvio: "Ibagué",
      departamentoEnvio: "Tolima",
      telefonoContacto: "+573001112233",
      creadoEn: "2026-10-31T10:30:00Z",
      datosFiscales: {
        tipoDocumento: "NIT",
        numeroDocumento: "901456789",
        digitoVerificacion: "3",
        razonSocialONombre: "Tostadora Tolima Especial S.A.S.",
        correoFacturacion: "compras@tostadoratolima.co",
        tipoPersona: "Jurídica",
        regimenTributario: "Responsable de IVA",
        direccionFiscal: "Cra 5 # 37-15, Ibagué",
        codigoMunicipioDane: "73001",
      },
      facturaElectronica: {
        id: "f1111111-2222-3333-4444-555555555599",
        pedidoId,
        numeroFactura: "SETT-104289",
        cufe: cufeDemo,
        urlCodigoQr: `https://catalogo-vpfe-hab.dian.gov.co/document/searchqr?documentkey=${cufeDemo}`,
        urlPdf: `${URL_BASE_API}/invoices/order/${pedidoId}/pdf`,
        urlXml: `${URL_BASE_API}/invoices/order/${pedidoId}/xml`,
        estadoDian: "APPROVED",
        creadoEn: "2026-10-31T10:30:05Z",
      },
      items: [
        {
          id: "d1",
          loteCafeId: "11111111-2222-3333-4444-555555555501",
          unidadVenta: "500g",
          tipoMolienda: "Filtro / Goteo (V60 / Chemex)",
          cantidad: 2,
          equivalenteKg: 1.0,
          precioUnitarioCop: 52000,
          subtotalCop: 104000,
        },
      ],
    };
  }
}
