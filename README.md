# Maicofi — Plataforma E-Commerce de Café Especial del Tolima

<p align="center">
  <img src="frontend/static/logo/Logo-Completo.png" alt="Logo Maicofi" width="220" />
</p>

**Maicofi** es una plataforma web *e-commerce* responsive diseñada para conectar directamente —sin intermediarios— a las familias caficultoras del departamento del **Tolima, Colombia** (*Planadas, Líbano, Santa Isabel, Anzoátegui, Herrera/Rioblanco, Ibagué, Chaparral, Ataco*) con compradores finales y tostadores mayoristas.

---

## 1. Stack Tecnológico y Versiones

- **Backend:** **Python 3.12** con **FastAPI**, **SQLAlchemy 2.0**, **Psycopg 3**, **Pydantic v2**, **bcrypt** y **httpx**.
- **Frontend:** **Fresh Framework** sobre **Deno 2.9.5** (V8 15.0) con **TypeScript 6.0.3**, **Preact Signals** y **Tailwind CSS** (SSR nativo + arquitectura de Islas).
  - *Restricción de Arquitectura:* **0% Node.js** (sin `npm` ni `package.json`). Gestión íntegra de módulos mediante `deno.json` y **JSR**.
- **Base de Datos:** **PostgreSQL 18** (`postgres:18-alpine`).

---

## 2. Módulos y Funcionalidades Principales

1. **UX Rural para Caficultores del Tolima (`/producer/panel`):**
   - Registro y gestión del perfil de finca (municipio, vereda, altura `m.s.n.m.`, historia familiar y coordenadas GPS).
   - Publicación de lotes de cosecha con conversión automática entre **Libras (500 g)**, **Kilos (1 kg)**, **Arrobas (12.5 kg)** y **Cargas (125 kg)**.
   - Subida móvil de fotografías integrada con **Cloudinary CDN** y conversión automática a formato ligero **`WebP`**.
2. **Catálogo de Especialidad, Perfil Sensorial y Trazabilidad (`/products/[slug]`):**
   - Ficha técnica completa: variedad (*Geisha, Tabi, Bourbon Rosado, Castillo, Caturra*), beneficio (*Lavado, Natural, Honey, Fermentación Anaeróbica*), puntaje en taza **SCA (80 - 100)**, fecha de tueste y control de empaque con válvula desgasificadora.
   - **Perfil Sensorial (`PerfilSensorial.tsx`):** Descriptores aromáticos clasificados por familia sensorial, barras de nivel (1 a 5) para **Acidez**, **Cuerpo** y **Dulzura**, y curva de nivel de tueste.
   - **Configurador Personalizado (`ConfiguradorProducto.tsx`):** Selección de presentación (`250g`, `500g`, `1000g`, `arroba`, `carga`), tipo de molienda (*Grano entero, V60/Chemex, Prensa Francesa, Moka Italiana, Espresso*) y modalidad de **Suscripción Recurrente (-10% de descuento automático)**.
   - **Calculadora de Barismo (`CalculadoraPreparacion.tsx`):** Cálculo en tiempo real de ratios de extracción, gramos de café, mililitros de agua y temperatura ideal según método y número de tazas.
   - **Geolocalización y Storytelling (`MapaFinca.tsx`):** Mapa interactivo gratuito con **Leaflet 1.9.4 + OpenStreetMap** ubicado sobre la vereda productora en el Tolima.
3. **Microservicios de Pago, Logística, Mensajería y Facturación Electrónica DIAN:**
   - **Pasarela Wompi Colombia (`services/wompi.py`):** Firma criptográfica de integridad `SHA-256` y webhook idempotente (`POST /api/v1/payments/webhook`) con verificación `hmac.compare_digest`.
   - **Alertas por WhatsApp y Correo (`services/notificaciones.py`):** Notificación automática al celular del caficultor vía Meta Cloud API / Twilio y envío de confirmación por Resend API.
   - **Cotizador Nacional de Envíos (`services/envios.py`):** Tarifador por peso volumétrico desde municipios del Tolima hacia cualquier ciudad de Colombia.
   - **Facturación Electrónica DIAN (`services/facturacion.py` y `FormularioFacturacion.tsx`):** Captura de datos tributarios (`CC`, `NIT` con cálculo automático de **Dígito de Verificación Módulo 11**, régimen fiscal y código DANE), liquidación de IVA cafetero (`0%` café verde/pergamino, `5%` café tostado), generación de **CUFE (SHA-384)** y descarga de PDF y XML UBL 2.1 (`/orders/[id]`).

---

## 3. Estructura del Proyecto

```text
Maicofi/
├── Logo/                               # Activos oficiales de identidad visual Maicofi
├── .env.example                        # Plantilla de variables de entorno
├── .gitignore
├── .dockerignore
├── docker-compose.yml                  # Servicio PostgreSQL 18 aislado en 127.0.0.1
├── backend/
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── core/                       # Configuración, JWT + HttpOnly Cookie, Rate Limiting y cabeceras HTTP
│       ├── db/                         # Conexión SQLAlchemy 2.0 y semilla de datos del Tolima
│       ├── models/                     # Entidades relacionales (Usuario, Finca, LoteCafe, PerfilSensorial, Pedido, FacturaElectronica)
│       ├── schemas/                    # Esquemas Pydantic v2 con validación y alias de contrato externo
│       ├── services/                   # Integraciones (Wompi, Facturación DIAN, WhatsApp, Correo, Cloudinary, Envíos)
│       └── routers/                    # Controladores RESTful (/auth, /producers, /farmers, /products, /subscriptions, /orders, /payments, /invoices)
└── frontend/
    ├── deno.json                       # Configuración Deno 2.9.5 + TypeScript 6.0.3 (0% Node.js)
    ├── dev.ts
    ├── main.ts
    ├── fresh.config.ts
    ├── fresh.gen.ts
    ├── tailwind.config.ts
    ├── static/
    ├── utils/
    ├── components/                     # Encabezado.tsx, TarjetaProducto.tsx, PerfilSensorial.tsx
    ├── islands/                        # CanastaCompra, ConfiguradorProducto, CalculadoraPreparacion, FormularioCaficultor, FormularioFacturacion, MapaFinca, BotonPagoWompi, SubidorImagen
    └── routes/                         # index.tsx, products/[slug].tsx, producer/panel.tsx, orders/[id].tsx
```

---

## 4. Guía de Instalación y Ejecución

### Paso 1: Variables de Entorno y Base de Datos (PostgreSQL 18)
```powershell
Copy-Item .env.example .env
docker compose up -d
```

### Paso 2: Backend (Python 3.12 + FastAPI)
```powershell
python -m venv backend\.venv
.\backend\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt

# Poblar semilla inicial de fincas, lotes y planes de suscripción del Tolima
$env:PYTHONPATH="backend"; python -m app.db.semilla

# Iniciar servidor API REST en http://127.0.0.1:8001 (Documentación en http://127.0.0.1:8001/docs)
uvicorn app.main:app --reload --port 8001 --app-dir backend
```

### Paso 3: Frontend (Deno 2.9.5 + Fresh)
```powershell
deno task --cwd frontend start
```
El marketplace estará disponible en **`http://localhost:8000`**.
