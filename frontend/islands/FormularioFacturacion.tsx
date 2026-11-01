import { useEffect, useState } from "preact/hooks";

export interface DatosFiscalesFormulario {
  tipoDocumento: "CC" | "NIT" | "CE" | "PASAPORTE";
  numeroDocumento: string;
  digitoVerificacion: string;
  razonSocialONombre: string;
  correoFacturacion: string;
  tipoPersona: "Natural" | "Jurídica";
  regimenTributario:
    | "No Responsable de IVA"
    | "Responsable de IVA"
    | "Régimen Simple de Tributación (RST)"
    | "Gran Contribuyente";
  direccionFiscal: string;
  codigoMunicipioDane: string;
}

interface PropiedadesFormularioFacturacion {
  direccionPredeterminada?: string;
  alCambiarDatosFiscales: (datos: DatosFiscalesFormulario | null) => void;
}

const FACTORES_MODULO_11_DIAN = [
  3,
  7,
  13,
  17,
  19,
  23,
  29,
  37,
  41,
  43,
  47,
  53,
  59,
  67,
  71,
];

export function calcularDigitoVerificacionNitDian(nit: string): string {
  const digitos = nit.replace(/\D/g, "");
  if (!digitos) return "0";
  let suma = 0;
  const invertidos = digitos.split("").reverse();
  for (let i = 0; i < invertidos.length && i < FACTORES_MODULO_11_DIAN.length; i++) {
    suma += parseInt(invertidos[i], 10) * FACTORES_MODULO_11_DIAN[i];
  }
  const residuo = suma % 11;
  return residuo > 1 ? String(11 - residuo) : String(residuo);
}

export const MUNICIPIOS_DANE_COLOMBIA = [
  { codigo: "73001", nombre: "Ibagué, Tolima (73001)" },
  { codigo: "73555", nombre: "Planadas, Tolima (73555)" },
  { codigo: "73411", nombre: "Líbano, Tolima (73411)" },
  { codigo: "73686", nombre: "Santa Isabel, Tolima (73686)" },
  { codigo: "73043", nombre: "Anzoátegui, Tolima (73043)" },
  { codigo: "73616", nombre: "Rioblanco / Herrera, Tolima (73616)" },
  { codigo: "73168", nombre: "Chaparral, Tolima (73168)" },
  { codigo: "73067", nombre: "Ataco, Tolima (73067)" },
  { codigo: "73283", nombre: "Fresno, Tolima (73283)" },
  { codigo: "73622", nombre: "Roncesvalles, Tolima (73622)" },
  { codigo: "73124", nombre: "Cajamarca, Tolima (73124)" },
  { codigo: "11001", nombre: "Bogotá D.C. (11001)" },
  { codigo: "05001", nombre: "Medellín, Antioquia (05001)" },
  { codigo: "76001", nombre: "Cali, Valle del Cauca (76001)" },
  { codigo: "66001", nombre: "Pereira, Risaralda (66001)" },
  { codigo: "17001", nombre: "Manizales, Caldas (17001)" },
];

