import { useState } from "preact/hooks";
import { ItemCanasta } from "./CanastaCompra.tsx";

export type PresentacionSeleccionable =
  | "250g"
  | "500g"
  | "1000g"
  | "arroba"
  | "carga";

export type MoliendaSeleccionable =
  | "Grano entero"
  | "Moka / Italiana"
  | "Filtro / Goteo (V60 / Chemex)"
  | "Prensa Francesa"
  | "Espresso";

export type FrecuenciaSeleccionable = "semanal" | "quincenal" | "mensual";

interface PropiedadesConfiguradorProducto {
  loteId: string;
  nombreLote: string;
  nombreFinca: string;
  municipio: string;
  precioLibraCop: number;
  precioArrobaCop?: number;
  precioCargaCop?: number;
  stockDisponibleKg: number;
  urlBaseApi: string;
}

const OPCIONES_MOLIENDA: Array<{
  valor: MoliendaSeleccionable;
  etiqueta: string;
  detalle: string;
}> = [
  {
    valor: "Grano entero",
    etiqueta: "Grano entero",
    detalle: "Máxima conservación de aromas",
  },
  {
    valor: "Filtro / Goteo (V60 / Chemex)",
    etiqueta: "Filtro / Goteo",
    detalle: "Molienda media para V60, Chemex o cafetera",
  },
  {
    valor: "Prensa Francesa",
    etiqueta: "Prensa Francesa",
    detalle: "Molienda gruesa uniforme",
  },
  {
    valor: "Moka / Italiana",
    etiqueta: "Moka / Italiana",
    detalle: "Molienda media-fina",
  },
  {
    valor: "Espresso",
    etiqueta: "Espresso",
    detalle: "Molienda fina para máquina de presión",
  },
];

const EQUIVALENCIA_KG: Record<PresentacionSeleccionable, number> = {
  "250g": 0.25,
  "500g": 0.5,
  "1000g": 1.0,
  arroba: 12.5,
  carga: 125.0,
};

