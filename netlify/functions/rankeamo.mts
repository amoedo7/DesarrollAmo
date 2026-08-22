import { getStore } from "@netlify/blobs";

const STORE = "rankeamo-v1";
const MIN_AMOUNT = 1000;
const MAX_AMOUNT = 100000000;

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });
}

function normalizeUrl(value: unknown) {
  const raw = String(value ?? "").trim();
  if (raw.length < 8 || raw.length > 300) throw new Error("El enlace no es válido.");
  const url = new URL(raw);
  if (!["http:", "https:"].includes(url.protocol)) throw new Error("El enlace debe empezar con http:// o https://");
  url.hash = "";
  return url.toString();
}

function cleanName(value: unknown) {
  const name = String(value ?? "").trim().replace(/\s+/g, " ");
  if (name.length < 2 || name.length > 60) throw new Error("El nombre debe tener entre 2 y 60 caracteres.");
  return name;
}

function parseAmount(value: unknown) {
  const amount = Number(value);
  if (!Number.isFinite(amount) || amount < MIN_AMOUNT || amount > MAX_AMOUNT) {
    throw new Error(`El aporte debe ser de al menos $${MIN_AMOUNT.toLocaleString("es-AR")} ARS.`);
  }
  return Math.round(amount * 100) / 100;
}

function token() {
  return Netlify.env.get("MERCADOPAGO_ACCESS_TOKEN")?.trim() || "";
}

async function listEntries() {
  const store = getStore(STORE, { consistency: "strong" });
  const { blobs } = await store.list({ prefix: "entries/" });
  const entries = (
    await Promise.all(
      blobs.map(async ({ key }) => {
        try {
          return await store.get(key, { type: "json" });
        } catch {
          return null;
        }
      })
    )
  )
    .filter(Boolean)
    .filter((x: any) => x.status === "approved")
    .sort((a: any, b: any) => Number(b.amount) - Number(a.amount) || String(a.paidAt).localeCompare(String(b.paidAt)))
    .map((x: any) => ({
      id: x.id,
      projectName: x.projectName,
      url: x.url,
      amount: x.amount,
      currency: "ARS",
      paidAt: x.paidAt,
    }));
  return entries;
}

async function checkout(req: Request) {
  if (req.method !== "POST") return json({ error: "Método no permitido." }, 405);

  const accessToken = token();
  if (!accessToken) {
    return json({ error: "RankeAMO ya está online, pero Mercado Pago todavía no está conectado." }, 503);
  }

  let body: any;
  try {
    body = await req.json();
  } catch {
    return json({ error: "Datos inválidos." }, 400);
  }

  try {
    const projectName = cleanName(body.projectName);
    const url = normalizeUrl(body.url);
    const amount = parseAmount(body.amount);
    const id = crypto.randomUUID();
    const origin = new URL(req.url).origin;
    const store = getStore(STORE, { consistency: "strong" });

    const pending = {
      id,
      projectName,
      url,
      amount,
      currency: "ARS",
      status: "pending",
      createdAt: new Date().toISOString(),
    };
    await store.setJSON(`pending/${id}`, pending);

    const preferenceRes = await fetch("https://api.mercadopago.com/checkout/preferences", {
      method: "POST",
      headers: {
        authorization: `Bearer ${accessToken}`,
        "content-type": "application/json",
      },
      body: JSON.stringify({
        items: [
          {
            id: "rankeamo-position",
            title: `RankeAMO · ${projectName}`,
            description: "Posición de visibilidad en RankeAMO",
            quantity: 1,
            currency_id: "ARS",
            unit_price: amount,
          },
        ],
        external_reference: id,
        notification_url: `${origin}/api/rankeamo/webhook`,
        back_urls: {
          success: `${origin}/rankeamo/?payment=approved`,
          pending: `${origin}/rankeamo/?payment=pending`,
          failure: `${origin}/rankeamo/?payment=failure`,
        },
        auto_return: "approved",
      }),
    });

    const preference = await preferenceRes.json().catch(() => ({}));
    if (!preferenceRes.ok || !preference?.init_point) {
      await store.delete(`pending/${id}`);
      console.error("Mercado Pago preference error", preferenceRes.status, preference);
      return json({ error: "Mercado Pago no pudo preparar el pago." }, 502);
    }

    return json({ checkoutUrl: preference.init_point });
  } catch (error: any) {
    return json({ error: error?.message || "No se pudo iniciar el pago." }, 400);
  }
}

