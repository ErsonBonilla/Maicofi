import { Handlers, PageProps } from "$fresh/server.ts";
import Encabezado from "../../components/Encabezado.tsx";
import PerfilSensorial from "../../components/PerfilSensorial.tsx";
import CalculadoraPreparacion from "../../islands/CalculadoraPreparacion.tsx";
import ConfiguradorProducto from "../../islands/ConfiguradorProducto.tsx";
import MapaFinca from "../../islands/MapaFinca.tsx";
import {
  consultarDetalleLotePorIdOSlug,
  consultarHistoriaProductor,
  formatearPesosCOP,
  HistoriaCaficultorTolima,
  LoteCafeTolima,
  URL_BASE_API,
} from "../../utils/clienteApi.ts";

interface DatosDetalleEspecialidad {
  lote: LoteCafeTolima | null;
  historiaCaficultor: HistoriaCaficultorTolima | null;
  urlBaseApi: string;
}

export const handler: Handlers<DatosDetalleEspecialidad> = {
  async GET(_req, ctx) {
    const identificadorSlug = ctx.params.slug;
    const lote = await consultarDetalleLotePorIdOSlug(identificadorSlug);

    let historiaCaficultor: HistoriaCaficultorTolima | null = null;
    if (lote) {
      historiaCaficultor = await consultarHistoriaProductor(lote.fincaId);
    }

    return ctx.render({
      lote,
      historiaCaficultor,
      urlBaseApi: URL_BASE_API,
    });
  },
};

