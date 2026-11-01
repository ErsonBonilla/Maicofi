import { formatearPesosCOP, LoteCafeTolima } from "../utils/clienteApi.ts";

interface PropiedadesTarjetaProducto {
  lote: LoteCafeTolima;
}

export default function TarjetaProducto({ lote }: PropiedadesTarjetaProducto) {
  const imagenPrincipal = lote.urlsFotos?.[0] ||
    "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?auto=format&fit=crop&w=800&q=80";
  const enlaceDetalle = `/products/${lote.slug || lote.id}`;

  return (
    <article class="bg-white rounded-2xl shadow-xs hover:shadow-xl transition-all duration-300 border border-[#E6DEC8] overflow-hidden flex flex-col justify-between">
      <div>
        <div class="relative h-52 overflow-hidden bg-[#2C4234]">
          <img
            src={imagenPrincipal}
            alt={`${lote.nombre} - ${lote.finca.nombreFinca}`}
            class="w-full h-full object-cover hover:scale-105 transition-transform duration-500"
            loading="lazy"
          />
          <div class="absolute top-3 left-3 bg-[#54121B] text-white text-xs font-extrabold px-3 py-1.5 rounded-full shadow-md">
            Taza SCA {lote.puntajeSca.toFixed(2)} pts
          </div>
          {lote.valvulaDesgasificadora && (
            <div class="absolute top-3 right-3 bg-white/90 text-[#2C4234] text-[10px] font-extrabold px-2.5 py-1 rounded-full">
              Válvula Desgasificadora
            </div>
          )}
          <div class="absolute bottom-3 left-3 bg-black/75 backdrop-blur-xs text-[#FAF6F0] text-xs font-semibold px-3 py-1.5 rounded-lg">
            {lote.finca.municipio}, Tolima • {lote.finca.alturaMsnm} m.s.n.m.
          </div>
        </div>

        <div class="p-5">
          <div class="flex flex-wrap items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#2C4234] mb-1.5">
            <span>Variedad {lote.variedad}</span>
            <span>•</span>
            <span>Beneficio {lote.proceso}</span>
            <span>•</span>
            <span>Tueste {lote.perfilSensorial.nivelTueste}</span>
          </div>

          <h3 class="text-lg font-extrabold text-[#232323] leading-snug mb-1.5">
            <a
              href={enlaceDetalle}
              class="hover:text-[#54121B] transition-colors"
            >
              {lote.nombre}
            </a>
          </h3>

          <p class="text-sm text-stone-600 mb-3">
            Finca <strong class="text-stone-800">{lote.finca.nombreFinca}</strong>{" "}
            ({lote.finca.vereda})
            {lote.finca.nombrePropietario
              ? ` • ${lote.finca.nombrePropietario}`
              : ""}
          </p>

          <div class="flex flex-wrap gap-1.5 mb-4">
            {lote.notasCata.map((nota) => (
              <span
                key={nota}
                class="text-xs bg-[#FAF6F0] text-[#54121B] border border-[#E5D5C5] px-2.5 py-1 rounded-full font-semibold"
              >
                {nota}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div class="px-5 pb-5 pt-3.5 border-t border-stone-100 bg-[#FAF6F0]/60 flex items-center justify-between gap-3">
        <div>
          <span class="block text-xs text-stone-500 font-medium">
            Precio por Libra (500 g)
          </span>
          <span class="text-xl font-extrabold text-[#232323]">
            {formatearPesosCOP(lote.precioLibraCop)}
          </span>
          <span class="block text-[11px] text-[#54121B] font-bold">
            Suscripción (-10%):{" "}
            {formatearPesosCOP(Math.round(lote.precioLibraCop * 0.9))}
          </span>
        </div>

        <a
          href={enlaceDetalle}
          class="bg-[#2C4234] hover:bg-[#54121B] text-white font-bold text-sm px-4 py-3 rounded-xl transition-colors text-center min-h-[44px] flex items-center"
        >
          Personalizar
        </a>
      </div>
    </article>
  );
}
