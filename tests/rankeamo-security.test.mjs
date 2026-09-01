import assert from "node:assert/strict";
import { createHmac } from "node:crypto";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  MAX_VISIBILITY_UNITS,
  VISIBILITY_UNIT_PRICE_ARS,
  parseVisibilityUnits,
  verifyMercadoPagoSignature,
  visibilityAmountFromUnits,
} from "../netlify/functions/rankeamo-security.mts";

function signedNotification({ dataId = "123456789", requestId = "req-123", secret = "whsec-test", nowMs, milliseconds = false }) {
  const timestamp = String(milliseconds ? nowMs : Math.floor(nowMs / 1000));
  const manifest = `id:${dataId};request-id:${requestId};ts:${timestamp};`;
  const digest = createHmac("sha256", secret).update(manifest).digest("hex");
  return { dataId, requestId, secret, nowMs, signature: `ts=${timestamp},v1=${digest}` };
}

test("el servidor calcula el monto desde unidades de precio fijo", () => {
  assert.equal(VISIBILITY_UNIT_PRICE_ARS, 1000);
  assert.equal(parseVisibilityUnits(5), 5);
  assert.equal(visibilityAmountFromUnits(5), 5000);
  assert.equal(visibilityAmountFromUnits(MAX_VISIBILITY_UNITS), 100000000);
  for (const invalid of [0, -1, 1.5, "5", NaN, Infinity, MAX_VISIBILITY_UNITS + 1]) {
    assert.throws(() => parseVisibilityUnits(invalid));
  }
});

test("acepta firmas válidas con timestamp en segundos o milisegundos", () => {
  const nowMs = Date.UTC(2026, 8, 1, 12, 0, 0);
  assert.equal(verifyMercadoPagoSignature(signedNotification({ nowMs })), true);
  assert.equal(verifyMercadoPagoSignature(signedNotification({ nowMs, milliseconds: true })), true);
});

test("rechaza firma alterada, campos alterados y replay fuera de ventana", () => {
  const nowMs = Date.UTC(2026, 8, 1, 12, 0, 0);
  const valid = signedNotification({ nowMs });
  const lastCharacter = valid.signature.at(-1);
  const tamperedSignature = `${valid.signature.slice(0, -1)}${lastCharacter === "0" ? "1" : "0"}`;
  assert.equal(verifyMercadoPagoSignature({ ...valid, requestId: "otro" }), false);
  assert.equal(verifyMercadoPagoSignature({ ...valid, dataId: "987654321" }), false);
  assert.equal(verifyMercadoPagoSignature({ ...valid, signature: tamperedSignature }), false);
  assert.equal(verifyMercadoPagoSignature({ ...valid, nowMs: nowMs + 301000 }), false);
  assert.equal(verifyMercadoPagoSignature({ ...valid, signature: "ts=bad,v1=no" }), false);
});

test("el handler verifica firma antes de consultar el pago y envía idempotencia", async () => {
  const source = await readFile(new URL("../netlify/functions/rankeamo.mts", import.meta.url), "utf8");
  const frontend = await readFile(new URL("../rankeamo/index.html", import.meta.url), "utf8");
  const webhook = source.slice(source.indexOf("async function webhook"));
  assert.ok(webhook.indexOf("verifyMercadoPagoSignature") < webhook.indexOf("/v1/payments/"));
  assert.match(source, /"x-idempotency-key": idempotencyKey/);
  assert.doesNotMatch(source, /body\.amount/);
  assert.match(source, /unit_price: VISIBILITY_UNIT_PRICE_ARS/);
  assert.match(frontend, /step="1000"/);
  assert.match(frontend, /visibilityUnits:selectedAmount\/unitPrice/);
  assert.doesNotMatch(frontend, /amount:Number\(form\.amount\.value\)/);
});
