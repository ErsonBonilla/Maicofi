import { useState } from "preact/hooks";
import SubidorImagen from "./SubidorImagen.tsx";

interface PropiedadesFormularioCaficultor {
  urlBaseApi: string;
  tokenAutenticacion?: string;
}

const VARIEDADES_TOLIMA = [
  "Castillo",
  "Caturra",
  "Tabi",
  "Colombia",
  "Geisha",
  "Bourbon Rosado",
  "Típica",
  "Catuaí",
];

const MUNICIPIOS_TOLIMA = [
  "Planadas",
  "Líbano",
  "Santa Isabel",
  "Anzoátegui",
  "Herrera (Rioblanco)",
  "Ibagué",
  "Chaparral",
  "Ataco",
  "Fresno",
  "Roncesvalles",
  "Ortega",
  "Cajamarca",
];

const PROCESOS_BENEFICIO = [
  {
    id: "Lavado",
    titulo: "Lavado Tradicional",
    descripcion: "Fermentado en pila y lavado con agua limpia de montaña",
  },
  {
    id: "Natural",
    titulo: "Natural en Marquesina",
    descripcion: "Secado al sol con la cereza madura completa",
  },
  {
    id: "Honey",
    titulo: "Honey / Enmielado",
    descripcion: "Secado lento conservando el mucílago dulce del grano",
  },
  {
    id: "Fermentación Anaeróbica",
    titulo: "Fermentación Anaeróbica",
    descripcion: "Fermentación controlada en biorreactor o tanque sellado",
  },
];

