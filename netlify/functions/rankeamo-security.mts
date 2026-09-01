import { createHmac, timingSafeEqual } from "node:crypto";

export const VISIBILITY_UNIT_PRICE_ARS = 1000;
export const MAX_VISIBILITY_UNITS = 100000;
export const MP_SIGNATURE_TOLERANCE_MS = 5 * 60 * 1000;

export function parseVisibilityUnits(value) {
  if (typeof value !== "number" || !Number.isInteger(value) || value < 1 || value > MAX_VISIBILITY_UNITS) {
    throw new Error(
      `Elegí entre 1 y ${MAX_VISIBILITY_UNITS.toLocaleString("es-AR")} unidades de visibilidad.`
    );
  }
  return value;
}

export function visibilityAmountFromUnits(units) {
  return parseVisibilityUnits(units) * VISIBILITY_UNIT_PRICE_ARS;
}

function parseSignatureHeader(signature) {
  const parts = new Map();
  for (const part of String(signature ?? "").split(",")) {
    const separator = part.indexOf("=");
    if (separator < 1) continue;
    const key = part.slice(0, separator).trim();
    const value = part.slice(separator + 1).trim();
    if (!key || !value || parts.has(key)) return null;
    parts.set(key, value);
  }
  return parts;
}

export function verifyMercadoPagoSignature({
  signature,
  requestId,
  dataId,
  secret,
  nowMs = Date.now(),
  toleranceMs = MP_SIGNATURE_TOLERANCE_MS,
}) {
  if (!signature || !requestId || !dataId || !secret) return false;

  const parts = parseSignatureHeader(signature);
  const timestamp = parts?.get("ts") ?? "";
  const receivedHex = parts?.get("v1") ?? "";
  if (!/^\d{10,13}$/.test(timestamp) || !/^[a-f\d]{64}$/i.test(receivedHex)) return false;

  const timestampNumber = Number(timestamp);
  if (!Number.isSafeInteger(timestampNumber)) return false;
  const timestampMs = timestampNumber >= 1_000_000_000_000 ? timestampNumber : timestampNumber * 1000;
  if (Math.abs(nowMs - timestampMs) > toleranceMs) return false;

  const manifest = `id:${String(dataId).toLowerCase()};request-id:${requestId};ts:${timestamp};`;
  const expected = createHmac("sha256", secret).update(manifest).digest();
  const received = Buffer.from(receivedHex, "hex");
  return received.length === expected.length && timingSafeEqual(received, expected);
}
