import { useState } from "preact/hooks";

// Contrato JSON externo en inglés devuelto por POST /api/v1/payments/checkout-session
interface ContratoExternoSesionWompi {
  order_id: string;
  reference: string;
  amount_in_cents: number;
  currency: string;
  public_key: string;
  signature_integrity: string;
  checkout_url: string;
  shipping_cost_cop: number;
  total_with_shipping_cop: number;
}

// Estado de dominio interno en español
interface SesionPagoWompiInterna {
  pedidoId: string;
  referencia: string;
  montoEnCentavos: number;
  moneda: string;
  llavePublica: string;
  firmaIntegridad: string;
  urlCheckoutWompi: string;
  costoEnvioCop: number;
  montoTotalConEnvioCop: number;
}

interface PropiedadesBotonPagoWompi {
  pedidoId: string;
  urlBaseApi: string;
  tokenAutenticacion?: string;
}

export default function BotonPagoWompi({
  pedidoId,
  urlBaseApi,
  tokenAutenticacion,
}: PropiedadesBotonPagoWompi) {
  const [sesionWompi, setSesionWompi] = useState<SesionPagoWompiInterna | null>(
    null,
  );
  const [generandoSesion, setGenerandoSesion] = useState(false);
  const [errorPago, setErrorPago] = useState<string | null>(null);

  const inicializarPasarelaWompi = async () => {
    setGenerandoSesion(true);
    setErrorPago(null);

    try {
      const respuesta = await fetch(
        `${urlBaseApi}/payments/checkout-session`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            ...(tokenAutenticacion
              ? { Authorization: `Bearer ${tokenAutenticacion}` }
              : {}),
          },
          body: JSON.stringify({
            order_id: pedidoId,
            redirect_url: `${
              globalThis.location?.origin || "http://localhost:8000"
            }/?pago=completado`,
          }),
        },
      );

      if (!respuesta.ok) {
        const err = await respuesta.json().catch(() => ({}));
        throw new Error(
          err.detail || "No fue posible generar la firma de pago en Wompi.",
        );
      }

      const dto: ContratoExternoSesionWompi = await respuesta.json();
      setSesionWompi({
        pedidoId: dto.order_id,
        referencia: dto.reference,
        montoEnCentavos: Number(dto.amount_in_cents),
        moneda: dto.currency,
        llavePublica: dto.public_key,
        firmaIntegridad: dto.signature_integrity,
        urlCheckoutWompi: dto.checkout_url,
        costoEnvioCop: Number(dto.shipping_cost_cop),
        montoTotalConEnvioCop: Number(dto.total_with_shipping_cop),
      });
    } catch (err) {
      setErrorPago(
        err instanceof Error
          ? err.message
          : "Error de conexión con el servicio de pagos Wompi.",
      );
    } finally {
      setGenerandoSesion(false);
    }
  };

  return (
    <div class="bg-[#FAF6F0] p-4 rounded-2xl border-2 border-[#54121B]/30 space-y-3 mt-3">
      <div class="flex items-center justify-between">
        <span class="text-xs font-extrabold uppercase tracking-wider text-[#54121B]">
          Pasarela Wompi Colombia (PSE • Nequi • Tarjetas)
        </span>
        <span class="text-[11px] font-bold bg-white px-2.5 py-0.5 rounded-full border border-[#E5D5C5] text-[#2C4234]">
          SHA-256 Verificado
        </span>
      </div>

      {!sesionWompi ? (
        <button
          type="button"
          onClick={inicializarPasarelaWompi}
          disabled={generandoSesion}
          class="w-full min-h-[46px] bg-[#54121B] hover:bg-[#2C4234] text-white font-extrabold text-sm rounded-xl transition-colors disabled:opacity-50"
        >
          {generandoSesion
            ? "Generando firma criptográfica Wompi..."
            : "Generar Link de Pago Seguro (PSE / Nequi)"}
        </button>
      ) : (
        <div class="space-y-2.5 text-xs bg-white p-3.5 rounded-xl border border-[#E5D5C5]">
          <div class="flex justify-between">
            <span class="text-stone-500">Referencia Wompi:</span>
            <strong class="font-mono text-[#232323]">
              {sesionWompi.referencia}
            </strong>
          </div>
          <div class="flex justify-between">
            <span class="text-stone-500">Flete Nacional Calculado:</span>
            <strong class="text-[#2C4234]">
              ${sesionWompi.costoEnvioCop.toLocaleString("es-CO")} COP
            </strong>
          </div>
          <div class="flex justify-between border-t border-stone-100 pt-1.5 text-sm">
            <span class="font-bold text-[#232323]">Total con Flete:</span>
            <strong class="font-extrabold text-[#54121B]">
              ${sesionWompi.montoTotalConEnvioCop.toLocaleString("es-CO")} COP
            </strong>
          </div>
          <p class="text-[10px] font-mono text-stone-400 truncate">
            Firma SHA-256: {sesionWompi.firmaIntegridad}
          </p>

          <a
            href={sesionWompi.urlCheckoutWompi}
            target="_blank"
            rel="noopener noreferrer"
            class="block w-full text-center bg-[#2C4234] hover:bg-[#54121B] text-white font-extrabold py-3 rounded-xl transition-colors mt-2"
          >
            Ir a Pagar en Wompi Colombia →
          </a>
        </div>
      )}

      {errorPago && (
        <p class="text-xs font-semibold text-red-700">{errorPago}</p>
      )}
    </div>
  );
}
