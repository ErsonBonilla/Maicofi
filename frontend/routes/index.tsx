import { Handlers, PageProps } from "$fresh/server.ts";
import Encabezado from "../components/Encabezado.tsx";
import TarjetaProducto from "../components/TarjetaProducto.tsx";
import {
  consultarCatalogoCafe,
  FiltrosCatalogo,
  LoteCafeTolima,
  URL_BASE_API,
} from "../utils/clienteApi.ts";

interface DatosPaginaCatalogo {
  lotes: LoteCafeTolima[];
  filtros: FiltrosCatalogo;
  urlBaseApi: string;
}

export const handler: Handlers<DatosPaginaCatalogo> = {
  async GET(req, ctx) {
    const url = new URL(req.url);
    const filtros: FiltrosCatalogo = {
      municipio: url.searchParams.get("municipio") ?? "",
      variedad: url.searchParams.get("variedad") ?? "",
      proceso: url.searchParams.get("proceso") ?? "",
      puntajeScaMinimo: url.searchParams.get("puntaje_sca_minimo") ?? "",
      precioMaximoLibra: url.searchParams.get("precio_maximo_libra") ?? "",
      fincaId: url.searchParams.get("finca_id") ?? "",
      busqueda: url.searchParams.get("busqueda") ?? "",
    };

    const lotes = await consultarCatalogoCafe(filtros);
    return ctx.render({
      lotes,
      filtros,
      urlBaseApi: URL_BASE_API,
    });
  },
};

