#!/usr/bin/env python3
"""Estado de CoinAMO (CAMO) para Termux, sin dependencias externas."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

TOKEN = "0x14ade63350ce5C6723Fd180Ec22A99699bA42894"
POOL = "0xfA4B3835E58d73B06Cc99c0Ed2B1223b74625faD"
NETWORK = "bsc"
API = "https://api.geckoterminal.com/api/v2"
STATE = Path.home() / ".cache" / "desarrollamo" / "camo-status.json"
HEADERS = {
    "Accept": "application/json;version=20230203",
    "User-Agent": "DesarrollAMO-CAMO-Status/1.0",
}


def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.load(response)


def pool_payload() -> dict:
    url = f"{API}/networks/{NETWORK}/pools/{POOL}"
    try:
        return get_json(url)["data"]
    except (urllib.error.HTTPError, KeyError):
        # Si el pool histórico dejó de indexarse, buscamos pools por contrato CAMO.
        url = f"{API}/networks/{NETWORK}/tokens/{TOKEN}/pools?page=1"
        data = get_json(url).get("data", [])
        if not data:
            raise RuntimeError("GeckoTerminal no devuelve ningún pool para CAMO")
        return data[0]


def fnum(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def pct_change(new, old):
    if new is None or old in (None, 0):
        return None
    return ((new - old) / old) * 100.0


def money(value):
    if value is None:
        return "N/D"
    if abs(value) < 0.01:
        return f"US${value:.10f}".rstrip("0").rstrip(".")
    return f"US${value:,.4f}"


def percent(value):
    return "N/D" if value is None else f"{value:+.2f}%"


def extract(data: dict) -> dict:
    attr = data.get("attributes", {})
    rel = data.get("relationships", {})
    token_lower = TOKEN.lower()
    base_id = (((rel.get("base_token") or {}).get("data") or {}).get("id") or "").lower()
    quote_id = (((rel.get("quote_token") or {}).get("data") or {}).get("id") or "").lower()

    if token_lower in quote_id:
        price = fnum(attr.get("quote_token_price_usd"))
    else:
        price = fnum(attr.get("base_token_price_usd"))

    changes = attr.get("price_change_percentage") or {}
    volumes = attr.get("volume_usd") or {}
    txns = attr.get("transactions") or {}
    t24 = txns.get("h24") or {}

    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "pool_name": attr.get("name") or "CAMO pool",
        "pool_address": attr.get("address") or POOL,
        "price_usd": price,
        "change_h24": fnum(changes.get("h24")),
        "liquidity_usd": fnum(attr.get("reserve_in_usd")),
        "volume_h24_usd": fnum(volumes.get("h24")),
        "buys_h24": int(t24.get("buys") or 0),
        "sells_h24": int(t24.get("sells") or 0),
        "fdv_usd": fnum(attr.get("fdv_usd")),
        "market_cap_usd": fnum(attr.get("market_cap_usd")),
    }


def load_state():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def save_state(status):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Ver estado on-chain/mercado de CAMO")
    parser.add_argument("--quiet", action="store_true", help="mostrar salida sólo si hay alerta")
    parser.add_argument("--json", action="store_true", help="salida JSON")
    parser.add_argument("--reset", action="store_true", help="borrar la referencia anterior")
    args = parser.parse_args()

    if args.reset:
        STATE.unlink(missing_ok=True)

    try:
        current = extract(pool_payload())
    except Exception as exc:
        print(f"CAMO ERROR: {exc}", file=sys.stderr)
        return 2

    previous = load_state()
    price_since = pct_change(current["price_usd"], previous.get("price_usd") if previous else None)
    liq_since = pct_change(current["liquidity_usd"], previous.get("liquidity_usd") if previous else None)
    vol_since = pct_change(current["volume_h24_usd"], previous.get("volume_h24_usd") if previous else None)

    reasons = []
    if price_since is not None and abs(price_since) >= 5:
        reasons.append(f"precio {price_since:+.2f}% desde la comprobación anterior")
    if current["change_h24"] is not None and abs(current["change_h24"]) >= 10:
        reasons.append(f"precio {current['change_h24']:+.2f}% en 24 h")
    if liq_since is not None and abs(liq_since) >= 25:
        reasons.append(f"liquidez {liq_since:+.2f}%")
    if vol_since is not None and abs(vol_since) >= 200:
        reasons.append(f"volumen 24 h {vol_since:+.2f}%")

    current["change_since_previous"] = price_since
    current["liquidity_change_since_previous"] = liq_since
    current["volume_change_since_previous"] = vol_since
    current["alert"] = bool(reasons)
    current["alert_reasons"] = reasons
    save_state(current)

    if args.quiet and not reasons:
        return 0

    if args.json:
        print(json.dumps(current, indent=2, ensure_ascii=False))
        return 1 if reasons else 0

    print("\nCAMO · DesarrollAMO")
    print("=" * 44)
    print(f"Pool:       {current['pool_name']}")
    print(f"Precio:     {money(current['price_usd'])}")
    print(f"24 h:       {percent(current['change_h24'])}")
    print(f"Desde ant.: {percent(price_since)}")
    print(f"Liquidez:   {money(current['liquidity_usd'])} ({percent(liq_since)})")
    print(f"Volumen 24h:{money(current['volume_h24_usd'])} ({percent(vol_since)})")
    print(f"Tx 24 h:    {current['buys_h24']} compras / {current['sells_h24']} ventas")
    print(f"Contrato:   {TOKEN}")
    print(f"Pool:       {current['pool_address']}")
    print("Fuente:     GeckoTerminal API · BNB Chain")
    if reasons:
        print("\n⚠ ALERTA: " + "; ".join(reasons))
    elif previous:
        print("\n✓ Sin movimiento grande desde la comprobación anterior")
    else:
        print("\n✓ Primera comprobación guardada como referencia")
    print()
    return 1 if reasons else 0


if __name__ == "__main__":
    raise SystemExit(main())
