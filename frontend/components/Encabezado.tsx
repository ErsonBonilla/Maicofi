import CanastaCompra from "../islands/CanastaCompra.tsx";

interface PropiedadesEncabezado {
  urlBaseApi: string;
  rutaActiva?: "catalogo" | "caficultor";
}

export default function Encabezado({
  urlBaseApi,
  rutaActiva = "catalogo",
}: PropiedadesEncabezado) {
  return (
    <header class="bg-white border-b border-[#E5D5C5] sticky top-0 z-30 shadow-xs">
      <div class="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between gap-4">
        <a href="/" class="flex items-center gap-3 group" aria-label="Inicio Maicofi">
          <img
            src="/logo/Logo.png"
            alt="Isotipo Maicofi"
            class="h-11 w-auto transition-transform group-hover:scale-105"
          />
          <div class="flex flex-col">
            <img
              src="/logo/Frase-Maicofi.png"
              alt="Maicofi"
              class="h-6 w-auto object-contain object-left"
            />
            <span class="text-[11px] font-semibold tracking-wider uppercase text-[#2C4234]">
              Café Especial del Tolima
            </span>
          </div>
        </a>

        <nav class="flex items-center gap-2 sm:gap-3">
          <a
            href="/"
            class={`text-sm font-bold px-3.5 py-2.5 rounded-xl transition-colors ${
              rutaActiva === "catalogo"
                ? "bg-[#FAF6F0] text-[#54121B]"
                : "text-stone-700 hover:bg-stone-100"
            }`}
          >
            Catálogo
          </a>
          <a
            href="/producer/panel"
            class={`text-sm font-bold px-3.5 py-2.5 rounded-xl border-2 transition-colors ${
              rutaActiva === "caficultor"
                ? "bg-[#2C4234] text-white border-[#2C4234]"
                : "text-[#2C4234] border-[#2C4234] hover:bg-[#2C4234] hover:text-white"
            }`}
          >
            Panel Caficultor
          </a>
          <CanastaCompra urlBaseApi={urlBaseApi} />
        </nav>
      </div>
    </header>
  );
}
