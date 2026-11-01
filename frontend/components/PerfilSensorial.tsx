import { PerfilSensorialCafe } from "../utils/clienteApi.ts";

interface PropiedadesPerfilSensorial {
  perfil: PerfilSensorialCafe;
  notasCata: string[];
}

function obtenerCategoriaDescriptor(nota: string): {
  familia: string;
  colorFondo: string;
  colorTexto: string;
  colorBorde: string;
} {
  const texto = nota.toLowerCase();
  if (
    texto.includes("panela") ||
    texto.includes("miel") ||
    texto.includes("caramelo") ||
    texto.includes("caña")
  ) {
    return {
      familia: "Dulce / Melaza",
      colorFondo: "bg-amber-50",
      colorTexto: "text-amber-900",
      colorBorde: "border-amber-300",
    };
  }
  if (texto.includes("chocolate") || texto.includes("cacao")) {
    return {
      familia: "Cacao / Tostado",
      colorFondo: "bg-stone-100",
      colorTexto: "text-stone-900",
      colorBorde: "border-stone-400",
    };
  }
  if (
    texto.includes("cítric") ||
    texto.includes("mandarina") ||
    texto.includes("naranja") ||
    texto.includes("limón")
  ) {
    return {
      familia: "Cítrico Brillante",
      colorFondo: "bg-yellow-50",
      colorTexto: "text-yellow-900",
      colorBorde: "border-yellow-300",
    };
  }
  if (
    texto.includes("jazmín") ||
    texto.includes("flor") ||
    texto.includes("té")
  ) {
    return {
      familia: "Floral / Herbáceo",
      colorFondo: "bg-emerald-50",
      colorTexto: "text-emerald-900",
      colorBorde: "border-emerald-300",
    };
  }
  return {
    familia: "Frutal de Montaña",
    colorFondo: "bg-[#FAF6F0]",
    colorTexto: "text-[#54121B]",
    colorBorde: "border-[#D9C3B0]",
  };
}

const NIVELES_TUESTE: Array<"Claro" | "Medio" | "Medio-Oscuro" | "Oscuro"> = [
  "Claro",
  "Medio",
  "Medio-Oscuro",
  "Oscuro",
];

function BarraAtributoSensorial({
  etiqueta,
  valor,
  descripcionNivel,
}: {
  etiqueta: string;
  valor: number;
  descripcionNivel: string;
}) {
  const valorSeguro = Math.min(5, Math.max(1, Math.round(valor)));

  return (
    <div class="space-y-1.5">
      <div class="flex items-center justify-between text-xs">
        <span class="font-extrabold uppercase tracking-wider text-[#232323]">
          {etiqueta}
        </span>
        <span class="font-bold text-[#54121B]">
          {valorSeguro}/5 • {descripcionNivel}
        </span>
      </div>
      <div
        class="grid grid-cols-5 gap-1.5"
        role="meter"
        aria-valuenow={valorSeguro}
        aria-valuemin={1}
        aria-valuemax={5}
      >
        {[1, 2, 3, 4, 5].map((segmento) => (
          <div
            key={segmento}
            class={`h-2.5 rounded-full transition-all ${
              segmento <= valorSeguro
                ? "bg-gradient-to-r from-[#54121B] to-[#2C4234]"
                : "bg-stone-200"
            }`}
          />
        ))}
      </div>
    </div>
  );
}

export default function PerfilSensorial({
  perfil,
  notasCata,
}: PropiedadesPerfilSensorial) {
  const descriptores = notasCata.length > 0
    ? notasCata
    : perfil.notasPrincipales;

  const describirIntensidad = (nivel: number) => {
    if (nivel >= 5) return "Muy Alta";
    if (nivel === 4) return "Alta y Balanceada";
    if (nivel === 3) return "Media";
    if (nivel === 2) return "Suave";
    return "Delicada";
  };

  return (
    <section class="bg-[#FAF6F0] rounded-2xl p-5 md:p-6 border border-[#E5D5C5] space-y-6">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#E5D5C5] pb-3">
        <div>
          <span class="text-[11px] font-extrabold uppercase tracking-widest text-[#2C4234]">
            Laboratorio de Catación SCA
          </span>
          <h3 class="text-lg font-extrabold text-[#232323]">
            Perfil Sensorial y Rueda de Sabores
          </h3>
        </div>
        <span class="text-xs font-bold bg-white border border-[#E5D5C5] text-[#54121B] px-3 py-1 rounded-full">
          Tueste: {perfil.nivelTueste}
        </span>
      </div>

      <div>
        <span class="block text-xs font-bold uppercase tracking-wider text-stone-500 mb-2.5">
          Descriptores Aromáticos en Taza
        </span>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          {descriptores.map((nota) => {
            const estilo = obtenerCategoriaDescriptor(nota);
            return (
              <div
                key={nota}
                class={`flex items-center gap-3 p-3 rounded-xl border ${estilo.colorFondo} ${estilo.colorBorde}`}
              >
                <span
                  class={`w-8 h-8 rounded-lg flex items-center justify-center bg-white/80 border ${estilo.colorBorde} ${estilo.colorTexto} shrink-0`}
                  aria-hidden="true"
                >
                  <svg
                    class="w-4 h-4"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2.2"
                  >
                    <path d="M17 8h1a4 4 0 1 1 0 8h-1" />
                    <path d="M3 8h14v9a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4Z" />
                    <line x1="6" y1="2" x2="6" y2="4" />
                    <line x1="10" y1="2" x2="10" y2="4" />
                    <line x1="14" y1="2" x2="14" y2="4" />
                  </svg>
                </span>
                <div>
                  <span class={`block font-extrabold text-sm ${estilo.colorTexto}`}>
                    {nota}
                  </span>
                  <span class="block text-[11px] font-semibold text-stone-500">
                    Familia: {estilo.familia}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div class="space-y-4 bg-white p-4 rounded-xl border border-[#E5D5C5]">
        <BarraAtributoSensorial
          etiqueta="Acidez"
          valor={perfil.acidez}
          descripcionNivel={describirIntensidad(perfil.acidez)}
        />
        <BarraAtributoSensorial
          etiqueta="Cuerpo"
          valor={perfil.cuerpo}
          descripcionNivel={describirIntensidad(perfil.cuerpo)}
        />
        <BarraAtributoSensorial
          etiqueta="Dulzura"
          valor={perfil.dulzura}
          descripcionNivel={describirIntensidad(perfil.dulzura)}
        />
      </div>

      <div>
        <span class="block text-xs font-bold uppercase tracking-wider text-stone-500 mb-2">
          Curva de Nivel de Tueste
        </span>
        <div class="grid grid-cols-4 gap-2">
          {NIVELES_TUESTE.map((nivel) => {
            const esActivo = perfil.nivelTueste === nivel;
            return (
              <div
                key={nivel}
                class={`text-center py-2 px-2 rounded-xl text-xs font-extrabold border transition-all ${
                  esActivo
                    ? "bg-[#54121B] text-white border-[#54121B] shadow-xs"
                    : "bg-white text-stone-500 border-stone-200"
                }`}
              >
                {nivel}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