export default function ConfiguradorProducto({
  loteId,
  nombreLote,
  nombreFinca,
  municipio,
  precioLibraCop,
  precioArrobaCop,
  precioCargaCop,
  stockDisponibleKg,
  urlBaseApi,
}: PropiedadesConfiguradorProducto) {
  const [presentacion, setPresentacion] = useState<PresentacionSeleccionable>(
    "500g",
  );
  const [molienda, setMolienda] = useState<MoliendaSeleccionable>(
    "Grano entero",
  );
  const [modalidadCompra, setModalidadCompra] = useState<
    "unica" | "suscripcion"
  >("unica");
  const [frecuenciaSuscripcion, setFrecuenciaSuscripcion] = useState<
    FrecuenciaSeleccionable
  >("mensual");
  const [cantidad, setCantidad] = useState(1);
  const [mensajeConfirmacionLocal, setMensajeConfirmacionLocal] = useState<
    string | null
  >(null);

  const valorArrobaBase = precioArrobaCop ??
    Math.round(precioLibraCop * 25 * 0.92);
  const valorCargaBase = precioCargaCop ??
    Math.round(precioLibraCop * 250 * 0.85);

  const calcularPrecioBasePresentacion = (
    pres: PresentacionSeleccionable,
  ): number => {
    if (pres === "250g") return Math.round(precioLibraCop * 0.55);
    if (pres === "500g") return precioLibraCop;
    if (pres === "1000g") return Math.round(precioLibraCop * 1.9);
    if (pres === "arroba") return valorArrobaBase;
    return valorCargaBase;
  };

  const precioUnitarioSinDescuento = calcularPrecioBasePresentacion(
    presentacion,
  );
  const precioUnitarioFinal = modalidadCompra === "suscripcion"
    ? Math.round(precioUnitarioSinDescuento * 0.9)
    : precioUnitarioSinDescuento;

  const ahorroTotalSuscripcion =
    (precioUnitarioSinDescuento - precioUnitarioFinal) * cantidad;
  const pesoTotalRequeridoKg = EQUIVALENCIA_KG[presentacion] * cantidad;
  const totalPagarCop = precioUnitarioFinal * cantidad;

  const agregarAlCarritoConfigurado = () => {
    const nuevoItem: ItemCanasta = {
      loteCafeId: loteId,
      nombreLote,
      nombreFinca,
      municipio,
      unidadVenta: presentacion,
      tipoMolienda: molienda,
      esSuscripcion: modalidadCompra === "suscripcion",
      frecuenciaSuscripcion: modalidadCompra === "suscripcion"
        ? frecuenciaSuscripcion
        : undefined,
      cantidad,
      precioUnitarioCop: precioUnitarioFinal,
    };

    globalThis.dispatchEvent(
      new CustomEvent<ItemCanasta>("maicofi:agregar-canasta", {
        detail: nuevoItem,
      }),
    );

    setMensajeConfirmacionLocal(
      modalidadCompra === "suscripcion"
        ? `Suscripción ${frecuenciaSuscripcion} (${presentacion} • ${molienda}) añadida con 10% de descuento.`
        : `Lote (${presentacion} • ${molienda}) añadido a la canasta.`,
    );
  };

  return (
    <div
      data-url-api={urlBaseApi}
      class="bg-[#FAF6F0] p-6 rounded-2xl border-2 border-[#E5D5C5] space-y-6"
    >
      <div>
        <span class="block text-xs font-extrabold uppercase tracking-wider text-[#2C4234] mb-2.5">
          1. Selecciona la Presentación (Detal o Mayorista)
        </span>
        <div class="grid grid-cols-2 sm:grid-cols-5 gap-2">
          {(
            [
              { id: "250g", titulo: "250 g", subtitulo: "Media libra" },
              { id: "500g", titulo: "500 g", subtitulo: "1 Libra" },
              { id: "1000g", titulo: "1000 g", subtitulo: "1 Kilo (-5%)" },
              { id: "arroba", titulo: "Arroba", subtitulo: "12.5 kg" },
              { id: "carga", titulo: "Carga", subtitulo: "125 kg" },
            ] as const
          ).map((opcion) => {
            const activo = presentacion === opcion.id;
            return (
              <button
                type="button"
                key={opcion.id}
                onClick={() => setPresentacion(opcion.id)}
                class={`p-3 rounded-xl border-2 text-left transition-all ${
                  activo
                    ? "bg-[#54121B] text-white border-[#54121B] shadow-xs"
                    : "bg-white text-[#232323] border-stone-300 hover:border-[#54121B]"
                }`}
              >
                <span class="block font-extrabold text-sm">
                  {opcion.titulo}
                </span>
                <span
                  class={`block text-[11px] ${
                    activo ? "text-stone-200" : "text-stone-500"
                  }`}
                >
                  {opcion.subtitulo}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      <div>
        <span class="block text-xs font-extrabold uppercase tracking-wider text-[#2C4234] mb-2.5">
          2. Selecciona el Tipo de Molienda
        </span>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
          {OPCIONES_MOLIENDA.map((op) => {
            const activo = molienda === op.valor;
            return (
              <button
                type="button"
                key={op.valor}
                onClick={() => setMolienda(op.valor)}
                class={`p-3 rounded-xl border-2 text-left transition-all ${
                  activo
                    ? "bg-[#2C4234] text-white border-[#2C4234] shadow-xs"
                    : "bg-white text-[#232323] border-stone-300 hover:border-[#2C4234]"
                }`}
              >
                <span class="block font-bold text-xs">{op.etiqueta}</span>
                <span
                  class={`block text-[11px] mt-0.5 ${
                    activo ? "text-stone-200" : "text-stone-500"
                  }`}
                >
                  {op.detalle}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      <div>
        <span class="block text-xs font-extrabold uppercase tracking-wider text-[#2C4234] mb-2.5">
          3. Modalidad de Compra
        </span>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <button
            type="button"
            onClick={() => setModalidadCompra("unica")}
            class={`p-3.5 rounded-xl border-2 text-left transition-all ${
              modalidadCompra === "unica"
                ? "bg-white border-[#232323] ring-2 ring-[#232323]/10"
                : "bg-white/60 border-stone-300 text-stone-600"
            }`}
          >
            <div class="flex items-center justify-between">
              <span class="font-extrabold text-sm text-[#232323]">
                Compra Única
              </span>
              <span class="text-xs font-bold text-stone-600">
                ${precioUnitarioSinDescuento.toLocaleString("es-CO")} / u
              </span>
            </div>
            <p class="text-[11px] text-stone-500 mt-1">
              Despacho inmediato desde la finca en el Tolima.
            </p>
          </button>

          <button
            type="button"
            onClick={() => setModalidadCompra("suscripcion")}
            class={`p-3.5 rounded-xl border-2 text-left transition-all ${
              modalidadCompra === "suscripcion"
                ? "bg-white border-[#54121B] ring-2 ring-[#54121B]/20"
                : "bg-white/60 border-stone-300 text-stone-600"
            }`}
          >
            <div class="flex items-center justify-between">
              <span class="font-extrabold text-sm text-[#54121B]">
                Suscripción (-10%)
              </span>
              <span class="text-xs font-extrabold bg-[#54121B] text-white px-2 py-0.5 rounded-full">
                ${Math.round(precioUnitarioSinDescuento * 0.9).toLocaleString("es-CO")} / u
              </span>
            </div>
            <p class="text-[11px] text-stone-500 mt-1">
              Café recién tostado recurrente con 10% de descuento fijo.
            </p>
          </button>
        </div>

        {modalidadCompra === "suscripcion" && (
          <div class="mt-3 bg-white p-3.5 rounded-xl border border-[#E5D5C5] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <span class="text-xs font-bold text-[#232323]">
              Frecuencia de entrega programada:
            </span>
            <div class="grid grid-cols-3 gap-2">
              {(["semanal", "quincenal", "mensual"] as const).map((frec) => (
                <button
                  type="button"
                  key={frec}
                  onClick={() => setFrecuenciaSuscripcion(frec)}
                  class={`px-3 py-1.5 rounded-lg text-xs font-bold capitalize border ${
                    frecuenciaSuscripcion === frec
                      ? "bg-[#54121B] text-white border-[#54121B]"
                      : "bg-[#FAF6F0] text-stone-700 border-stone-300"
                  }`}
                >
                  {frec}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-3 border-t border-[#E5D5C5]">
        <div>
          <label class="block text-xs font-bold text-stone-600 mb-1">
            Cantidad ({pesoTotalRequeridoKg.toFixed(2)} kg totales)
          </label>
          <div class="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setCantidad((c) => Math.max(1, c - 1))}
              class="w-10 h-10 rounded-xl bg-white border border-stone-300 font-extrabold text-lg"
            >
              -
            </button>
            <span class="w-10 text-center font-extrabold text-lg">
              {cantidad}
            </span>
            <button
              type="button"
              onClick={() => setCantidad((c) => c + 1)}
              class="w-10 h-10 rounded-xl bg-white border border-stone-300 font-extrabold text-lg"
            >
              +
            </button>
          </div>
        </div>

        <div class="text-right">
          {modalidadCompra === "suscripcion" && (
            <span class="block text-xs font-bold text-emerald-800">
              Ahorras ${ahorroTotalSuscripcion.toLocaleString("es-CO")} COP por entrega (-10%)
            </span>
          )}
          <span class="block text-xs text-stone-500">
            Disponible en finca: {stockDisponibleKg} kg
          </span>
          <span class="text-2xl font-extrabold text-[#232323]">
            ${totalPagarCop.toLocaleString("es-CO")} COP
          </span>
        </div>
      </div>

      {mensajeConfirmacionLocal && (
        <div class="p-3 bg-emerald-50 border border-emerald-300 text-emerald-900 rounded-xl text-xs font-bold">
          {mensajeConfirmacionLocal}
        </div>
      )}

      <button
        type="button"
        onClick={agregarAlCarritoConfigurado}
        disabled={pesoTotalRequeridoKg > stockDisponibleKg}
        class="w-full min-h-[52px] bg-[#2C4234] hover:bg-[#54121B] text-white font-extrabold text-base rounded-xl shadow-md transition-colors disabled:opacity-50"
      >
        {pesoTotalRequeridoKg > stockDisponibleKg
          ? "La cantidad supera el stock disponible del lote"
          : modalidadCompra === "suscripcion"
          ? `Añadir Suscripción ${frecuenciaSuscripcion.toUpperCase()} (-10%) a la Canasta`
          : "Añadir Lote Personalizado a la Canasta"}
      </button>
    </div>
  );
}
