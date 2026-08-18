// Toegangspoort voor de hele Commerciële Dugout.
// Zet de héle site achter één gedeeld wachtwoord, vóór er iets laadt.
//
// v2: eigen inlogPAGINA in plaats van de native browser-popup.
// De popup (WWW-Authenticate) wordt door sommige Chrome-installaties
// (bedrijfsbeleid/extensies) nooit getoond, waardoor je de site niet in
// kunt. Deze pagina werkt in elke browser. Na correct inloggen zet we een
// HttpOnly-cookie (30 dagen), daarna laadt de site direct door.
//
// Credentials komen uit Netlify env-vars (Project configuration -> Environment
// variables), NIET uit de code:
//   BASIC_AUTH_USER
//   BASIC_AUTH_PASSWORD
//
// Een Authorization: Basic-header (bijv. curl -u voor monitoring) blijft ook werken.
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

// Cookie-token: HMAC over een vaste string met user+pass als sleutel.
// Verandert het wachtwoord in Netlify, dan zijn alle oude cookies direct ongeldig.
async function makeToken(user: string, pass: string): Promise<string> {
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw", enc.encode(user + ":" + pass),
    { name: "HMAC", hash: "SHA-256" }, false, ["sign"],
  );
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode("dugout-cookie-v1"));
  return btoa(String.fromCharCode(...new Uint8Array(sig)))
    .replace(/=+$/, "").replace(/\+/g, "-").replace(/\//g, "_");
}

function loginPage(fout: boolean): Response {
  const html = `<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>De Commerciële Dugout · Toegang</title>
<style>
  :root{--bg:#FAF7F4;--surface:#FFFFFF;--border:#EAE3DB;--text:#2B2825;--muted:#6A645C;--soft:#8A837B;--accent:#FF5C01;--accent2:#FFAA00;--red:#C23A2B;--redbg:#FBE7E4}
  @media (prefers-color-scheme:dark){:root{--bg:#191712;--surface:#221F19;--border:#38322A;--text:#F3EFEA;--muted:#ADA69C;--soft:#8B847A;--accent:#FF6A1A;--accent2:#FFB733;--red:#F09A8D;--redbg:#3A1D18}}
  *{box-sizing:border-box}
  body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px;
    font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;background:var(--bg);color:var(--text)}
  .card{width:380px;max-width:100%;background:var(--surface);border:1px solid var(--border);border-radius:20px;
    box-shadow:0 12px 40px rgba(47,47,47,.16);padding:32px 28px}
  h1{font-size:20px;font-weight:800;margin:0 0 4px;text-align:center;letter-spacing:-.01em}
  p{color:var(--muted);font-size:13.5px;margin:0 0 8px;text-align:center}
  label{display:block;font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--soft);font-weight:700;margin:16px 0 6px}
  input{width:100%;padding:11px 12px;border-radius:10px;border:1px solid var(--border);background:var(--bg);color:var(--text);font:inherit;font-size:16px}
  input:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px rgba(255,92,1,.12)}
  button{width:100%;margin-top:20px;padding:12px;border:none;border-radius:10px;cursor:pointer;font:inherit;font-weight:700;color:#fff;
    background:linear-gradient(180deg,var(--accent2),var(--accent));box-shadow:0 2px 8px rgba(255,92,1,.28)}
  button:hover{filter:brightness(1.04)}
  .err{color:var(--red);background:var(--redbg);border-radius:9px;padding:9px 11px;font-size:13px;font-weight:600;margin-top:14px;text-align:center}
</style>
</head>
<body>
<form class="card" method="post" action="/">
  <h1>De Commerciële Dugout</h1>
  <p>Vul het gedeelde toegangswachtwoord in.</p>
  <label for="u">Gebruikersnaam</label>
  <input id="u" name="gebruiker" autocomplete="username" autofocus required>
  <label for="p">Wachtwoord</label>
  <input id="p" name="wachtwoord" type="password" autocomplete="current-password" required>
  ${fout ? '<div class="err">Onjuiste gebruikersnaam of wachtwoord.</div>' : ""}
  <button type="submit">Naar de Dugout</button>
</form>
<script>
  // Supabase invite-/herstel-links dragen hun token in de #hash (bijv.
  // #access_token=...&type=invite). Een gewone form-POST naar "/" gooit die
  // hash weg, waardoor de uitnodiging na de poort niet meer werkt. Door de
  // hash aan de form-action te plakken blijft hij (ook door de 303-redirect
  // heen) in de adresbalk staan en kan de app hem gewoon verwerken.
  if (location.hash) document.querySelector("form").action = "/" + location.hash;
</script>
</body>
</html>`;
  return new Response(html, {
    status: 401,
    headers: {
      "content-type": "text/html; charset=utf-8",
      "cache-control": "no-store",
      // Bewust GEEN WWW-Authenticate-header: dan probeert de browser
      // geen (mogelijk geblokkeerde) native popup te tonen.
    },
  });
}

export default async function handler(request: Request, context: Context) {
  const USER = Deno.env.get("BASIC_AUTH_USER");
  const PASS = Deno.env.get("BASIC_AUTH_PASSWORD");

  // Als de env-vars (nog) niet zijn ingesteld: niet dichtgooien, gewoon
  // doorlaten. Voorkomt dat de site per ongeluk volledig op slot gaat.
  if (!USER || !PASS) {
    return context.next();
  }

  const token = await makeToken(USER, PASS);

  // 1) Geldige cookie -> direct door
  const cookies = request.headers.get("cookie") || "";
  const heeftCookie = cookies.split(/;\s*/).some((c) => c === "dugout_auth=" + token);
  if (heeftCookie) {
    return context.next();
  }

  // 2) Authorization: Basic blijft werken (curl/monitoring/oude sessies)
  const header = request.headers.get("authorization") || "";
  const [scheme, encoded] = header.split(" ");
  if (scheme === "Basic" && encoded) {
    let decoded = "";
    try { decoded = atob(encoded); } catch { decoded = ""; }
    const idx = decoded.indexOf(":");
    if (idx !== -1) {
      // Beide checks altijd uitvoeren (geen early-return) tegen timing-lek.
      const okUser = safeEqual(decoded.slice(0, idx), USER);
      const okPass = safeEqual(decoded.slice(idx + 1), PASS);
      if (okUser && okPass) return context.next();
    }
  }

  // 3) Inlogformulier ingestuurd?
  if (request.method === "POST") {
    const ct = request.headers.get("content-type") || "";
    if (ct.includes("application/x-www-form-urlencoded")) {
      const body = await request.text();
      const params = new URLSearchParams(body);
      const okUser = safeEqual(params.get("gebruiker") || "", USER);
      const okPass = safeEqual(params.get("wachtwoord") || "", PASS);
      if (okUser && okPass) {
        return new Response(null, {
          status: 303,
          headers: {
            "Location": "/",
            "Set-Cookie": `dugout_auth=${token}; Path=/; Max-Age=2592000; Secure; HttpOnly; SameSite=Lax`,
            "cache-control": "no-store",
          },
        });
      }
      return loginPage(true);
    }
  }

  // 4) Geen geldige toegang -> inlogpagina
  return loginPage(false);
}
