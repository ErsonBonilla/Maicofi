import { useEffect, useState } from "preact/hooks";
import BotonPagoWompi from "./BotonPagoWompi.tsx";
import FormularioFacturacion, {
  DatosFiscalesFormulario,
} from "./FormularioFacturacion.tsx";

export interface ItemCanasta {
  loteCafeId: string;
  nombreLote: string;
  nombreFinca: string;
  municipio: string;
  unidadVenta: "250g" | "500g" | "1000g" | "libra" | "arroba" | "carga";
  tipoMolienda?: string;
  esSuscripcion?: boolean;
  frecuenciaSuscripcion?: "semanal" | "quincenal" | "mensual";
  cantidad: number;
  precioUnitarioCop: number;
}

interface PropiedadesCanastaCompra {
  urlBaseApi: string;
  tokenAutenticacion?: string;
}

const CLAVE_ALMACENAMIENTO_CANASTA = "maicofi_canasta_v1";

export default function CanastaCompra({
  urlBaseApi,
  tokenAutenticacion,
}: PropiedadesCanastaCompra) {
  const [abierto, setAbierto] = useState(false);
  const [itemsCanasta, setItemsCanasta] = useState<ItemCanasta[]>([]);

  // Sesión mantenida en memoria + Cookie HttpOnly (sin exponer JWT en localStorage)
  const [tokenMemoria, setTokenMemoria] = useState<string>(
    tokenAutenticacion ?? "",
  );
  const [nombreUsuarioActivo, setNombreUsuarioActivo] = useState<string>("");
  const [identificadorLogin, setIdentificadorLogin] = useState("");
  const [contrasenaLogin, setContrasenaLogin] = useState("");
  const [autenticando, setAutenticando] = useState(false);

  const [direccionEnvio, setDireccionEnvio] = useState("");
  const [ciudadEnvio, setCiudadEnvio] = useState("Ibagué");
  const [telefonoContacto, setTelefonoContacto] = useState("");
  const [notasPedido, setNotasPedido] = useState("");
  const [datosFiscalesDian, setDatosFiscalesDian] = useState<
    DatosFiscalesFormulario | null
  >(null);
  const [procesandoPedido, setProcesandoPedido] = useState(false);
  const [pedidoRecienCreadoId, setPedidoRecienCreadoId] = useState<
    string | null
  >(null);
  const [mensajeConfirmacion, setMensajeConfirmacion] = useState<string | null>(
    null,
  );
  const [mensajeError, setMensajeError] = useState<string | null>(null);

  useEffect(() => {
    const guardado = localStorage.getItem(CLAVE_ALMACENAMIENTO_CANASTA);
    if (guardado) {
      try {
        setItemsCanasta(JSON.parse(guardado));
      } catch {
        setItemsCanasta([]);
      }
    }

    const manejarEventoAgregar = (evento: Event) => {
      const eventoPersonalizado = evento as CustomEvent<ItemCanasta>;
      const nuevoItem = eventoPersonalizado.detail;

      setItemsCanasta((actuales) => {
        const indiceExistente = actuales.findIndex(
          (i) =>
            i.loteCafeId === nuevoItem.loteCafeId &&
            i.unidadVenta === nuevoItem.unidadVenta &&
            (i.tipoMolienda ?? "Grano entero") ===
              (nuevoItem.tipoMolienda ?? "Grano entero") &&
            Boolean(i.esSuscripcion) === Boolean(nuevoItem.esSuscripcion) &&
            i.frecuenciaSuscripcion === nuevoItem.frecuenciaSuscripcion,
        );
        let actualizados: ItemCanasta[];
        if (indiceExistente >= 0) {
          actualizados = [...actuales];
          actualizados[indiceExistente] = {
            ...actualizados[indiceExistente],
            cantidad: actualizados[indiceExistente].cantidad + nuevoItem.cantidad,
          };
        } else {
          actualizados = [...actuales, nuevoItem];
        }
        localStorage.setItem(
          CLAVE_ALMACENAMIENTO_CANASTA,
          JSON.stringify(actualizados),
        );
        return actualizados;
      });
      setMensajeConfirmacion(null);
      setMensajeError(null);
      setAbierto(true);
    };

    globalThis.addEventListener("maicofi:agregar-canasta", manejarEventoAgregar);
    return () =>
      globalThis.removeEventListener(
        "maicofi:agregar-canasta",
        manejarEventoAgregar,
      );
  }, []);

  const actualizarCantidadItem = (indice: number, variacion: number) => {
    setItemsCanasta((actuales) => {
      const siguientes = actuales
        .map((item, idx) =>
          idx === indice
            ? { ...item, cantidad: item.cantidad + variacion }
            : item
        )
        .filter((item) => item.cantidad > 0);
      localStorage.setItem(
        CLAVE_ALMACENAMIENTO_CANASTA,
        JSON.stringify(siguientes),
      );
      return siguientes;
    });
  };

  const iniciarSesionComprador = async (evento: Event) => {
    evento.preventDefault();
    setAutenticando(true);
    setMensajeError(null);

    try {
      const respuesta = await fetch(`${urlBaseApi}/auth/login`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          identifier: identificadorLogin.trim(),
          password: contrasenaLogin,
        }),
      });

      if (!respuesta.ok) {
        const errorJson = await respuesta.json().catch(() => ({}));
        throw new Error(errorJson.detail || "Credenciales inválidas.");
      }

      const datos = await respuesta.json();
      setTokenMemoria(datos.access_token);
      setNombreUsuarioActivo(datos.full_name);
      setContrasenaLogin("");
    } catch (err) {
      setMensajeError(
        err instanceof Error ? err.message : "No fue posible iniciar sesión.",
      );
    } finally {
      setAutenticando(false);
    }
  };

  const activarAccesoDemoComprador = async () => {
    setAutenticando(true);
    setMensajeError(null);

    try {
      const respuesta = await fetch(`${urlBaseApi}/auth/demo-access`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role: "buyer" }),
      });

      if (!respuesta.ok) {
        const errorJson = await respuesta.json().catch(() => ({}));
        throw new Error(
          errorJson.detail || "El acceso demostrativo no está disponible.",
        );
      }

      const datos = await respuesta.json();
      setTokenMemoria(datos.access_token);
      setNombreUsuarioActivo(datos.full_name);
    } catch (err) {
      setMensajeError(
        err instanceof Error
          ? err.message
          : "Error solicitando sesión demostrativa.",
      );
    } finally {
      setAutenticando(false);
    }
  };

  const totalUnidades = itemsCanasta.reduce((acc, i) => acc + i.cantidad, 0);
  const montoTotalCop = itemsCanasta.reduce(
    (acc, i) => acc + i.precioUnitarioCop * i.cantidad,
    0,
  );

  const confirmarPedidoDirecto = async (evento: Event) => {
    evento.preventDefault();
    setProcesandoPedido(true);
    setMensajeError(null);
    setMensajeConfirmacion(null);

    try {
      const encabezadosComunes: Record<string, string> = {
        "Content-Type": "application/json",
        ...(tokenMemoria ? { Authorization: `Bearer ${tokenMemoria}` } : {}),
      };

      const itemsCompraUnica = itemsCanasta.filter((i) => !i.esSuscripcion);
      const itemsSuscripcion = itemsCanasta.filter((i) => i.esSuscripcion);

      const resumenesConfirmados: string[] = [];

      if (itemsCompraUnica.length > 0) {
        const cuerpoContratoPedido = {
          shipping_address: direccionEnvio,
          shipping_city: ciudadEnvio,
          shipping_department: "Tolima",
          contact_phone: telefonoContacto,
          notes: notasPedido || undefined,
          tax_data: datosFiscalesDian
            ? {
              document_type: datosFiscalesDian.tipoDocumento,
              document_number: datosFiscalesDian.numeroDocumento,
              verification_digit: datosFiscalesDian.digitoVerificacion || undefined,
              tax_name: datosFiscalesDian.razonSocialONombre,
              billing_email: datosFiscalesDian.correoFacturacion,
              person_type: datosFiscalesDian.tipoPersona,
              tax_regime: datosFiscalesDian.regimenTributario,
              tax_address: datosFiscalesDian.direccionFiscal || direccionEnvio,
              municipality_code: datosFiscalesDian.codigoMunicipioDane,
            }
            : undefined,
          items: itemsCompraUnica.map((item) => ({
            coffee_lot_id: item.loteCafeId,
            unit_type: item.unidadVenta,
            grind_type: item.tipoMolienda ?? "Grano entero",
            quantity: item.cantidad,
          })),
        };

        const respuestaPedido = await fetch(`${urlBaseApi}/orders`, {
          method: "POST",
          credentials: "include",
          headers: encabezadosComunes,
          body: JSON.stringify(cuerpoContratoPedido),
        });

        if (!respuestaPedido.ok) {
          const errorJson = await respuestaPedido.json().catch(() => ({}));
          throw new Error(
            errorJson.detail ||
              "Debes iniciar sesión antes de confirmar el pedido.",
          );
        }

        const pedidoCreado = await respuestaPedido.json();
        setPedidoRecienCreadoId(String(pedidoCreado.id));
        resumenesConfirmados.push(
          `Pedido #${String(pedidoCreado.id).slice(0, 8)}`,
        );
      }

      for (const sub of itemsSuscripcion) {
        const respuestaSub = await fetch(`${urlBaseApi}/subscriptions`, {
          method: "POST",
          credentials: "include",
          headers: encabezadosComunes,
          body: JSON.stringify({
            coffee_lot_id: sub.loteCafeId,
            frequency: sub.frecuenciaSuscripcion ?? "mensual",
            weight_presentation: sub.unidadVenta,
            grind_type: sub.tipoMolienda ?? "Grano entero",
            quantity: sub.cantidad,
            shipping_address: direccionEnvio,
            shipping_city: ciudadEnvio,
          }),
        });

        if (!respuestaSub.ok) {
          const errorJson = await respuestaSub.json().catch(() => ({}));
          throw new Error(
            errorJson.detail || "No fue posible activar la suscripción.",
          );
        }

        const subCreada = await respuestaSub.json();
        resumenesConfirmados.push(
          `Suscripción ${sub.frecuenciaSuscripcion} (-10%, próxima entrega: ${subCreada.next_delivery_date})`,
        );
      }

      setMensajeConfirmacion(
        `Confirmado con éxito: ${resumenesConfirmados.join(" + ")}.`,
      );
      setItemsCanasta([]);
      localStorage.removeItem(CLAVE_ALMACENAMIENTO_CANASTA);
    } catch (err) {
      setMensajeError(
        err instanceof Error
          ? err.message
          : "Error de conexión con el servidor de pedidos.",
      );
    } finally {
      setProcesandoPedido(false);
    }
  };

  return (
    <>
      <button
        type="button"
        onClick={() => setAbierto(true)}
        class="relative bg-[#54121B] hover:bg-[#2C4234] text-white font-bold px-4 py-2.5 rounded-xl flex items-center gap-2 transition-colors min-h-[44px]"
      >
        <span>Canasta</span>
        <span class="bg-[#FAF6F0] text-[#54121B] text-xs font-extrabold px-2 py-0.5 rounded-full">
          {totalUnidades}
        </span>
      </button>

      {abierto && (
        <div class="fixed inset-0 z-50 flex justify-end bg-black/50 backdrop-blur-xs">
          <div class="bg-white w-full max-w-md h-full flex flex-col justify-between p-6 shadow-2xl overflow-y-auto">
            <div>
              <div class="flex items-center justify-between border-b border-stone-200 pb-4">
                <div>
                  <span class="text-xs font-bold uppercase tracking-wider text-[#2C4234]">
                    Comercio Directo del Tolima
                  </span>
                  <h3 class="text-xl font-extrabold text-[#232323]">
                    Canasta de Compra
                  </h3>
                </div>
                <button
                  type="button"
                  onClick={() => setAbierto(false)}
                  class="text-stone-500 hover:text-black text-2xl font-bold px-2.5 py-1 rounded-lg hover:bg-stone-100"
                  aria-label="Cerrar canasta"
                >
                  ×
                </button>
              </div>

              {mensajeConfirmacion && (
                <div class="mt-4 p-4 bg-emerald-50 border border-emerald-300 text-emerald-900 rounded-xl text-sm font-semibold space-y-2">
                  <p>{mensajeConfirmacion}</p>
                  {pedidoRecienCreadoId && (
                    <>
                      <BotonPagoWompi
                        pedidoId={pedidoRecienCreadoId}
                        urlBaseApi={urlBaseApi}
                        tokenAutenticacion={tokenMemoria}
                      />
                      <a
                        href={`/orders/${pedidoRecienCreadoId}`}
                        class="block text-center text-xs font-extrabold text-[#2C4234] hover:text-[#54121B] underline pt-1"
                      >
                        Ver Detalle del Pedido y Factura Electrónica DIAN (CUFE / PDF) →
                      </a>
                    </>
                  )}
                </div>
              )}

              {mensajeError && (
                <div class="mt-4 p-4 bg-red-50 border border-red-300 text-red-900 rounded-xl text-sm font-semibold">
                  {mensajeError}
                </div>
              )}

              {itemsCanasta.length === 0 ? (
                <div class="py-14 text-center space-y-2">
                  <p class="text-stone-600 font-semibold text-base">
                    Tu canasta está vacía.
                  </p>
                  <p class="text-stone-500 text-xs">
                    Personaliza tus lotes en 250g, 500g, 1000g, arroba o carga, eligiendo molienda o suscripción (-10%).
                  </p>
                </div>
              ) : (
                <ul class="divide-y divide-stone-200 my-4">
                  {itemsCanasta.map((item, indice) => (
                    <li
                      key={`${item.loteCafeId}-${item.unidadVenta}-${item.tipoMolienda}-${item.frecuenciaSuscripcion}`}
                      class="py-3.5 flex justify-between items-center gap-3"
                    >
                      <div>
                        <div class="flex items-center gap-1.5">
                          <p class="font-bold text-sm text-[#232323]">
                            {item.nombreLote}
                          </p>
                          {item.esSuscripcion && (
                            <span class="text-[10px] font-extrabold uppercase bg-[#54121B] text-white px-2 py-0.5 rounded-full">
                              Suscripción {item.frecuenciaSuscripcion} (-10%)
                            </span>
                          )}
                        </div>
                        <p class="text-xs text-stone-500 mt-0.5">
                          {item.nombreFinca} ({item.municipio}) •{" "}
                          <strong class="uppercase text-[#2C4234]">
                            {item.unidadVenta}
                          </strong>{" "}
                          • {item.tipoMolienda ?? "Grano entero"}
                        </p>
                        <p class="text-sm font-extrabold text-[#54121B] mt-1">
                          $
                          {(item.precioUnitarioCop * item.cantidad).toLocaleString(
                            "es-CO",
                          )}{" "}
                          COP
                        </p>
                      </div>
                      <div class="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => actualizarCantidadItem(indice, -1)}
                          class="w-9 h-9 rounded-lg bg-stone-100 hover:bg-stone-200 font-bold text-base"
                        >
                          -
                        </button>
                        <span class="font-extrabold text-sm w-6 text-center">
                          {item.cantidad}
                        </span>
                        <button
                          type="button"
                          onClick={() => actualizarCantidadItem(indice, 1)}
                          class="w-9 h-9 rounded-lg bg-stone-100 hover:bg-stone-200 font-bold text-base"
                        >
                          +
                        </button>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {itemsCanasta.length > 0 && (
              <div class="border-t border-stone-200 pt-4 space-y-4">
                {!tokenMemoria ? (
                  <div class="bg-[#FAF6F0] p-4 rounded-2xl border border-[#E5D5C5] space-y-3">
                    <p class="text-xs font-extrabold uppercase tracking-wider text-[#54121B]">
                      Identifícate para confirmar tu pedido
                    </p>
                    <form onSubmit={iniciarSesionComprador} class="space-y-2">
                      <input
                        type="text"
                        required
                        placeholder="Celular (+57...) o correo"
                        value={identificadorLogin}
                        onInput={(e) =>
                          setIdentificadorLogin(
                            (e.target as HTMLInputElement).value,
                          )}
                        class="w-full px-3 py-2 rounded-xl border border-stone-300 text-xs bg-white"
                      />
                      <input
                        type="password"
                        required
                        placeholder="Contraseña"
                        value={contrasenaLogin}
                        onInput={(e) =>
                          setContrasenaLogin(
                            (e.target as HTMLInputElement).value,
                          )}
                        class="w-full px-3 py-2 rounded-xl border border-stone-300 text-xs bg-white"
                      />
                      <div class="grid grid-cols-2 gap-2">
                        <button
                          type="submit"
                          disabled={autenticando}
                          class="bg-[#2C4234] text-white font-bold text-xs py-2.5 rounded-xl"
                        >
                          Iniciar Sesión
                        </button>
                        <button
                          type="button"
                          disabled={autenticando}
                          onClick={activarAccesoDemoComprador}
                          class="bg-white text-[#54121B] border border-[#54121B] font-bold text-xs py-2.5 rounded-xl"
                        >
                          Acceso Demo (Dev)
                        </button>
                      </div>
                    </form>
                  </div>
                ) : (
                  <div class="text-xs bg-emerald-50 border border-emerald-200 text-emerald-900 px-3 py-2 rounded-xl flex justify-between items-center">
                    <span>
                      Sesión activa: <strong>{nombreUsuarioActivo || "Comprador"}</strong>
                    </span>
                    <button
                      type="button"
                      onClick={() => {
                        setTokenMemoria("");
                        setNombreUsuarioActivo("");
                      }}
                      class="underline font-bold"
                    >
                      Cambiar
                    </button>
                  </div>
                )}

                <form onSubmit={confirmarPedidoDirecto} class="space-y-3">
                  <div class="flex justify-between text-lg font-extrabold text-[#232323]">
                    <span>Total a Pagar:</span>
                    <span>${montoTotalCop.toLocaleString("es-CO")} COP</span>
                  </div>

                  <div>
                    <label class="block text-xs font-bold text-stone-700 mb-1">
                      Dirección de entrega
                    </label>
                    <input
                      type="text"
                      required
                      maxLength={250}
                      placeholder="Ej: Cra 5 # 37-15, Barrio Cádiz"
                      value={direccionEnvio}
                      onInput={(e) =>
                        setDireccionEnvio((e.target as HTMLInputElement).value)}
                      class="w-full px-3.5 py-2.5 rounded-xl border border-stone-300 text-sm"
                    />
                  </div>

                  <div class="grid grid-cols-2 gap-2">
                    <div>
                      <label class="block text-xs font-bold text-stone-700 mb-1">
                        Ciudad / Municipio
                      </label>
                      <input
                        type="text"
                        required
                        maxLength={100}
                        value={ciudadEnvio}
                        onInput={(e) =>
                          setCiudadEnvio((e.target as HTMLInputElement).value)}
                        class="w-full px-3.5 py-2.5 rounded-xl border border-stone-300 text-sm"
                      />
                    </div>
                    <div>
                      <label class="block text-xs font-bold text-stone-700 mb-1">
                        Celular / WhatsApp
                      </label>
                      <input
                        type="tel"
                        required
                        pattern="^\+?[0-9]{7,15}$"
                        placeholder="+57310..."
                        value={telefonoContacto}
                        onInput={(e) =>
                          setTelefonoContacto(
                            (e.target as HTMLInputElement).value,
                          )}
                        class="w-full px-3.5 py-2.5 rounded-xl border border-stone-300 text-sm"
                      />
                    </div>
                  </div>

                  <div>
                    <label class="block text-xs font-bold text-stone-700 mb-1">
                      Indicaciones para el caficultor o transportadora (opcional)
                    </label>
                    <input
                      type="text"
                      maxLength={500}
                      placeholder="Ej: Despacho en bolsa con válvula desgasificadora"
                      value={notasPedido}
                      onInput={(e) =>
                        setNotasPedido((e.target as HTMLInputElement).value)}
                      class="w-full px-3.5 py-2.5 rounded-xl border border-stone-300 text-sm"
                    />
                  </div>

                  {/* Isla de Captura Tributaria DIAN */}
                  <FormularioFacturacion
                    direccionPredeterminada={direccionEnvio}
                    alCambiarDatosFiscales={setDatosFiscalesDian}
                  />

                  <button
                    type="submit"
                    disabled={procesandoPedido || !tokenMemoria}
                    class="w-full min-h-[48px] bg-[#2C4234] hover:bg-[#54121B] text-white font-extrabold rounded-xl transition-colors disabled:opacity-50"
                  >
                    {procesandoPedido
                      ? "Procesando pedido..."
                      : "Confirmar Pedido Directo"}
                  </button>
                </form>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}
