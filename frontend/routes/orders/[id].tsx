import { Handlers, PageProps } from "$fresh/server.ts";
import Encabezado from "../../components/Encabezado.tsx";
import {
  consultarPedidoYFacturaDian,
  DetallePedidoCompletoInterno,
  formatearPesosCOP,
  URL_BASE_API,
} from "../../utils/clienteApi.ts";

interface DatosPaginaOrdenFactura {
  pedido: DetallePedidoCompletoInterno | null;
  urlBaseApi: string;
}

export const handler: Handlers<DatosPaginaOrdenFactura> = {
  async GET(_req, ctx) {
    const pedidoId = ctx.params.id;
    const pedido = await consultarPedidoYFacturaDian(pedidoId);
    return ctx.render({
      pedido,
      urlBaseApi: URL_BASE_API,
    });
  },
};

export default function PaginaDetalleOrdenYFacturaDian({
  data,
}: PageProps<DatosPaginaOrdenFactura>) {
  const { pedido, urlBaseApi } = data;

  if (!pedido) {
    return (
      <div class="min-h-screen bg-[#FAF6F0]">
        <Encabezado urlBaseApi={urlBaseApi} />
        <main class="max-w-4xl mx-auto px-4 py-16 text-center">
          <h1 class="text-2xl font-extrabold text-[#232323]">
            No se encontró el pedido consultado
          </h1>
          <a
            href="/"
            class="inline-block mt-4 bg-[#2C4234] text-white font-bold px-5 py-3 rounded-xl"
          >
            Volver al catálogo
          </a>
        </main>
      </div>
    );
  }

  const factura = pedido.facturaElectronica;
  const datosFiscales = pedido.datosFiscales;
  const totalGeneral = pedido.montoTotalCop + pedido.costoEnvioCop;

  return (
    <div class="min-h-screen bg-[#FAF6F0]">
      <Encabezado urlBaseApi={urlBaseApi} rutaActiva="catalogo" />

      <main class="max-w-5xl mx-auto px-4 py-8 space-y-6">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <span class="text-xs font-extrabold uppercase tracking-wider text-[#2C4234]">
              Trazabilidad Tributaria y Comercial • Normativa DIAN Colombia
            </span>
            <h1 class="text-2xl md:text-3xl font-extrabold text-[#232323]">
              Detalle de Orden #{pedido.id.slice(0, 8)} y Factura Electrónica
            </h1>
          </div>

          <span class="text-xs font-extrabold px-3.5 py-1.5 rounded-full bg-[#2C4234] text-white self-start sm:self-center">
            Estado Pedido: {pedido.estado}
          </span>
        </div>

        {/* Tarjeta Principal de Factura Electrónica DIAN y CUFE */}
        <section class="bg-white rounded-3xl p-6 md:p-8 border-2 border-[#2C4234]/20 shadow-xs space-y-6">
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-stone-200 pb-4">
            <div>
              <span class="text-[11px] font-extrabold uppercase tracking-widest text-[#54121B]">
                Factura Electrónica de Venta con Validación Previa DIAN
              </span>
              <h2 class="text-xl font-extrabold text-[#232323] mt-0.5">
                Consecutivo Oficial: {factura?.numeroFactura ?? "En Emisión"}
              </h2>
            </div>

            {factura && (
              <span
                class={`text-xs font-extrabold px-3.5 py-1.5 rounded-full ${
                  factura.estadoDian === "APPROVED"
                    ? "bg-emerald-100 text-emerald-900 border border-emerald-300"
                    : factura.estadoDian === "REJECTED"
                    ? "bg-red-100 text-red-900 border border-red-300"
                    : "bg-amber-100 text-amber-900 border border-amber-300"
                }`}
              >
                Estado DIAN: {factura.estadoDian}
              </span>
            )}
          </div>

          {factura?.cufe ? (
            <div class="bg-[#FAF6F0] p-5 rounded-2xl border border-[#E5D5C5] space-y-3">
              <div>
                <span class="block text-xs font-extrabold uppercase tracking-wider text-[#2C4234] mb-1">
                  Código Único de Facturación Electrónica (CUFE - Algoritmo SHA-384)
                </span>
                <p class="font-mono text-xs text-[#232323] bg-white p-3 rounded-xl border border-stone-200 break-all select-all">
                  {factura.cufe}
                </p>
              </div>

              <div class="flex flex-wrap items-center gap-3 pt-2">
                {factura.urlPdf && (
                  <a
                    href={factura.urlPdf}
                    target="_blank"
                    rel="noopener noreferrer"
                    class="bg-[#54121B] hover:bg-[#2C4234] text-white font-extrabold text-xs px-5 py-3 rounded-xl transition-colors"
                  >
                    Descargar Factura Electrónica (PDF)
                  </a>
                )}

                {factura.urlXml && (
                  <a
                    href={factura.urlXml}
                    target="_blank"
                    rel="noopener noreferrer"
                    class="bg-white hover:bg-stone-100 text-[#232323] border border-stone-300 font-bold text-xs px-4 py-3 rounded-xl transition-colors"
                  >
                    Descargar XML Firmado (UBL 2.1)
                  </a>
                )}

                {factura.urlCodigoQr && (
                  <a
                    href={factura.urlCodigoQr}
                    target="_blank"
                    rel="noopener noreferrer"
                    class="text-xs font-bold text-[#2C4234] hover:underline ml-auto"
                  >
                    Verificar validez en portal catálogo DIAN →
                  </a>
                )}
              </div>
            </div>
          ) : (
            <div class="p-4 rounded-2xl bg-amber-50 border border-amber-200 text-xs text-amber-900">
              {factura?.mensajeErrorDian
                ? `Observación DIAN: ${factura.mensajeErrorDian}`
                : "La factura electrónica está siendo procesada de forma asíncrona ante la DIAN."}
            </div>
          )}

          {/* Datos Fiscales del Adquirente y Resumen Financiero */}
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
            <div class="bg-stone-50 p-5 rounded-2xl border border-stone-200 space-y-2">
              <h3 class="text-xs font-extrabold uppercase tracking-wider text-stone-500">
                Datos Tributarios del Adquirente (RUT / DIAN)
              </h3>
              {datosFiscales ? (
                <dl class="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <dt class="text-stone-500">Razón Social / Nombre</dt>
                    <dd class="font-bold text-[#232323]">
                      {datosFiscales.razonSocialONombre}
                    </dd>
                  </div>
                  <div>
                    <dt class="text-stone-500">Identificación Tributaria</dt>
                    <dd class="font-bold text-[#232323] font-mono">
                      {datosFiscales.tipoDocumento} {datosFiscales.numeroDocumento}
                      {datosFiscales.digitoVerificacion
                        ? `-${datosFiscales.digitoVerificacion}`
                        : ""}
                    </dd>
                  </div>
                  <div>
                    <dt class="text-stone-500">Tipo Contribuyente</dt>
                    <dd class="font-bold text-[#232323]">
                      Persona {datosFiscales.tipoPersona}
                    </dd>
                  </div>
                  <div>
                    <dt class="text-stone-500">Régimen Fiscal</dt>
                    <dd class="font-bold text-[#232323]">
                      {datosFiscales.regimenTributario}
                    </dd>
                  </div>
                  <div>
                    <dt class="text-stone-500">Correo Recepción DIAN</dt>
                    <dd class="font-bold text-[#232323]">
                      {datosFiscales.correoFacturacion}
                    </dd>
                  </div>
                  <div>
                    <dt class="text-stone-500">Código Municipio DANE</dt>
                    <dd class="font-bold text-[#232323] font-mono">
                      {datosFiscales.codigoMunicipioDane}
                    </dd>
                  </div>
                </dl>
              ) : (
                <p class="text-xs text-stone-600">
                  Emitida a Consumidor Final (222222222222) — Municipio DANE 73001.
                </p>
              )}
            </div>

            <div class="bg-stone-50 p-5 rounded-2xl border border-stone-200 flex flex-col justify-between space-y-3">
              <h3 class="text-xs font-extrabold uppercase tracking-wider text-stone-500">
                Liquidación de Orden y Flete
              </h3>
              <div class="space-y-1.5 text-sm">
                <div class="flex justify-between">
                  <span class="text-stone-600">Subtotal Lotes de Café:</span>
                  <strong class="text-[#232323]">
                    {formatearPesosCOP(pedido.montoTotalCop)}
                  </strong>
                </div>
                <div class="flex justify-between">
                  <span class="text-stone-600">
                    Flete Nacional ({pedido.ciudadEnvio}, {pedido.departamentoEnvio}):
                  </span>
                  <strong class="text-[#2C4234]">
                    {formatearPesosCOP(pedido.costoEnvioCop)}
                  </strong>
                </div>
                <div class="flex justify-between border-t border-stone-200 pt-2 text-base font-extrabold text-[#54121B]">
                  <span>Total Facturado COP:</span>
                  <span>{formatearPesosCOP(totalGeneral)}</span>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