export default function FormularioFacturacion({
  direccionPredeterminada = "",
  alCambiarDatosFiscales,
}: PropiedadesFormularioFacturacion) {
  const [requiereFacturaNominal, setRequiereFacturaNominal] = useState(true);
  const [tipoPersona, setTipoPersona] = useState<"Natural" | "Jurídica">(
    "Natural",
  );
  const [tipoDocumento, setTipoDocumento] = useState<
    "CC" | "NIT" | "CE" | "PASAPORTE"
  >("CC");
  const [numeroDocumento, setNumeroDocumento] = useState("");
  const [digitoVerificacion, setDigitoVerificacion] = useState("");
  const [razonSocialONombre, setRazonSocialONombre] = useState("");
  const [correoFacturacion, setCorreoFacturacion] = useState("");
  const [regimenTributario, setRegimenTributario] = useState<
    DatosFiscalesFormulario["regimenTributario"]
  >("No Responsable de IVA");
  const [direccionFiscal, setDireccionFiscal] = useState(
    direccionPredeterminada,
  );
  const [codigoMunicipioDane, setCodigoMunicipioDane] = useState("73001");
  const [errorValidacionDocumento, setErrorValidacionDocumento] = useState<
    string | null
  >(null);

  useEffect(() => {
    if (direccionPredeterminada && !direccionFiscal) {
      setDireccionFiscal(direccionPredeterminada);
    }
  }, [direccionPredeterminada]);

  useEffect(() => {
    if (!requiereFacturaNominal) {
      alCambiarDatosFiscales(null);
      return;
    }

    const limpio = numeroDocumento.trim();
    let dvActual = digitoVerificacion;

    if (tipoDocumento === "NIT") {
      const soloDigitos = limpio.replace(/\D/g, "");
      if (soloDigitos.length > 0 && (soloDigitos.length < 8 || soloDigitos.length > 10)) {
        setErrorValidacionDocumento(
          "El NIT en Colombia debe contener entre 8 y 10 dígitos sin el DV.",
        );
      } else {
        setErrorValidacionDocumento(null);
      }
      dvActual = calcularDigitoVerificacionNitDian(soloDigitos);
      setDigitoVerificacion(dvActual);
    } else if (tipoDocumento === "CC") {
      const soloDigitos = limpio.replace(/\D/g, "");
      if (soloDigitos.length > 0 && (soloDigitos.length < 6 || soloDigitos.length > 10)) {
        setErrorValidacionDocumento(
          "La Cédula de Ciudadanía debe tener entre 6 y 10 dígitos numéricos.",
        );
      } else {
        setErrorValidacionDocumento(null);
      }
      dvActual = "";
      setDigitoVerificacion("");
    } else {
      setErrorValidacionDocumento(null);
    }

    if (limpio.length >= 5 && razonSocialONombre.trim().length >= 3 && correoFacturacion.includes("@")) {
      alCambiarDatosFiscales({
        tipoDocumento,
        numeroDocumento: limpio,
        digitoVerificacion: dvActual,
        razonSocialONombre: razonSocialONombre.trim(),
        correoFacturacion: correoFacturacion.trim(),
        tipoPersona,
        regimenTributario,
        direccionFiscal: (direccionFiscal || direccionPredeterminada || "Ibagué, Tolima").trim(),
        codigoMunicipioDane,
      });
    }
  }, [
    requiereFacturaNominal,
    tipoPersona,
    tipoDocumento,
    numeroDocumento,
    razonSocialONombre,
    correoFacturacion,
    regimenTributario,
    direccionFiscal,
    direccionPredeterminada,
    codigoMunicipioDane,
  ]);

  return (
    <div class="bg-[#FAF6F0] p-4 rounded-2xl border border-[#E5D5C5] space-y-3">
      <div class="flex items-center justify-between">
        <div>
          <span class="block text-xs font-extrabold uppercase tracking-wider text-[#2C4234]">
            Facturación Electrónica DIAN (Anexo 1.9)
          </span>
          <span class="text-[11px] text-stone-600">
            Datos tributarios para emisión de CUFE y representación gráfica PDF.
          </span>
        </div>
        <button
          type="button"
          onClick={() => setRequiereFacturaNominal((v) => !v)}
          class="text-[11px] font-bold text-[#54121B] underline"
        >
          {requiereFacturaNominal ? "Usar Consumidor Final" : "Personalizar NIT/CC"}
        </button>
      </div>

      {requiereFacturaNominal && (
        <div class="space-y-2.5 pt-1">
          {/* Selector de Tipo de Persona */}
          <div class="grid grid-cols-2 gap-2">
            {(["Natural", "Jurídica"] as const).map((tp) => (
              <button
                type="button"
                key={tp}
                onClick={() => {
                  setTipoPersona(tp);
                  if (tp === "Jurídica") {
                    setTipoDocumento("NIT");
                    setRegimenTributario("Responsable de IVA");
                  } else {
                    setTipoDocumento("CC");
                    setRegimenTributario("No Responsable de IVA");
                  }
                }}
                class={`py-2 px-3 rounded-xl text-xs font-extrabold border transition-all ${
                  tipoPersona === tp
                    ? "bg-[#2C4234] text-white border-[#2C4234]"
                    : "bg-white text-stone-700 border-stone-300"
                }`}
              >
                Persona {tp}
              </button>
            ))}
          </div>

          {/* Tipo y Número de Documento + DV Automático */}
          <div class="grid grid-cols-12 gap-2">
            <div class="col-span-4">
              <label class="block text-[11px] font-bold text-stone-700 mb-0.5">
                Tipo Doc.
              </label>
              <select
                value={tipoDocumento}
                onChange={(e) =>
                  setTipoDocumento(
                    (e.target as HTMLSelectElement)
                      .value as DatosFiscalesFormulario["tipoDocumento"],
                  )}
                class="w-full px-2.5 py-2 rounded-xl border border-stone-300 text-xs font-bold bg-white"
              >
                <option value="CC">CC (Cédula)</option>
                <option value="NIT">NIT (Empresa)</option>
                <option value="CE">CE</option>
                <option value="PASAPORTE">Pasaporte</option>
              </select>
            </div>

            <div class={tipoDocumento === "NIT" ? "col-span-6" : "col-span-8"}>
              <label class="block text-[11px] font-bold text-stone-700 mb-0.5">
                {tipoDocumento === "NIT" ? "Número NIT (sin DV)" : "Número Documento"}
              </label>
              <input
                type="text"
                required
                placeholder={tipoDocumento === "NIT" ? "Ej: 901456789" : "Ej: 1110456789"}
                value={numeroDocumento}
                onInput={(e) =>
                  setNumeroDocumento((e.target as HTMLInputElement).value)}
                class="w-full px-3 py-2 rounded-xl border border-stone-300 text-xs bg-white font-mono"
              />
            </div>

            {tipoDocumento === "NIT" && (
              <div class="col-span-2">
                <label class="block text-[11px] font-bold text-[#54121B] mb-0.5">
                  DV
                </label>
                <input
                  type="text"
                  readOnly
                  value={digitoVerificacion}
                  class="w-full px-2 py-2 rounded-xl border border-[#54121B] text-xs font-extrabold text-center bg-white text-[#54121B]"
                  title="Dígito de verificación calculado con Módulo 11 DIAN"
                />
              </div>
            )}
          </div>

          {errorValidacionDocumento && (
            <p class="text-[11px] font-semibold text-red-700">
              {errorValidacionDocumento}
            </p>
          )}

          {/* Razón Social o Nombre Completo */}
          <div>
            <label class="block text-[11px] font-bold text-stone-700 mb-0.5">
              {tipoPersona === "Jurídica"
                ? "Razón Social registrada en el RUT"
                : "Nombres y Apellidos del Adquirente"}
            </label>
            <input
              type="text"
              required
              maxLength={180}
              placeholder={
                tipoPersona === "Jurídica"
                  ? "Ej: Tostadora Tolima Especial S.A.S."
                  : "Ej: Carlos Andrés Gómez"
              }
              value={razonSocialONombre}
              onInput={(e) =>
                setRazonSocialONombre((e.target as HTMLInputElement).value)}
              class="w-full px-3 py-2 rounded-xl border border-stone-300 text-xs bg-white"
            />
          </div>

          {/* Correo de Recepción XML/PDF DIAN y Régimen Tributario */}
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <div>
              <label class="block text-[11px] font-bold text-stone-700 mb-0.5">
                Correo Recepción Factura DIAN
              </label>
              <input
                type="email"
                required
                placeholder="facturacion@empresa.co"
                value={correoFacturacion}
                onInput={(e) =>
                  setCorreoFacturacion((e.target as HTMLInputElement).value)}
                class="w-full px-3 py-2 rounded-xl border border-stone-300 text-xs bg-white"
              />
            </div>

            <div>
              <label class="block text-[11px] font-bold text-stone-700 mb-0.5">
                Régimen Tributario
              </label>
              <select
                value={regimenTributario}
                onChange={(e) =>
                  setRegimenTributario(
                    (e.target as HTMLSelectElement)
                      .value as DatosFiscalesFormulario["regimenTributario"],
                  )}
                class="w-full px-2.5 py-2 rounded-xl border border-stone-300 text-xs font-semibold bg-white"
              >
                <option value="No Responsable de IVA">
                  No Responsable de IVA
                </option>
                <option value="Responsable de IVA">
                  Responsable de IVA (Común)
                </option>
                <option value="Régimen Simple de Tributación (RST)">
                  Régimen Simple (RST)
                </option>
                <option value="Gran Contribuyente">Gran Contribuyente</option>
              </select>
            </div>
          </div>

          {/* Municipio Código DANE */}
          <div>
            <label class="block text-[11px] font-bold text-stone-700 mb-0.5">
              Municipio Fiscal (Código DANE Oficial)
            </label>
            <select
              value={codigoMunicipioDane}
              onChange={(e) =>
                setCodigoMunicipioDane((e.target as HTMLSelectElement).value)}
              class="w-full px-2.5 py-2 rounded-xl border border-stone-300 text-xs font-semibold bg-white"
            >
              {MUNICIPIOS_DANE_COLOMBIA.map((mun) => (
                <option key={mun.codigo} value={mun.codigo}>
                  {mun.nombre}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}
    </div>
  );
}
