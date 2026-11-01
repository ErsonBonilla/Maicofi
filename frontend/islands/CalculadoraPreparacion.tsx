import { useState } from "preact/hooks";

interface MetodoExtraccion {
  id: string;
  nombre: string;
  ratioAguaPorGramo: number;
  mililitrosPorTaza: number;
  temperaturaIdealC: number;
  moliendaRecomendada: string;
  tiempoExtraccion: string;
  instruccionClave: string;
}

const METODOS_PREPARACION: MetodoExtraccion[] = [
  {
    id: "v60",
    nombre: "V60 / Filtro Cono",
    ratioAguaPorGramo: 16,
    mililitrosPorTaza: 160,
    temperaturaIdealC: 92,
    moliendaRecomendada: "Media-Fina (textura sal de mesa)",
    tiempoExtraccion: "2:30 - 3:00 min",
    instruccionClave:
      "Realiza una preinfusión (bloom) de 30 segundos con el doble de agua que el peso del café antes de verter en espiral.",
  },
  {
    id: "chemex",
    nombre: "Chemex",
    ratioAguaPorGramo: 15,
    mililitrosPorTaza: 180,
    temperaturaIdealC: 93,
    moliendaRecomendada: "Media-Gruesa",
    tiempoExtraccion: "3:30 - 4:15 min",
    instruccionClave:
      "Enjuaga previamente el filtro de papel grueso con agua caliente para eliminar sabores residuales y precalentar la jarra.",
  },
  {
    id: "prensa",
    nombre: "Prensa Francesa",
    ratioAguaPorGramo: 12,
    mililitrosPorTaza: 160,
    temperaturaIdealC: 94,
    moliendaRecomendada: "Gruesa uniforme",
    tiempoExtraccion: "4:00 min",
    instruccionClave:
      "Deja reposar 4 minutos, rompe suavemente la costra superior con cuchara de madera y baja el émbolo sin presionar el fondo.",
  },
  {
    id: "aeropress",
    nombre: "AeroPress",
    ratioAguaPorGramo: 14,
    mililitrosPorTaza: 150,
    temperaturaIdealC: 90,
    moliendaRecomendada: "Media-Fina",
    tiempoExtraccion: "1:45 - 2:00 min",
    instruccionClave:
      "Agita suavemente durante 10 segundos tras agregar el agua y presiona de manera constante durante 30 segundos.",
  },
  {
    id: "moka",
    nombre: "Moka Italiana",
    ratioAguaPorGramo: 10,
    mililitrosPorTaza: 90,
    temperaturaIdealC: 95,
    moliendaRecomendada: "Fina-Media (sin compactar)",
    tiempoExtraccion: "3:00 min a fuego bajo",
    instruccionClave:
      "Llena la base con agua previamente caliente hasta justo debajo de la válvula de seguridad y retira del fuego al primer burbujeo.",
  },
  {
    id: "espresso",
    nombre: "Espresso",
    ratioAguaPorGramo: 2,
    mililitrosPorTaza: 36,
    temperaturaIdealC: 93,
    moliendaRecomendada: "Fina calibrada",
    tiempoExtraccion: "26 - 30 seg (9 bares)",
    instruccionClave:
      "Compacta (tamp) de forma nivelada a 15 kg de presión buscando una extracción sedosa tipo miel.",
  },
];

interface PropiedadesCalculadoraPreparacion {
  nombreLote?: string;
  nivelTueste?: string;
}

