import { useEffect, useRef } from "preact/hooks";

interface PropiedadesMapaFinca {
  latitud: number;
  longitud: number;
  nombreFinca: string;
  municipio: string;
  vereda: string;
  alturaMsnm: number;
  nombreProductor?: string;
}

export default function MapaFinca({
  latitud,
  longitud,
  nombreFinca,
  municipio,
  vereda,
  alturaMsnm,
  nombreProductor,
}: PropiedadesMapaFinca) {
  const contenedorMapaRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let instanciaMapa: { remove: () => void } | null = null;

    const inicializarLeaflet = async () => {
      if (!contenedorMapaRef.current) return;

      const moduloLeaflet = await import("https://esm.sh/leaflet@1.9.4");
      const L = moduloLeaflet.default || moduloLeaflet;

      const iconoCafetal = L.divIcon({
        className: "marcador-finca-maicofi",
        html: `<div style="background:#54121B;color:#FAF6F0;border:3px solid #2C4234;border-radius:9999px;width:28px;height:28px;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:12px;box-shadow:0 4px 10px rgba(0,0,0,0.3);">M</div>`,
        iconSize: [28, 28],
        iconAnchor: [14, 14],
      });

      const mapa = L.map(contenedorMapaRef.current, {
        scrollWheelZoom: false,
      }).setView([latitud, longitud], 13);

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 18,
        attribution: "© OpenStreetMap contributors • Origen Tolima",
      }).addTo(mapa);

      const marcador = L.marker([latitud, longitud], { icon: iconoCafetal })
        .addTo(mapa);

      marcador.bindPopup(
        `<div style="font-family:sans-serif;font-size:12px;line-height:1.4;">
          <strong style="color:#54121B;font-size:13px;">${nombreFinca}</strong><br/>
          <span>${vereda}, ${municipio} (Tolima)</span><br/>
          <strong>Altitud: ${alturaMsnm} m.s.n.m.</strong>
          ${nombreProductor ? `<br/><span>Productor: ${nombreProductor}</span>` : ""}
        </div>`,
      ).openPopup();

      instanciaMapa = mapa;
    };

    inicializarLeaflet();

    return () => {
      if (instanciaMapa) {
        instanciaMapa.remove();
      }
    };
  }, [
    latitud,
    longitud,
    nombreFinca,
    municipio,
    vereda,
    alturaMsnm,
    nombreProductor,
  ]);

  return (
    <div class="space-y-2">
      <div class="flex items-center justify-between">
        <span class="text-xs font-extrabold uppercase tracking-wider text-[#2C4234]">
          Mapa Interactivo de la Finca (OpenStreetMap)
        </span>
        <span class="text-[11px] font-mono text-stone-500">
          {latitud.toFixed(4)}° N, {longitud.toFixed(4)}° O
        </span>
      </div>
      <div
        ref={contenedorMapaRef}
        class="w-full h-56 rounded-2xl border-2 border-[#E5D5C5] overflow-hidden bg-stone-100 z-10"
        aria-label={`Mapa de ubicación de ${nombreFinca} en ${municipio}, Tolima`}
      />
    </div>
  );
}
