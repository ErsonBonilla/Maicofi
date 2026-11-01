import { FreshContext } from "$fresh/server.ts";

export async function handler(
  _req: Request,
  ctx: FreshContext,
): Promise<Response> {
  const respuesta = await ctx.next();

  respuesta.headers.set("X-Content-Type-Options", "nosniff");
  respuesta.headers.set("X-Frame-Options", "DENY");
  respuesta.headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
  respuesta.headers.set(
    "Permissions-Policy",
    "geolocation=(), microphone=(), camera=()",
  );
  respuesta.headers.set(
    "Content-Security-Policy",
    [
      "default-src 'self'",
      "img-src 'self' https://images.unsplash.com https://res.cloudinary.com https://*.tile.openstreetmap.org https://unpkg.com data: blob:",
      "style-src 'self' 'unsafe-inline' https://unpkg.com",
      "script-src 'self' 'unsafe-inline' https://unpkg.com https://checkout.wompi.co",
      "connect-src 'self' http://127.0.0.1:8001 http://localhost:8001 https://sandbox.wompi.co https://checkout.wompi.co",
      "frame-ancestors 'none'",
    ].join("; "),
  );

  return respuesta;
}