export default function CalculadoraPreparacion({
  nombreLote,
  nivelTueste = "Medio",
}: PropiedadesCalculadoraPreparacion) {
  const [metodoId, setMetodoId] = useState<string>("v60");
  const [cantidadTazas, setCantidadTazas] = useState<number>(2);

  const metodoActual =
    METODOS_PREPARACION.find((m) => m.id === metodoId) ??
    METODOS_PREPARACION[0];

  const ajusteTemperaturaTueste = nivelTueste === "Claro"
    ? 1
    : nivelTueste === "Oscuro"
    ? -2
    : 0;

  const temperaturaSugeridaC =
    metodoActual.temperaturaIdealC + ajusteTemperaturaTueste;
  const aguaTotalMl = metodoActual.mililitrosPorTaza * cantidadTazas;
  const gramosCafeRequeridos = Number(
    (aguaTotalMl / metodoActual.ratioAguaPorGramo).toFixed(1),
  );
  const aguaPreinfusionMl = Math.round(gramosCafeRequeridos * 2);

  return (
    <section class="bg-white rounded-3xl p-6 md:p-8 border border-[#E5D5C5] shadow-xs space-y-6">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-stone-200 pb-4">
        <div>
          <span class="text-xs font-extrabold uppercase tracking-widest text-[#2C4234]">
            Guía de Barismo en Casa
          </span>
          <h2 class="text-xl md:text-2xl font-extrabold text-[#232323]">
            Calculadora Interactiva de Preparación
          </h2>
          {nombreLote && (
            <p class="text-xs text-stone-600 mt-0.5">
              Receta calibrada para <strong>{nombreLote}</strong> (Tueste {nivelTueste})
            </p>
          )}
        </div>

        <span class="text-xs font-extrabold bg-[#FAF6F0] border border-[#E5D5C5] text-[#54121B] px-3.5 py-1.5 rounded-full self-start md:self-center">
          Ratio Oficial 1:{metodoActual.ratioAguaPorGramo}
        </span>
      </div>

      <div>
        <label class="block text-xs font-extrabold uppercase tracking-wider text-stone-500 mb-2.5">
          1. Elige tu método de extracción favorito
        </label>
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
          {METODOS_PREPARACION.map((m) => {
            const seleccionado = m.id === metodoId;
            return (
              <button
                type="button"
                key={m.id}
                onClick={() => setMetodoId(m.id)}
                class={`p-3 rounded-xl border-2 text-left transition-all ${
                  seleccionado
                    ? "bg-[#2C4234] text-white border-[#2C4234] shadow-xs"
                    : "bg-[#FAF6F0] text-[#232323] border-stone-300 hover:border-[#2C4234]"
                }`}
              >
                <span class="block font-extrabold text-xs">{m.nombre}</span>
                <span
                  class={`block text-[11px] mt-0.5 ${
                    seleccionado ? "text-stone-200" : "text-stone-500"
                  }`}
                >
                  Ratio 1:{m.ratioAguaPorGramo}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      <div class="bg-[#FAF6F0] p-4 rounded-2xl border border-[#E5D5C5] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <label class="block text-sm font-extrabold text-[#232323]">
            2. ¿Cuántas tazas deseas preparar?
          </label>
          <span class="text-xs text-stone-500">
            Base de {metodoActual.mililitrosPorTaza} ml por taza en {metodoActual.nombre}
          </span>
        </div>

        <div class="flex items-center gap-2">
          {[1, 2, 3, 4, 6, 8].map((num) => (
            <button
              type="button"
              key={num}
              onClick={() => setCantidadTazas(num)}
              class={`w-10 h-10 rounded-xl font-extrabold text-sm border-2 transition-all ${
                cantidadTazas === num
                  ? "bg-[#54121B] text-white border-[#54121B]"
                  : "bg-white text-[#232323] border-stone-300 hover:border-[#54121B]"
              }`}
            >
              {num}
            </button>
          ))}
        </div>
      </div>

      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div class="bg-[#FAF6F0] p-4 rounded-2xl border border-[#E5D5C5]">
          <span class="block text-xs font-bold text-stone-500">
            Café Molido Requerido
          </span>
          <span class="text-2xl font-extrabold text-[#54121B] mt-1 block">
            {gramosCafeRequeridos} g
          </span>
          <span class="text-[11px] text-stone-500">
            ~{Math.max(1, Math.round(gramosCafeRequeridos / 7))} cucharadas soperas
          </span>
        </div>

        <div class="bg-[#FAF6F0] p-4 rounded-2xl border border-[#E5D5C5]">
          <span class="block text-xs font-bold text-stone-500">
            Agua Total Filtrada
          </span>
          <span class="text-2xl font-extrabold text-[#2C4234] mt-1 block">
            {aguaTotalMl} ml
          </span>
          <span class="text-[11px] text-stone-500">
            Preinfusión: {aguaPreinfusionMl} ml (30 s)
          </span>
        </div>

        <div class="bg-[#FAF6F0] p-4 rounded-2xl border border-[#E5D5C5]">
          <span class="block text-xs font-bold text-stone-500">
            Temperatura Ideal
          </span>
          <span class="text-2xl font-extrabold text-[#232323] mt-1 block">
            {temperaturaSugeridaC} °C
          </span>
          <span class="text-[11px] text-stone-500">
            Ajustada a tueste {nivelTueste.toLowerCase()}
          </span>
        </div>

        <div class="bg-[#FAF6F0] p-4 rounded-2xl border border-[#E5D5C5]">
          <span class="block text-xs font-bold text-stone-500">
            Tiempo de Infusión
          </span>
          <span class="text-lg font-extrabold text-[#232323] mt-1 block">
            {metodoActual.tiempoExtraccion}
          </span>
          <span class="text-[11px] text-stone-500">
            {metodoActual.moliendaRecomendada}
          </span>
        </div>
      </div>

      <div class="bg-stone-50 p-4 rounded-xl border border-stone-200 text-xs text-stone-700 leading-relaxed">
        <strong class="text-[#232323]">Consejo del Maestro Tostador: </strong>
        {metodoActual.instruccionClave}
      </div>
    </section>
  );
}