async function webhook(req: Request) {
  if (req.method !== "POST" && req.method !== "GET") return new Response("ok", { status: 200 });
  const accessToken = token();
  if (!accessToken) return new Response("ok", { status: 200 });

  let body: any = {};
  if (req.method === "POST") {
    try { body = await req.json(); } catch {}
  }

  const requestUrl = new URL(req.url);
  const type = body?.type || requestUrl.searchParams.get("type") || requestUrl.searchParams.get("topic");
  const paymentId = String(body?.data?.id || requestUrl.searchParams.get("data.id") || requestUrl.searchParams.get("id") || "").trim();

  if (type && type !== "payment") return new Response("ok", { status: 200 });
  if (!paymentId || !/^\d+$/.test(paymentId)) return new Response("ok", { status: 200 });

  try {
    const paymentRes = await fetch(`https://api.mercadopago.com/v1/payments/${encodeURIComponent(paymentId)}`, {
      headers: { authorization: `Bearer ${accessToken}` },
    });
    if (!paymentRes.ok) return new Response("ok", { status: 200 });

    const payment: any = await paymentRes.json();
    const ref = String(payment?.external_reference || "").trim();
    if (!ref) return new Response("ok", { status: 200 });

    const store = getStore(STORE, { consistency: "strong" });
    const existing: any = await store.get(`entries/${ref}`, { type: "json" });
    const pending: any = await store.get(`pending/${ref}`, { type: "json" });

    if (payment.status !== "approved") {
      if (existing && String(existing.paymentId) === paymentId &&
          ["refunded", "charged_back", "cancelled"].includes(String(payment.status))) {
        await store.delete(`entries/${ref}`);
      }
      return new Response("ok", { status: 200 });
    }

    if (String(payment.currency_id) !== "ARS") return new Response("ok", { status: 200 });

    const source = pending || existing;
    if (!source) return new Response("ok", { status: 200 });

    const paidAmount = Number(payment.transaction_amount);
    if (!Number.isFinite(paidAmount) || Math.abs(paidAmount - Number(source.amount)) > 0.01) {
      console.error("RankeAMO amount mismatch", { ref, paidAmount, expected: source.amount });
      return new Response("ok", { status: 200 });
    }

    const entry = {
      id: ref,
      paymentId,
      projectName: source.projectName,
      url: source.url,
      amount: paidAmount,
      currency: "ARS",
      status: "approved",
      createdAt: source.createdAt || new Date().toISOString(),
      paidAt: payment.date_approved || new Date().toISOString(),
    };

    await store.setJSON(`entries/${ref}`, entry);
    if (pending) await store.delete(`pending/${ref}`);
  } catch (error) {
    console.error("RankeAMO webhook error", error);
  }

  return new Response("ok", { status: 200 });
}

export default async (req: Request) => {
  const path = new URL(req.url).pathname;

  if (path === "/api/rankeamo") {
    if (req.method !== "GET") return json({ error: "Método no permitido." }, 405);
    try {
      return json({ entries: await listEntries() });
    } catch (error) {
      console.error("RankeAMO list error", error);
      return json({ error: "No se pudo cargar el ranking." }, 500);
    }
  }

  if (path === "/api/rankeamo/checkout") return checkout(req);
  if (path === "/api/rankeamo/webhook") return webhook(req);
  return json({ error: "No encontrado." }, 404);
};

export const config = {
  path: ["/api/rankeamo", "/api/rankeamo/checkout", "/api/rankeamo/webhook"],
};