export default function PaginaDetalleCafeEspecialidad({
  data,
}: PageProps<DatosDetalleEspecialidad>) {
  const { lote, historiaCaficultor, urlBaseApi } = data;

  if (!lote) {
    return (
      <div class="min-h-screen bg-[#FAF6F0]">
        <Encabezado urlBaseApi={urlBaseApi} />
        <main class="max-w-4xl mx-auto px-4 py-16 text-center">
          <h1 class="text-2xl font-extrabold text-[#232323]">
            El lote de café solicitado no fue encontrado
          </h1>
          <a
            href="/"
            class="inline-block mt-4 bg-[#2C4234] text-white font-bold px-5 py-3 rounded-xl"
          >
            Volver al catálogo del Tolima
          </a>
        </main>
      </div>
    );
  }

  const fotoPrincipal = lote.urlsFotos?.[0] ||
    "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?auto=format&fit=crop&w=1000&q=80";

  const fotoProductor = historiaCaficultor?.fotoProductorUrl ||
    lote.finca.fotoProductorUrl ||
    "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=600&q=80";

  const otrosLotesFinca = (historiaCaficultor?.otrosLotes ?? []).filter(
    (item) => item.id !== lote.id,
  );

  const latitudFinca = historiaCaficultor?.latitud ?? lote.finca.latitud;
  const longitudFinca = historiaCaficultor?.longitud ?? lote.finca.longitud;

  return (
    <div class="min-h-screen bg-[#FAF6F0]">
      <Encabezado urlBaseApi={urlBaseApi} rutaActiva="catalogo" />

      <main class="max-w-7xl mx-auto px-4 py-8 space-y-10">
        {/* Migas de pan */}
        <nav class="text-xs font-semibold text-stone-500 flex flex-wrap items-center gap-2">
          <a href="/" class="hover:text-[#54121B]">Catálogo Tolima</a>
          <span>/</span>
          <a
            href={`/?municipio=${encodeURIComponent(lote.finca.municipio)}`}
            class="hover:text-[#54121B]"
          >
            {lote.finca.municipio}
          </a>
          <span>/</span>
          <span class="text-[#232323] font-bold">{lote.nombre}</span>
        </nav>

        {/* Bloque Principal: Ficha Técnica + Perfil Sensorial + Configurador de Compra */}
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 bg-white p-6 md:p-8 rounded-3xl shadow-xs border border-[#E5D5C5]">
          {/* Columna izquierda: Imagen, Ficha Técnica Completa y Rueda Sensorial */}
          <div class="lg:col-span-5 space-y-6">
            <div class="relative rounded-2xl overflow-hidden bg-[#2C4234] aspect-4/3">
              <img
                src={fotoPrincipal}
                alt={lote.nombre}
                class="w-full h-full object-cover"
              />
              <span class="absolute top-4 left-4 bg-[#54121B] text-white font-extrabold text-sm px-3.5 py-1.5 rounded-full shadow-md">
                Puntaje SCA {lote.puntajeSca.toFixed(2)} pts
              </span>
              {lote.valvulaDesgasificadora && (
                <span class="absolute bottom-4 left-4 bg-white/95 text-[#2C4234] font-extrabold text-xs px-3 py-1.5 rounded-xl shadow">
                  Empaque con Válvula Desgasificadora
                </span>
              )}
            </div>

            {/* A. Ficha Técnica Completa del Café de Especialidad */}
            <section class="bg-[#FAF6F0] rounded-2xl p-5 border border-[#E5D5C5] space-y-3">
              <div class="flex items-center justify-between border-b border-[#E5D5C5] pb-2">
                <h2 class="text-sm font-extrabold uppercase tracking-wider text-[#2C4234]">
                  Ficha Técnica de Especialidad
                </h2>
                <span class="text-[11px] font-bold text-[#54121B]">
                  Cosecha {lote.anioCosecha}
                </span>
              </div>

              <dl class="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <dt class="text-xs text-stone-500">Finca Productora</dt>
                  <dd class="font-bold text-[#232323]">
                    {lote.finca.nombreFinca}
                  </dd>
                </div>
                <div>
                  <dt class="text-xs text-stone-500">Municipio y Vereda</dt>
                  <dd class="font-bold text-[#232323]">
                    {lote.finca.municipio} ({lote.finca.vereda})
                  </dd>
                </div>
                <div>
                  <dt class="text-xs text-stone-500">Altura de Cultivo</dt>
                  <dd class="font-bold text-[#232323]">
                    {lote.finca.alturaMsnm} m.s.n.m.
                  </dd>
                </div>
                <div>
                  <dt class="text-xs text-stone-500">Variedad Botánica</dt>
                  <dd class="font-bold text-[#232323]">{lote.variedad}</dd>
                </div>
                <div>
                  <dt class="text-xs text-stone-500">Proceso de Beneficio</dt>
                  <dd class="font-bold text-[#232323]">{lote.proceso}</dd>
                </div>
                <div>
                  <dt class="text-xs text-stone-500">Puntaje Taza SCA</dt>
                  <dd class="font-extrabold text-[#54121B]">
                    {lote.puntajeSca.toFixed(2)} / 100
                  </dd>
                </div>
                <div>
                  <dt class="text-xs text-stone-500">Fecha de Tueste</dt>
                  <dd class="font-bold text-[#232323]">
                    {lote.fechaTueste ?? "Tueste bajo pedido"}
                  </dd>
                </div>
                <div>
                  <dt class="text-xs text-stone-500">Control de Empaque</dt>
                  <dd class="font-bold text-[#2C4234]">
                    {lote.valvulaDesgasificadora
                      ? "Con válvula desgasificadora 1 vía"
                      : "Saco tradicional"}
                  </dd>
                </div>
              </dl>
            </section>

            {/* B. Componente de Perfil Sensorial y Rueda de Sabores */}
            <PerfilSensorial
              perfil={lote.perfilSensorial}
              notasCata={lote.notasCata}
            />
          </div>

          {/* Columna derecha: Encabezado del Lote y Configurador Interactivo */}
          <div class="lg:col-span-7 flex flex-col justify-between space-y-6">
            <div class="space-y-4">
              <div class="flex flex-wrap items-center gap-2">
                <span class="text-xs font-extrabold uppercase tracking-wider bg-[#2C4234]/10 text-[#2C4234] px-3 py-1 rounded-full">
                  Origen {lote.finca.municipio}, Tolima • {lote.finca.alturaMsnm} m.s.n.m.
                </span>
                <span class="text-xs font-semibold text-stone-500">
                  Inventario disponible: {lote.stockDisponibleKg} kg
                </span>
              </div>

              <h1 class="text-2xl md:text-4xl font-extrabold text-[#232323] leading-tight">
                {lote.nombre}
              </h1>

              <p class="text-sm text-stone-600 leading-relaxed">
                Lote cultivado en la <strong>{lote.finca.nombreFinca}</strong> ({lote.finca.vereda})
                {lote.finca.nombrePropietario
                  ? ` por ${lote.finca.nombrePropietario}`
                  : ""}. Empacado en bolsa tricapa con válvula desgasificadora unidireccional para preservar los compuestos aromáticos volátiles recién tostados.
              </p>
            </div>

            {/* C & D. Isla ConfiguradorProducto (Presentación, Molienda y Suscripción -10%) */}
            <ConfiguradorProducto
              loteId={lote.id}
              nombreLote={lote.nombre}
              nombreFinca={lote.finca.nombreFinca}
              municipio={lote.finca.municipio}
              precioLibraCop={lote.precioLibraCop}
              precioArrobaCop={lote.precioArrobaCop}
              precioCargaCop={lote.precioCargaCop}
              stockDisponibleKg={lote.stockDisponibleKg}
              urlBaseApi={urlBaseApi}
            />
          </div>
        </div>

        {/* F. Guía de Preparación Interactiva (Isla CalculadoraPreparacion) */}
        <CalculadoraPreparacion
          nombreLote={lote.nombre}
          nivelTueste={lote.perfilSensorial.nivelTueste}
        />

        {/* E. Storytelling y Trazabilidad Directa del Productor */}
        <section class="bg-white rounded-3xl p-6 md:p-8 border border-[#E5D5C5] shadow-xs space-y-6">
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-stone-200 pb-4">
            <div>
              <span class="text-xs font-extrabold uppercase tracking-widest text-[#54121B]">
                Trazabilidad Directa a la Vereda
              </span>
              <h2 class="text-xl md:text-2xl font-extrabold text-[#232323]">
                Conoce al Caficultor Detrás de Tu Taza
              </h2>
            </div>

            <a
              href={`/?finca_id=${encodeURIComponent(lote.fincaId)}`}
              class="inline-flex items-center justify-center bg-[#2C4234] hover:bg-[#54121B] text-white font-bold text-xs px-4 py-2.5 rounded-xl transition-colors"
            >
              Ver todos los lotes de este productor
            </a>
          </div>

          <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
            <div class="lg:col-span-4 flex items-center gap-4 bg-[#FAF6F0] p-4 rounded-2xl border border-[#E5D5C5]">
              <img
                src={fotoProductor}
                alt={lote.finca.nombrePropietario || lote.finca.nombreFinca}
                class="w-20 h-20 rounded-2xl object-cover border-2 border-[#2C4234] shrink-0"
              />
              <div>
                <h3 class="font-extrabold text-base text-[#232323]">
                  {lote.finca.nombrePropietario || "Familia Caficultora"}
                </h3>
                <p class="text-xs font-bold text-[#2C4234]">
                  {lote.finca.nombreFinca}
                </p>
                <p class="text-xs text-stone-500 mt-0.5">
                  {lote.finca.vereda}, {lote.finca.municipio} (Tolima)
                </p>
                <span class="inline-block mt-1.5 text-[11px] font-bold bg-white px-2.5 py-0.5 rounded-full border border-[#E5D5C5] text-[#54121B]">
                  Altitud: {lote.finca.alturaMsnm} m.s.n.m.
                </span>
              </div>
            </div>

            <div class="lg:col-span-5 space-y-2">
              <h4 class="text-xs font-extrabold uppercase tracking-wider text-stone-500">
                Historia Familiar y Tradición Cafetera
              </h4>
              <p class="text-sm text-stone-700 leading-relaxed">
                {historiaCaficultor?.historiaProductor ||
                  lote.finca.historiaProductor}
              </p>
            </div>

            {/* D. Geolocalización Interactiva de Finca (Leaflet.js + OpenStreetMap) */}
            <div class="lg:col-span-3 bg-[#FAF6F0] p-4 rounded-2xl border border-[#E5D5C5] space-y-2.5">
              {latitudFinca !== undefined && longitudFinca !== undefined ? (
                <MapaFinca
                  latitud={latitudFinca}
                  longitud={longitudFinca}
                  nombreFinca={lote.finca.nombreFinca}
                  municipio={lote.finca.municipio}
                  vereda={lote.finca.vereda}
                  alturaMsnm={lote.finca.alturaMsnm}
                  nombreProductor={lote.finca.nombrePropietario}
                />
              ) : (
                <>
                  <span class="block text-xs font-extrabold uppercase tracking-wider text-[#2C4234]">
                    Geolocalización en el Tolima
                  </span>
                  <p class="text-xs text-stone-600">
                    Cordillera Central / Sur del Tolima — Microclima de bosque de niebla andino.
                  </p>
                </>
              )}
            </div>
          </div>

          {otrosLotesFinca.length > 0 && (
            <div class="pt-4 border-t border-stone-200">
              <h4 class="text-xs font-extrabold uppercase tracking-wider text-stone-500 mb-3">
                Otros lotes cosechados en {lote.finca.nombreFinca}
              </h4>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {otrosLotesFinca.map((otro) => (
                  <a
                    key={otro.id}
                    href={`/products/${otro.slug || otro.id}`}
                    class="flex items-center justify-between p-4 rounded-2xl bg-[#FAF6F0] hover:bg-[#EFE6D5] border border-[#E5D5C5] transition-colors"
                  >
                    <div>
                      <span class="text-[11px] font-extrabold text-[#2C4234] uppercase">
                        Variedad {otro.variedad} • {otro.proceso}
                      </span>
                      <p class="font-extrabold text-sm text-[#232323]">
                        {otro.nombre}
                      </p>
                      <p class="text-xs text-stone-600">
                        SCA {otro.puntajeSca.toFixed(2)} pts
                      </p>
                    </div>
                    <span class="font-extrabold text-sm text-[#54121B]">
                      {formatearPesosCOP(otro.precioLibraCop)} / lb
                    </span>
                  </a>
                ))}
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
