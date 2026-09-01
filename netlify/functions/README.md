# RankeAMO en Netlify

La función necesita dos secretos distintos, limitados al runtime de Functions:

- `MERCADOPAGO_ACCESS_TOKEN`: consulta y crea recursos mediante la API.
- `MERCADOPAGO_WEBHOOK_SECRET` (o el alias `MP_WEBHOOK_SECRET`): valida `x-signature` de Webhooks. Nunca usar el access token como secreto de firma.

En Mercado Pago, el evento **Pagos** debe apuntar por Webhooks a
`https://desarrollamo.com.ar/api/rankeamo/webhook`. El receptor rechaza firmas inválidas,
notificaciones con más de cinco minutos y pagos cuyo monto o moneda no coinciden con la
operación guardada.

RankeAMO vende unidades de visibilidad a un precio fijo de $1.000 ARS. El navegador sólo
envía la cantidad de unidades; el total se calcula y persiste en el servidor antes de crear
la preferencia con una clave UUID de idempotencia.