export default function FormularioCaficultor({
  urlBaseApi,
  tokenAutenticacion,
}: PropiedadesFormularioCaficultor) {
  const [pestanaActiva, setPestanaActiva] = useState<"lote" | "finca">("lote");

  const [tokenMemoria, setTokenMemoria] = useState<string>(
    tokenAutenticacion ?? "",
  );
  const [nombreCaficultorActivo, setNombreCaficultorActivo] = useState<string>(
    "",
  );
  const [identificadorAcceso, setIdentificadorAcceso] = useState("");
  const [contrasenaAcceso, setContrasenaAcceso] = useState("");
  const [autenticando, setAutenticando] = useState(false);

  const [nombreLote, setNombreLote] = useState("");
  const [variedadSeleccionada, setVariedadSeleccionada] = useState("Castillo");
  const [procesoSeleccionado, setProcesoSeleccionado] = useState("Lavado");
  const [estadoPresentacion, setEstadoPresentacion] = useState(
    "Café Pergamino Seco",
  );
  const [puntajeSca, setPuntajeSca] = useState("85.5");
  const [notasCataTexto, setNotasCataTexto] = useState(
    "Panela, Chocolate, Cítrico Naranja",
  );
  const [humedadPorcentaje, setHumedadPorcentaje] = useState("11.0");
  const [precioLibraCop, setPrecioLibraCop] = useState("34000");
  const [unidadInventario, setUnidadInventario] = useState<
    "arrobas" | "cargas" | "kilos"
  >("arrobas");
  const [cantidadInventario, setCantidadInventario] = useState("12");
  const [urlFotoLote, setUrlFotoLote] = useState("");

  const [nombreFinca, setNombreFinca] = useState("Finca El Mirador del Nevado");
  const [municipioTolima, setMunicipioTolima] = useState("Planadas");
  const [veredaFinca, setVeredaFinca] = useState("Vereda Gaitania");
  const [alturaMsnm, setAlturaMsnm] = useState("1920");
  const [historiaProductor, setHistoriaProductor] = useState(
    "Familia caficultora del Tolima dedicada al cultivo bajo sombrío nativo y recolección manual de cereza madura.",
  );

  const [enviando, setEnviando] = useState(false);
  const [mensajeEstado, setMensajeEstado] = useState<
    { tipo: "exito" | "error"; texto: string } | null
  >(null);

  const kilosTotalesCalculados = (() => {
    const cantidad = parseFloat(cantidadInventario) || 0;
    if (unidadInventario === "cargas") return cantidad * 125;
    if (unidadInventario === "arrobas") return cantidad * 12.5;
    return cantidad;
  })();

  const precioSugeridoArrobaCop = Math.round(
    (parseFloat(precioLibraCop) || 0) * 25 * 0.92,
  );
  const precioSugeridoCargaCop = Math.round(
    (parseFloat(precioLibraCop) || 0) * 250 * 0.85,
  );

  const iniciarSesionCaficultor = async (evento: Event) => {
    evento.preventDefault();
    setAutenticando(true);
    setMensajeEstado(null);

    try {
      const respuesta = await fetch(`${urlBaseApi}/auth/login`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          identifier: identificadorAcceso.trim(),
          password: contrasenaAcceso,
        }),
      });

      if (!respuesta.ok) {
        const errorJson = await respuesta.json().catch(() => ({}));
        throw new Error(
          errorJson.detail || "Número de celular o contraseña inválidos.",
        );
      }

      const datos = await respuesta.json();
      setTokenMemoria(datos.access_token);
      setNombreCaficultorActivo(datos.full_name);
      setContrasenaAcceso("");
      setMensajeEstado({
        tipo: "exito",
        texto: `Sesión iniciada correctamente como ${datos.full_name}.`,
      });
    } catch (err) {
      setMensajeEstado({
        tipo: "error",
        texto: err instanceof Error
          ? err.message
          : "No fue posible iniciar sesión.",
      });
    } finally {
      setAutenticando(false);
    }
  };

  const activarSesionDemoCaficultor = async () => {
    setAutenticando(true);
    setMensajeEstado(null);

    try {
      const respuesta = await fetch(`${urlBaseApi}/auth/demo-access`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role: "farmer" }),
      });

      if (!respuesta.ok) {
        const errorJson = await respuesta.json().catch(() => ({}));
        throw new Error(
          errorJson.detail || "El acceso demostrativo no está habilitado.",
        );
      }

      const datos = await respuesta.json();
      setTokenMemoria(datos.access_token);
      setNombreCaficultorActivo(datos.full_name);
      setMensajeEstado({
        tipo: "exito",
        texto: `Sesión demostrativa activa: ${datos.full_name} (Planadas, Tolima).`,
      });
    } catch (err) {
      setMensajeEstado({
        tipo: "error",
        texto: err instanceof Error
          ? err.message
          : "Error solicitando acceso demostrativo.",
      });
    } finally {
      setAutenticando(false);
    }
  };

  const manejarPublicacionLote = async (evento: Event) => {
    evento.preventDefault();
    setEnviando(true);
    setMensajeEstado(null);

    try {
      const cuerpoContratoLote = {
        name: nombreLote,
        variety: variedadSeleccionada,
        process: procesoSeleccionado,
        presentation_state: estadoPresentacion,
        sca_score: parseFloat(puntajeSca),
        tasting_notes: notasCataTexto
          .split(",")
          .map((nota) => nota.trim())
          .filter(Boolean),
        humidity_pct: parseFloat(humedadPorcentaje) || 11.0,
        harvest_year: 2026,
        price_per_lb_cop: parseFloat(precioLibraCop),
        price_per_arroba_cop: precioSugeridoArrobaCop,
        price_per_carga_cop: precioSugeridoCargaCop,
        available_stock_kg: kilosTotalesCalculados,
        photos_urls: urlFotoLote.trim() ? [urlFotoLote.trim()] : [],
      };

      const respuesta = await fetch(`${urlBaseApi}/products`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          ...(tokenMemoria ? { Authorization: `Bearer ${tokenMemoria}` } : {}),
        },
        body: JSON.stringify(cuerpoContratoLote),
      });

      if (!respuesta.ok) {
        const errorJson = await respuesta.json().catch(() => ({}));
        throw new Error(
          errorJson.detail || "Debes iniciar sesión como caficultor para publicar.",
        );
      }

      setMensajeEstado({
        tipo: "exito",
        texto:
          "El lote de café fue publicado exitosamente en el catálogo de Maicofi.",
      });
      setNombreLote("");
    } catch (err) {
      setMensajeEstado({
        tipo: "error",
        texto: err instanceof Error
          ? err.message
          : "Error de conexión. Verifica que el backend esté en ejecución.",
      });
    } finally {
      setEnviando(false);
    }
  };

  const manejarGuardadoFinca = async (evento: Event) => {
    evento.preventDefault();
    setEnviando(true);
    setMensajeEstado(null);

    try {
      const cuerpoContratoFinca = {
        farm_name: nombreFinca,
        municipality: municipioTolima,
        vereda: veredaFinca,
        altitude_masl: parseInt(alturaMsnm, 10),
        farmer_story: historiaProductor,
        photos_urls: [],
      };

      const respuesta = await fetch(`${urlBaseApi}/producers/farm`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          ...(tokenMemoria ? { Authorization: `Bearer ${tokenMemoria}` } : {}),
        },
        body: JSON.stringify(cuerpoContratoFinca),
      });

      if (!respuesta.ok) {
        const errorJson = await respuesta.json().catch(() => ({}));
        throw new Error(
          errorJson.detail || "No se pudo actualizar el perfil de la finca.",
        );
      }

      setMensajeEstado({
        tipo: "exito",
        texto:
          "Los datos de tu finca cafetera en el Tolima han sido actualizados correctamente.",
      });
    } catch (err) {
      setMensajeEstado({
        tipo: "error",
        texto: err instanceof Error
          ? err.message
          : "Error de conexión al guardar la finca.",
      });
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div class="bg-white rounded-3xl shadow-lg border-2 border-[#2C4234]/20 p-6 md:p-8 max-w-3xl mx-auto space-y-6">
      <div class="bg-[#FAF6F0] p-4 md:p-5 rounded-2xl border border-[#E5D5C5]">
        {!tokenMemoria ? (
          <form onSubmit={iniciarSesionCaficultor} class="space-y-3">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <span class="text-xs font-extrabold uppercase tracking-wider text-[#54121B]">
                  Acceso Seguro de Productor (Cookie HttpOnly + JWT)
                </span>
                <p class="text-xs text-stone-600">
                  Ingresa con tu número de celular registrado o activa la sesión demostrativa de desarrollo.
                </p>
              </div>
              <button
                type="button"
                disabled={autenticando}
                onClick={activarSesionDemoCaficultor}
                class="bg-white hover:bg-[#2C4234] hover:text-white text-[#2C4234] border-2 border-[#2C4234] font-bold text-xs px-3.5 py-2.5 rounded-xl transition-colors shrink-0"
              >
                Acceso Rápido Demo (Dev)
              </button>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
              <input
                type="text"
                required
                placeholder="Celular (+57...) o correo"
                value={identificadorAcceso}
                onInput={(e) =>
                  setIdentificadorAcceso((e.target as HTMLInputElement).value)}
                class="px-3.5 py-2.5 rounded-xl border border-stone-300 text-sm bg-white"
              />
              <input
                type="password"
                required
                placeholder="Contraseña"
                value={contrasenaAcceso}
                onInput={(e) =>
                  setContrasenaAcceso((e.target as HTMLInputElement).value)}
                class="px-3.5 py-2.5 rounded-xl border border-stone-300 text-sm bg-white"
              />
              <button
                type="submit"
                disabled={autenticando}
                class="bg-[#54121B] hover:bg-[#2C4234] text-white font-bold text-sm py-2.5 px-4 rounded-xl transition-colors"
              >
                {autenticando ? "Verificando..." : "Iniciar Sesión"}
              </button>
            </div>
          </form>
        ) : (
          <div class="flex items-center justify-between">
            <div class="text-sm">
              <span class="text-stone-500">Productor autenticado: </span>
              <strong class="text-[#2C4234]">
                {nombreCaficultorActivo || "Caficultor del Tolima"}
              </strong>
            </div>
            <button
              type="button"
              onClick={async () => {
                await fetch(`${urlBaseApi}/auth/logout`, {
                  method: "POST",
                  credentials: "include",
                }).catch(() => {});
                setTokenMemoria("");
                setNombreCaficultorActivo("");
              }}
              class="text-xs font-bold text-[#54121B] underline"
            >
              Cerrar sesión
            </button>
          </div>
        )}
      </div>

      <div class="grid grid-cols-2 gap-3 bg-[#FAF6F0] p-2 rounded-2xl border border-[#E5D5C5]">
        <button
          type="button"
          onClick={() => {
            setPestanaActiva("lote");
            setMensajeEstado(null);
          }}
          class={`min-h-[48px] rounded-xl font-extrabold text-sm sm:text-base transition-all ${
            pestanaActiva === "lote"
              ? "bg-[#54121B] text-white shadow-md"
              : "text-[#232323] hover:bg-white/60"
          }`}
        >
          1. Publicar Lote de Cosecha
        </button>
        <button
          type="button"
          onClick={() => {
            setPestanaActiva("finca");
            setMensajeEstado(null);
          }}
          class={`min-h-[48px] rounded-xl font-extrabold text-sm sm:text-base transition-all ${
            pestanaActiva === "finca"
              ? "bg-[#2C4234] text-white shadow-md"
              : "text-[#232323] hover:bg-white/60"
          }`}
        >
          2. Perfil de Mi Finca
        </button>
      </div>

      {pestanaActiva === "lote" ? (
        <form onSubmit={manejarPublicacionLote} class="space-y-6">
          <div class="border-b border-stone-200 pb-4">
            <h2 class="text-2xl font-extrabold text-[#232323]">
              Registrar Lote de Café Especial
            </h2>
            <p class="text-sm text-stone-600 mt-1">
              Ingresa los datos de tu cosecha en términos cafeteros locales. El sistema calcula automáticamente el peso en kilos y los precios sugeridos por arroba y carga.
            </p>
          </div>

          <div>
            <label class="block text-base font-bold text-[#232323] mb-1">
              1. Nombre o identificación del lote
            </label>
            <input
              type="text"
              required
              maxLength={150}
              placeholder="Ej: Lote La Loma - Cosecha Principal"
              value={nombreLote}
              onInput={(e) => setNombreLote((e.target as HTMLInputElement).value)}
              class="w-full text-base px-4 py-3.5 rounded-xl border-2 border-stone-300 focus:border-[#2C4234] outline-none"
            />
          </div>

          <div>
            <label class="block text-base font-bold text-[#232323] mb-2">
              2. Variedad de café sembrada
            </label>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              {VARIEDADES_TOLIMA.map((variedad) => (
                <button
                  type="button"
                  key={variedad}
                  onClick={() => setVariedadSeleccionada(variedad)}
                  class={`min-h-[48px] px-3 py-2.5 rounded-xl font-bold text-sm border-2 transition-all ${
                    variedadSeleccionada === variedad
                      ? "bg-[#2C4234] text-white border-[#2C4234] shadow-sm"
                      : "bg-[#FAF6F0] text-[#232323] border-stone-300 hover:border-[#2C4234]"
                  }`}
                >
                  {variedad}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label class="block text-base font-bold text-[#232323] mb-2">
              3. Tipo de Beneficio / Proceso
            </label>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {PROCESOS_BENEFICIO.map((proc) => (
                <button
                  type="button"
                  key={proc.id}
                  onClick={() => setProcesoSeleccionado(proc.id)}
                  class={`text-left p-4 rounded-xl border-2 transition-all ${
                    procesoSeleccionado === proc.id
                      ? "bg-[#54121B] text-white border-[#54121B]"
                      : "bg-white text-[#232323] border-stone-300 hover:border-[#54121B]"
                  }`}
                >
                  <div class="font-bold text-base">{proc.titulo}</div>
                  <div
                    class={`text-xs mt-1 ${
                      procesoSeleccionado === proc.id
                        ? "text-stone-200"
                        : "text-stone-500"
                    }`}
                  >
                    {proc.descripcion}
                  </div>
                </button>
              ))}
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label class="block text-sm font-bold text-[#232323] mb-1">
                4. Presentación del Grano
              </label>
              <select
                value={estadoPresentacion}
                onChange={(e) =>
                  setEstadoPresentacion((e.target as HTMLSelectElement).value)}
                class="w-full min-h-[48px] px-3.5 py-3 rounded-xl border-2 border-stone-300 bg-white font-semibold text-sm"
              >
                <option value="Café Pergamino Seco">
                  Café Pergamino Seco (CPS)
                </option>
                <option value="Excelso Verde Trillado">
                  Excelso Verde Trillado
                </option>
                <option value="Tostado en Grano">Tostado en Grano</option>
                <option value="Tostado Molido">Tostado Molido</option>
              </select>
            </div>

            <div>
              <label class="block text-sm font-bold text-[#232323] mb-1">
                5. Puntaje en Taza SCA (80 - 100)
              </label>
              <input
                type="number"
                step="0.25"
                min="80"
                max="100"
                value={puntajeSca}
                onInput={(e) =>
                  setPuntajeSca((e.target as HTMLInputElement).value)}
                class="w-full min-h-[48px] px-4 py-3 rounded-xl border-2 border-stone-300 font-extrabold text-lg"
              />
            </div>

            <div>
              <label class="block text-sm font-bold text-[#232323] mb-1">
                6. Humedad del Grano (%)
              </label>
              <input
                type="number"
                step="0.1"
                min="9.0"
                max="13.5"
                value={humedadPorcentaje}
                onInput={(e) =>
                  setHumedadPorcentaje((e.target as HTMLInputElement).value)}
                class="w-full min-h-[48px] px-4 py-3 rounded-xl border-2 border-stone-300 font-bold text-lg"
              />
            </div>
          </div>

          <div class="bg-[#FAF6F0] p-5 rounded-2xl border border-[#E5D5C5]">
            <label class="block text-base font-bold text-[#232323] mb-2">
              7. Cantidad disponible en la finca
            </label>
            <div class="flex flex-col sm:flex-row gap-3">
              <input
                type="number"
                min="1"
                step="0.5"
                value={cantidadInventario}
                onInput={(e) =>
                  setCantidadInventario((e.target as HTMLInputElement).value)}
                class="sm:w-1/2 min-h-[48px] px-4 py-3 rounded-xl border-2 border-stone-300 font-extrabold text-xl bg-white"
              />
              <div class="grid grid-cols-3 gap-2 sm:w-1/2">
                {(["arrobas", "cargas", "kilos"] as const).map((unidad) => (
                  <button
                    type="button"
                    key={unidad}
                    onClick={() => setUnidadInventario(unidad)}
                    class={`min-h-[48px] rounded-xl font-bold capitalize border-2 ${
                      unidadInventario === unidad
                        ? "bg-[#2C4234] text-white border-[#2C4234]"
                        : "bg-white text-stone-700 border-stone-300"
                    }`}
                  >
                    {unidad}
                  </button>
                ))}
              </div>
            </div>
            <p class="text-xs text-[#2C4234] font-bold mt-2.5">
              Equivalencia en inventario: {kilosTotalesCalculados.toFixed(1)} kg
              ({(kilosTotalesCalculados * 2).toFixed(0)} libras disponibles para la venta).
            </p>
          </div>

          <div class="bg-stone-50 p-5 rounded-2xl border border-stone-200">
            <label class="block text-base font-bold text-[#232323] mb-1">
              8. Precio por Libra (500 g) en Pesos Colombianos (COP)
            </label>
            <input
              type="number"
              step="500"
              min="5000"
              max="500000"
              value={precioLibraCop}
              onInput={(e) =>
                setPrecioLibraCop((e.target as HTMLInputElement).value)}
              class="w-full min-h-[48px] px-4 py-3 rounded-xl border-2 border-stone-300 font-extrabold text-xl bg-white"
            />
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-3 text-xs bg-white p-3.5 rounded-xl border border-stone-200">
              <div>
                <span class="text-stone-500 block">
                  Precio mayorista sugerido por Arroba (12.5 kg):
                </span>
                <strong class="text-sm text-[#2C4234]">
                  ${precioSugeridoArrobaCop.toLocaleString("es-CO")} COP
                </strong>
              </div>
              <div>
                <span class="text-stone-500 block">
                  Precio mayorista sugerido por Carga (125 kg):
                </span>
                <strong class="text-sm text-[#54121B]">
                  ${precioSugeridoCargaCop.toLocaleString("es-CO")} COP
                </strong>
              </div>
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-bold text-[#232323] mb-1">
                9. Notas de cata / Perfil sensorial (separadas por coma)
              </label>
              <input
                type="text"
                maxLength={200}
                value={notasCataTexto}
                onInput={(e) =>
                  setNotasCataTexto((e.target as HTMLInputElement).value)}
                placeholder="Ej: Panela, Mora, Cacao, Naranja"
                class="w-full min-h-[48px] px-4 py-3 rounded-xl border-2 border-stone-300 text-sm"
              />
            </div>
            <div>
              <label class="block text-sm font-bold text-[#232323] mb-1">
                10. Enlace HTTPS de foto del lote (o sube desde tu celular abajo)
              </label>
              <input
                type="url"
                maxLength={500}
                value={urlFotoLote}
                onInput={(e) =>
                  setUrlFotoLote((e.target as HTMLInputElement).value)}
                placeholder="https://res.cloudinary.com/..."
                class="w-full min-h-[48px] px-4 py-3 rounded-xl border-2 border-stone-300 text-sm"
              />
            </div>
          </div>

          <SubidorImagen
            urlBaseApi={urlBaseApi}
            tokenAutenticacion={tokenMemoria}
            alSubirImagenExitosamente={(urlOptimizadaWebp) =>
              setUrlFotoLote(urlOptimizadaWebp)}
          />

          {mensajeEstado && (
            <div
              class={`p-4 rounded-xl font-semibold text-sm ${
                mensajeEstado.tipo === "exito"
                  ? "bg-emerald-50 text-emerald-900 border border-emerald-300"
                  : "bg-red-50 text-red-900 border border-red-300"
              }`}
            >
              {mensajeEstado.texto}
            </div>
          )}

          <button
            type="submit"
            disabled={enviando || !tokenMemoria}
            class="w-full min-h-[54px] bg-[#54121B] hover:bg-[#2C4234] text-white font-extrabold text-lg rounded-2xl shadow-md transition-colors disabled:opacity-50"
          >
            {enviando
              ? "Publicando lote..."
              : !tokenMemoria
              ? "Inicia sesión arriba para publicar tu lote"
              : "Publicar Lote en el Catálogo"}
          </button>
        </form>
      ) : (
        <form onSubmit={manejarGuardadoFinca} class="space-y-5">
          <div class="border-b border-stone-200 pb-4">
            <h2 class="text-2xl font-extrabold text-[#232323]">
              Datos de Mi Finca Cafetera
            </h2>
            <p class="text-sm text-stone-600 mt-1">
              Cuenta la historia de tu finca, su ubicación en el Tolima y la altura sobre el nivel del mar.
            </p>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-bold text-[#232323] mb-1">
                Nombre de la Finca
              </label>
              <input
                type="text"
                required
                maxLength={150}
                value={nombreFinca}
                onInput={(e) =>
                  setNombreFinca((e.target as HTMLInputElement).value)}
                class="w-full min-h-[48px] px-4 py-3 rounded-xl border-2 border-stone-300"
              />
            </div>

            <div>
              <label class="block text-sm font-bold text-[#232323] mb-1">
                Municipio del Tolima
              </label>
              <select
                value={municipioTolima}
                onChange={(e) =>
                  setMunicipioTolima((e.target as HTMLSelectElement).value)}
                class="w-full min-h-[48px] px-4 py-3 rounded-xl border-2 border-stone-300 bg-white font-semibold"
              >
                {MUNICIPIOS_TOLIMA.map((mun) => (
                  <option key={mun} value={mun}>
                    {mun}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-bold text-[#232323] mb-1">
                Vereda o Corregimiento
              </label>
              <input
                type="text"
                required
                maxLength={120}
                value={veredaFinca}
                onInput={(e) =>
                  setVeredaFinca((e.target as HTMLInputElement).value)}
                class="w-full min-h-[48px] px-4 py-3 rounded-xl border-2 border-stone-300"
              />
            </div>

            <div>
              <label class="block text-sm font-bold text-[#232323] mb-1">
                Altura sobre el nivel del mar (m.s.n.m.)
              </label>
              <input
                type="number"
                min="800"
                max="2600"
                required
                value={alturaMsnm}
                onInput={(e) =>
                  setAlturaMsnm((e.target as HTMLInputElement).value)}
                class="w-full min-h-[48px] px-4 py-3 rounded-xl border-2 border-stone-300 font-bold"
              />
            </div>
          </div>

          <div>
            <label class="block text-sm font-bold text-[#232323] mb-1">
              Historia del productor y tradición familiar
            </label>
            <textarea
              rows={4}
              required
              maxLength={2000}
              value={historiaProductor}
              onInput={(e) =>
                setHistoriaProductor((e.target as HTMLTextAreaElement).value)}
              class="w-full p-4 rounded-xl border-2 border-stone-300 text-sm"
            />
          </div>

          {mensajeEstado && (
            <div
              class={`p-4 rounded-xl font-semibold text-sm ${
                mensajeEstado.tipo === "exito"
                  ? "bg-emerald-50 text-emerald-900 border border-emerald-300"
                  : "bg-red-50 text-red-900 border border-red-300"
              }`}
            >
              {mensajeEstado.texto}
            </div>
          )}

          <button
            type="submit"
            disabled={enviando || !tokenMemoria}
            class="w-full min-h-[54px] bg-[#2C4234] hover:bg-[#54121B] text-white font-extrabold text-lg rounded-2xl shadow-md transition-colors disabled:opacity-50"
          >
            {enviando
              ? "Guardando datos..."
              : !tokenMemoria
              ? "Inicia sesión arriba para guardar tu finca"
              : "Guardar Perfil de la Finca"}
          </button>
        </form>
      )}
    </div>
  );
}
