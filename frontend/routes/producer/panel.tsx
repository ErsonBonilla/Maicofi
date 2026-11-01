import { Handlers, PageProps } from "$fresh/server.ts";
import Encabezado from "../../components/Encabezado.tsx";
import FormularioCaficultor from "../../islands/FormularioCaficultor.tsx";
import { URL_BASE_API } from "../../utils/clienteApi.ts";

interface DatosPanelCaficultor {
  urlBaseApi: string;
}

export const handler: Handlers<DatosPanelCaficultor> = {
  GET(_req, ctx) {
    return ctx.render({
      urlBaseApi: URL_BASE_API,
    });
  },
};

export default function PaginaPanelCaficultor({
  data,
}: PageProps<DatosPanelCaficultor>) {
  return (
    <div class="min-h-screen bg-[#FAF6F0]">
      <Encabezado urlBaseApi={data.urlBaseApi} rutaActiva="caficultor" />

      <main class="max-w-4xl mx-auto px-4 py-8 space-y-6">
        <div class="bg-gradient-to-r from-[#2C4234] to-[#54121B] text-white rounded-3xl p-6 md:p-8 shadow-md">
          <span class="text-xs font-bold uppercase tracking-widest bg-white/15 px-3 py-1 rounded-full">
            Módulo de Caficultores del Tolima
          </span>
          <h1 class="text-2xl md:text-4xl font-extrabold mt-3">
            Panel de Gestión de Finca y Cosecha
          </h1>
          <p class="text-sm md:text-base text-stone-200 mt-2 max-w-2xl">
            Publica tus lotes desde el celular usando las medidas tradicionales de la caficultura colombiana: libras, arrobas y cargas de café pergamino o tostado.
          </p>
        </div>

        <FormularioCaficultor urlBaseApi={data.urlBaseApi} />
      </main>
    </div>
  );
}