export default function PaginaCatalogoPrincipal({
  data,
}: PageProps<DatosPaginaCatalogo>) {
  return (
    <div class="min-h-screen flex flex-col justify-between">
      <div>
        <Encabezado urlBaseApi={data.urlBaseApi} rutaActiva="catalogo" />

        {/* Portada Regional del Tolima */}
        <section class="bg-gradient-to-br from-[#54121B] via-[#3E2424] to-[#2C4234] text-white py-12 md:py-16 px-4">
          <div class="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-8">
            <div class="max-w-2xl">
              <span class="inline-block text-xs uppercase tracking-widest bg-white/15 px-3.5 py-1.5 rounded-full font-bold">
                Origen Denominación Tolima • Comercio Directo
              </span>
              <h1 class="text-3xl md:text-5xl font-extrabold mt-4 leading-tight">
                Café especial de alta montaña, directo de las veredas del Tolima.
              </h1>
              <p class="mt-4 text-stone-200 text-base md:text-lg leading-relaxed">
                Conectamos sin intermediarios a las familias caficultoras de{" "}
                <strong>
                  Planadas, Líbano, Santa Isabel, Anzoátegui, Herrera e Ibagué
                </strong>{" "}
                con compradores al detal y tostadores mayoristas.
              </p>
            </div>

            <div class="bg-white/10 backdrop-blur-xs border border-white/20 rounded-2xl p-5 flex items-center gap-4">
              <img
                src="/logo/Logo-Completo.png"
                alt="Logo Completo Maicofi"
                class="h-24 w-auto bg-white p-3 rounded-xl shadow-md"
              />
              <div class="text-xs space-y-1.5 text-stone-100">
                <p class="font-bold text-sm text-white">Garantía de Origen</p>
                <p>• Puntaje SCA verificado (+84 pts)</p>
                <p>• Trazabilidad por finca y vereda</p>
                <p>• Venta por Libra, Arroba o Carga</p>
              </div>
            </div>
          </div>
        </section>

        {/* Barra de Filtros del Catálogo */}
        <main class="max-w-7xl mx-auto px-4 py-8">
          <form
            method="GET"
            class="bg-white p-5 rounded-2xl shadow-xs border border-[#E5D5C5] grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3 mb-8"
          >
            <div>
              <label class="block text-[11px] font-bold uppercase text-stone-500 mb-1">
                Municipio del Tolima
              </label>
              <select
                name="municipio"
                defaultValue={data.filtros.municipio}
                class="w-full px-3 py-2.5 rounded-xl border border-stone-300 text-sm font-semibold bg-white"
              >
                <option value="">Todos los municipios</option>
                <option value="Planadas">Planadas</option>
                <option value="Líbano">Líbano</option>
                <option value="Santa Isabel">Santa Isabel</option>
                <option value="Anzoátegui">Anzoátegui</option>
                <option value="Herrera (Rioblanco)">Herrera (Rioblanco)</option>
                <option value="Ibagué">Ibagué</option>
                <option value="Chaparral">Chaparral</option>
                <option value="Ataco">Ataco</option>
              </select>
            </div>

            <div>
              <label class="block text-[11px] font-bold uppercase text-stone-500 mb-1">
                Variedad de Café
              </label>
              <select
                name="variedad"
                defaultValue={data.filtros.variedad}
                class="w-full px-3 py-2.5 rounded-xl border border-stone-300 text-sm font-semibold bg-white"
              >
                <option value="">Todas las variedades</option>
                <option value="Castillo">Castillo</option>
                <option value="Caturra">Caturra</option>
                <option value="Tabi">Tabi</option>
                <option value="Geisha">Geisha</option>
                <option value="Bourbon Rosado">Bourbon Rosado</option>
                <option value="Colombia">Colombia</option>
                <option value="Típica">Típica</option>
              </select>
            </div>

            <div>
              <label class="block text-[11px] font-bold uppercase text-stone-500 mb-1">
                Proceso / Beneficio
              </label>
              <select
                name="proceso"
                defaultValue={data.filtros.proceso}
                class="w-full px-3 py-2.5 rounded-xl border border-stone-300 text-sm font-semibold bg-white"
              >
                <option value="">Todos los procesos</option>
                <option value="Lavado">Lavado</option>
                <option value="Natural">Natural</option>
                <option value="Honey">Honey</option>
                <option value="Fermentación Anaeróbica">Anaeróbico</option>
              </select>
            </div>

            <div>
              <label class="block text-[11px] font-bold uppercase text-stone-500 mb-1">
                Puntaje Taza SCA Mínimo
              </label>
              <input
                type="number"
                name="puntaje_sca_minimo"
                placeholder="Ej: 86.0"
                defaultValue={data.filtros.puntajeScaMinimo}
                step="0.5"
                min="80"
                max="100"
                class="w-full px-3 py-2.5 rounded-xl border border-stone-300 text-sm"
              />
            </div>

            <div>
              <label class="block text-[11px] font-bold uppercase text-stone-500 mb-1">
                Precio Máximo / Libra COP
              </label>
              <input
                type="number"
                name="precio_maximo_libra"
                placeholder="Ej: 45000"
                defaultValue={data.filtros.precioMaximoLibra}
                step="1000"
                class="w-full px-3 py-2.5 rounded-xl border border-stone-300 text-sm"
              />
            </div>

            <div class="flex items-end gap-2">
              <button
                type="submit"
                class="w-full bg-[#2C4234] hover:bg-[#54121B] text-white font-bold rounded-xl py-2.5 px-4 transition-colors text-sm min-h-[42px]"
              >
                Filtrar Catálogo
              </button>
            </div>
          </form>

          {data.lotes.length === 0 ? (
            <div class="bg-white rounded-2xl p-12 text-center border border-[#E5D5C5]">
              <h2 class="text-xl font-extrabold text-[#232323]">
                No encontramos lotes con esos filtros específicos
              </h2>
              <p class="text-sm text-stone-600 mt-2">
                Intenta ampliar el rango de precio o consultar todos los municipios del Tolima.
              </p>
              <a
                href="/"
                class="inline-block mt-4 bg-[#54121B] text-white font-bold text-sm px-5 py-2.5 rounded-xl"
              >
                Ver todos los lotes
              </a>
            </div>
          ) : (
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {data.lotes.map((lote) => (
                <TarjetaProducto key={lote.id} lote={lote} />
              ))}
            </div>
          )}
        </main>
      </div>

      <footer class="bg-white border-t border-[#E5D5C5] py-8 px-4 mt-12">
        <div class="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-stone-600">
          <div class="flex items-center gap-3">
            <img src="/logo/Logo.png" alt="Maicofi" class="h-8 w-auto" />
            <span>
              <strong>Maicofi</strong> — Plataforma de Café Especial del Tolima, Colombia.
            </span>
          </div>
          <span>
            Planadas • Líbano • Santa Isabel • Anzoátegui • Herrera • Ibagué
          </span>
        </div>
      </footer>
    </div>
  );
}
