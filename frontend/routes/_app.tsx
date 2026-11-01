import { type PageProps } from "$fresh/server.ts";

export default function App({ Component }: PageProps) {
  return (
    <html lang="es-CO">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Maicofi | Café Especial del Tolima Directo del Caficultor</title>
        <meta
          name="description"
          content="Comercialización directa de café especial producido en el departamento del Tolima, Colombia: Planadas, Líbano, Santa Isabel, Anzoátegui, Herrera e Ibagué."
        />
        <link rel="icon" type="image/png" href="/logo/Logo.png" />
        <link
          rel="stylesheet"
          href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
          crossorigin=""
        />
        <link rel="stylesheet" href="/styles.css" />
      </head>
      <body class="bg-[#FAF6F0] text-[#232323] antialiased selection:bg-[#54121B] selection:text-white">
        <Component />
      </body>
    </html>
  );
}
