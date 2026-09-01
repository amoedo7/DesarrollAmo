import { getStore } from "@netlify/blobs";
import {
  VISIBILITY_UNIT_PRICE_ARS,
  parseVisibilityUnits,
  verifyMercadoPagoSignature,
  visibilityAmountFromUnits,
} from "./rankeamo-security.mts";

const STORE = "rankeamo-v1";
const MAX_WEBHOOK_BYTES = 256 * 1024;

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

function token() {
  return Netlify.env.get("MERCADOPAGO_ACCESS_TOKEN")?.trim() || "";
}

function webhookSecret() {
  return (
    Netlify.env.get("MERCADOPAGO_WEBHOOK_SECRET")?.trim() ||
    Netlify.env.get("MP_WEBHOOK_SECRET")?.trim() ||
    ""
  );
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
    const visibilityUnits = parseVisibilityUnits(body.visibilityUnits);
    const amount = visibilityAmountFromUnits(visibilityUnits);
    const id = crypto.randomUUID();
    const idempotencyKey = crypto.randomUUID();
    const origin = new URL(req.url).origin;
    const store = getStore(STORE, { consistency: "strong" });

    const pending = {
      id,
      projectName,
      url,
      visibilityUnits,
      amount,
      currency: "ARS",
      idempotencyKey,
      status: "pending",
      createdAt: new Date().toISOString(),
    };
    await store.setJSON(`pending/${id}`, pending);

    const preferenceRes = await fetch("https://api.mercadopago.com/checkout/preferences", {
      method: "POST",
      headers: {
        authorization: `Bearer ${accessToken}`,
        "content-type": "application/json",
        "x-idempotency-key": idempotencyKey,
      },
      body: JSON.stringify({
        items: [
          {
            id: "rankeamo-position",
            title: `RankeAMO · ${projectName}`,
            description: "Posición de visibilidad en RankeAMO",
            quantity: visibilityUnits,
            currency_id: "ARS",
            unit_price: VISIBILITY_UNIT_PRICE_ARS,
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
  if (req.method !== "POST") return new Response("Método no permitido", { status: 405 });
  const accessToken = token();
  const secret = webhookSecret();
  if (!accessToken || !secret) {
    console.error("RankeAMO webhook is missing Mercado Pago credentials");
    return new Response("Webhook no configurado", { status: 503 });
  }

  const contentLength = Number(req.headers.get("content-length") || 0);
  if (Number.isFinite(contentLength) && contentLength > MAX_WEBHOOK_BYTES) {
    return new Response("Payload demasiado grande", { status: 413 });
  }

  let body: any = {};
  try {
    const rawBody = await req.text();
    if (rawBody.length > MAX_WEBHOOK_BYTES) return new Response("Payload demasiado grande", { status: 413 });
    body = JSON.parse(rawBody);
  } catch {
    return new Response("JSON inválido", { status: 400 });
  }

  const requestUrl = new URL(req.url);
  const queryType = requestUrl.searchParams.get("type") || requestUrl.searchParams.get("topic") || "";
  const bodyType = String(body?.type || "").trim();
  const queryPaymentId = String(requestUrl.searchParams.get("data.id") || "").trim();
  const bodyPaymentId = String(body?.data?.id || "").trim();
  const signature = req.headers.get("x-signature") || "";
  const requestId = req.headers.get("x-request-id") || "";

  if ((queryType && queryType !== "payment") || (bodyType && bodyType !== "payment")) {
    return new Response("ok", { status: 200 });
  }
  if (!queryPaymentId || !/^\d+$/.test(queryPaymentId)) return new Response("Notificación inválida", { status: 400 });
  if (bodyPaymentId && bodyPaymentId !== queryPaymentId) return new Response("Notificación inválida", { status: 401 });

  if (!verifyMercadoPagoSignature({
    signature,
    requestId,
    dataId: queryPaymentId,
    secret,
  })) {
    return new Response("Firma inválida", { status: 401 });
  }

  const paymentId = queryPaymentId;

  try {
    const paymentRes = await fetch(`https://api.mercadopago.com/v1/payments/${encodeURIComponent(paymentId)}`, {
      headers: { authorization: `Bearer ${accessToken}` },
    });
    if (!paymentRes.ok) {
      console.error("RankeAMO payment lookup error", { paymentId, status: paymentRes.status });
      return new Response("No se pudo verificar el pago", { status: 502 });
    }

    const payment: any = await paymentRes.json();
    const ref = String(payment?.external_reference || "").trim();
    if (!/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(ref)) {
      return new Response("ok", { status: 200 });
    }

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
    return new Response("Error temporal", { status: 500 });
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
