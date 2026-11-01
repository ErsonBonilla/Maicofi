import { useState } from "preact/hooks";

// Contrato JSON externo en inglés devuelto por POST /api/v1/media/upload
interface ContratoExternoSubidaImagen {
  public_id: string;
  original_url: string;
  optimized_webp_url: string;
  card_thumbnail_url: string;
  format: string;
}

interface PropiedadesSubidorImagen {
  urlBaseApi: string;
  tokenAutenticacion?: string;
  alSubirImagenExitosamente: (urlWebpOptimizada: string) => void;
}

export default function SubidorImagen({
  urlBaseApi,
  tokenAutenticacion,
  alSubirImagenExitosamente,
}: PropiedadesSubidorImagen) {
  const [subiendo, setSubiendo] = useState(false);
  const [urlVistaPrevia, setUrlVistaPrevia] = useState<string | null>(null);
  const [urlCloudinaryWebp, setUrlCloudinaryWebp] = useState<string | null>(
    null,
  );
  const [mensajeError, setMensajeError] = useState<string | null>(null);

  const manejarSeleccionArchivo = async (evento: Event) => {
    const input = evento.target as HTMLInputElement;
    const archivo = input.files?.[0];
    if (!archivo) return;

    setMensajeError(null);
    setUrlVistaPrevia(URL.createObjectURL(archivo));
    setSubiendo(true);

    try {
      const formulario = new FormData();
      formulario.append("file", archivo);

      const respuesta = await fetch(`${urlBaseApi}/media/upload`, {
        method: "POST",
        credentials: "include",
        headers: {
          ...(tokenAutenticacion
            ? { Authorization: `Bearer ${tokenAutenticacion}` }
            : {}),
        },
        body: formulario,
      });

      if (!respuesta.ok) {
        const err = await respuesta.json().catch(() => ({}));
        throw new Error(
          err.detail ||
            "Inicia sesión como caficultor para subir fotos a Cloudinary.",
        );
      }

      const dto: ContratoExternoSubidaImagen = await respuesta.json();
      const urlWebpOptimizada = dto.optimized_webp_url;
      setUrlCloudinaryWebp(urlWebpOptimizada);
      alSubirImagenExitosamente(urlWebpOptimizada);
    } catch (err) {
      setMensajeError(
        err instanceof Error
          ? err.message
          : "No fue posible optimizar la fotografía.",
      );
    } finally {
      setSubiendo(false);
    }
  };

  return (
    <div class="bg-[#FAF6F0] p-4 rounded-2xl border-2 border-dashed border-[#2C4234]/40 space-y-3">
      <div class="flex items-center justify-between">
        <div>
          <span class="block text-xs font-extrabold uppercase tracking-wider text-[#2C4234]">
            Subida de Fotografía (Cloudinary CDN WebP)
          </span>
          <span class="text-[11px] text-stone-600">
            Toma una foto desde tu celular; se optimiza automáticamente a formato WebP ligero.
          </span>
        </div>
      </div>

      <label class="flex items-center justify-center min-h-[48px] px-4 py-2.5 rounded-xl bg-white hover:bg-stone-50 border border-stone-300 cursor-pointer font-bold text-xs text-[#232323] transition-colors">
        <span>
          {subiendo
            ? "Optimizando imagen en Cloudinary..."
            : "Seleccionar o Tomar Foto del Lote / Finca"}
        </span>
        <input
          type="file"
          accept="image/jpeg,image/png,image/webp"
          capture="environment"
          onChange={manejarSeleccionArchivo}
          class="hidden"
        />
      </label>

      {urlVistaPrevia && (
        <div class="flex items-center gap-3 bg-white p-2.5 rounded-xl border border-[#E5D5C5]">
          <img
            src={urlVistaPrevia}
            alt="Vista previa del lote"
            class="w-14 h-14 object-cover rounded-lg border border-stone-200 shrink-0"
          />
          <div class="text-xs overflow-hidden">
            <p class="font-bold text-emerald-800">
              {urlCloudinaryWebp
                ? "Optimizada en Cloudinary (WebP)"
                : "Procesando imagen..."}
            </p>
            {urlCloudinaryWebp && (
              <p class="font-mono text-[10px] text-stone-500 truncate">
                {urlCloudinaryWebp}
              </p>
            )}
          </div>
        </div>
      )}

      {mensajeError && (
        <p class="text-xs font-semibold text-red-700">{mensajeError}</p>
      )}
    </div>
  );
}
