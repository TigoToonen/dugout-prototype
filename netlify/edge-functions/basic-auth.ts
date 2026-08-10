// Basic-auth gate voor de hele Commerciële Dugout.
// Zet de héle site achter één gedeeld wachtwoord, vóór er iets laadt.
// Sluit Jeroen's punt af: alles buiten Supabase (testdata, namen, layout)
// is anders leesbaar met alleen de link.
//
// Credentials komen uit Netlify env-vars (Site settings -> Environment variables),
// NIET uit de code:
//   BASIC_AUTH_USER
//   BASIC_AUTH_PASSWORD
//
// Config staat in netlify.toml (path = "/*").

import type { Context } from "https://edge.netlify.com";

// Constant-time vergelijking, voorkomt timing-aanvallen op het wachtwoord.
function safeEqual(a: string, b: string): boolean {
  const enc = new TextEncoder();
  const ab = enc.encode(a);
  const bb = enc.encode(b);
  if (ab.length !== bb.length) return false;
  let diff = 0;
  for (let i = 0; i < ab.length; i++) diff |= ab[i] ^ bb[i];
  return diff === 0;
}

export default async function handler(request: Request, context: Context) {
  const USER = Deno.env.get("BASIC_AUTH_USER");
  const PASS = Deno.env.get("BASIC_AUTH_PASSWORD");

  // Als de env-vars (nog) niet zijn ingesteld: niet dichtgooien, gewoon
  // doorlaten. Voorkomt dat de site per ongeluk volledig op slot gaat.
  if (!USER || !PASS) {
    return context.next();
  }

  const header = request.headers.get("authorization") || "";
  const [scheme, encoded] = header.split(" ");

  if (scheme === "Basic" && encoded) {
    let decoded = "";
    try {
      decoded = atob(encoded);
    } catch {
      decoded = "";
    }
    const idx = decoded.indexOf(":");
    if (idx !== -1) {
      const u = decoded.slice(0, idx);
      const p = decoded.slice(idx + 1);
      // Beide checks altijd uitvoeren (geen early-return) tegen timing-lek.
      const okUser = safeEqual(u, USER);
      const okPass = safeEqual(p, PASS);
      if (okUser && okPass) {
        return context.next();
      }
    }
  }

  return new Response("Authenticatie vereist.", {
    status: 401,
    headers: {
      "WWW-Authenticate": 'Basic realm="Commerciele Dugout", charset="UTF-8"',
      "content-type": "text/plain; charset=utf-8",
    },
  });
}
