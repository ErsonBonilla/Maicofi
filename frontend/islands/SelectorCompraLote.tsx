import { useState } from "preact/hooks";
import { ItemCanasta } from "./CanastaCompra.tsx";

interface PropiedadesSelectorCompraLote {
  loteId: string;
  nombreLote: string;
  nombreFinca: string;
  municipio: string;
  precioLibraCop: number;
  precioArrobaCop?: number;
  precioCargaCop?: number;
  stockDisponibleKg: number;
}

export default function SelectorCompraLote({
  loteId,
  nombreLote,
  nombreFinca,
  municipio,
  precioLibraCop,
  precioArrobaCop,
  precioCargaCop,
  stockDisponibleKg,
}: PropiedadesSelectorCompraLote) {
  const [unidadSeleccionada, setUnidadSeleccionada] = useState<
    "libra" | "arroba" | "carga"
  >("libra");
  const [cantidad, setCantidad] = useState(1);

  const valorArroba = precioArrobaCop ?? Math.round(precioLibraCop * 25 * 0.92);
  const valorCarga = precioCargaCop ?? Math.round(precioLibraCop * 250 * 0.85);

  const precioUnitarioActual = unidadSeleccionada === "libra"
    ? precioLibraCop
    : unidadSeleccionada === "arroba"
    ? valorArroba
    : valorCarga;

  const pesoEquivalenteKg = unidadSeleccionada === "libra"
    ? cantidad * 0.5
    : unidadSeleccionada === "arroba"
    ? cantidad * 12.5
    : cantidad * 125;

  const agregarALaCanasta = () => {
    const detalle: ItemCanasta = {
      loteCafeId: loteId,
      nombreLote,
      nombreFinca,
      municipio,
      unidadVenta: unidadSeleccionada,
      cantidad,
      precioUnitarioCop: precioUnitarioActual,
    };

    globalThis.dispatchEvent(
      new CustomEvent<ItemCanasta>("maicofi:agregar-canasta", {
        detail: detalle,
      }),
    );
  };

  return (
    <div class="bg-[#FAF6F0] p-6 rounded-2xl border-2 border-[#E5D5C5] space-y-5">
      <div>
        <span class="block text-xs font-bold uppercase tracking-wider text-[#2C4234] mb-2">
          1. Selecciona la escala de compra
        </span>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
          <button
            type="button"
            onClick={() => setUnidadSeleccionada("libra")}
            class={`p-3 rounded-xl border-2 text-left transition-all ${
              unidadSeleccionada === "libra"
                ? "bg-[#54121B] text-white border-[#54121B]"
                : "bg-white text-[#232323] border-stone-300"
            }`}
          >
            <span class="block font-extrabold text-sm">Libra (500 g)</span>
            <span class="block text-xs opacity-90">
              ${precioLibraCop.toLocaleString("es-CO")} COP
            </span>
          </button>

          <button
            type="button"
            onClick={() => setUnidadSeleccionada("arroba")}
            class={`p-3 rounded-xl border-2 text-left transition-all ${
              unidadSeleccionada === "arroba"
                ? "bg-[#54121B] text-white border-[#54121B]"
                : "bg-white text-[#232323] border-stone-300"
            }`}
          >
            <span class="block font-extrabold text-sm">Arroba (12.5 kg)</span>
            <span class="block text-xs opacity-90">
              ${valorArroba.toLocaleString("es-CO")} COP
            </span>
          </button>

          <button
            type="button"
            onClick={() => setUnidadSeleccionada("carga")}
            class={`p-3 rounded-xl border-2 text-left transition-all ${
              unidadSeleccionada === "carga"
                ? "bg-[#54121B] text-white border-[#54121B]"
                : "bg-white text-[#232323] border-stone-300"
            }`}
          >
            <span class="block font-extrabold text-sm">Carga (125 kg)</span>
            <span class="block text-xs opacity-90">
              ${valorCarga.toLocaleString("es-CO")} COP
            </span>
          </button>
        </div>
      </div>

      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2 border-t border-[#E5D5C5]">
        <div>
          <label class="block text-xs font-bold text-stone-600 mb-1">
            Cantidad de {unidadSeleccionada}s ({pesoEquivalenteKg} kg en total)
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
          <span class="block text-xs text-stone-500">
            Subtotal ({stockDisponibleKg} kg disponibles en finca)
          </span>
          <span class="text-2xl font-extrabold text-[#232323]">
            ${(precioUnitarioActual * cantidad).toLocaleString("es-CO")} COP
          </span>
        </div>
      </div>

      <button
        type="button"
        onClick={agregarALaCanasta}
        disabled={pesoEquivalenteKg > stockDisponibleKg}
        class="w-full min-h-[52px] bg-[#2C4234] hover:bg-[#54121B] text-white font-extrabold text-base rounded-xl shadow-md transition-colors disabled:opacity-50"
      >
        {pesoEquivalenteKg > stockDisponibleKg
          ? "Cantidad supera el stock disponible del lote"
          : "Agregar Lote a la Canasta"}
      </button>
    </div>
  );
}
