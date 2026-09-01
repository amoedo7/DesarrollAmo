#!/usr/bin/env python3
"""Panel on-chain de CoinAMO (CAMO) para Termux, sin dependencias externas."""

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
RPC_URLS = (
    "https://bsc-dataseed.binance.org/",
    "https://bsc.publicnode.com",
)
STATE = Path.home() / ".cache" / "desarrollamo" / "camo-status.json"
HEADERS = {
    "Accept": "application/json;version=20230203",
    "User-Agent": "DesarrollAMO-CAMO-Status/2.0",
}
LIQUIDITY_CRITICAL_USD = 500.0
LIQUIDITY_LOW_USD = 2000.0


def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.load(response)


def post_json(url: str, payload):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": HEADERS["User-Agent"],
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.load(response)


def pool_payload() -> dict:
    url = f"{API}/networks/{NETWORK}/pools/{POOL}"
    try:
        return get_json(url)["data"]
    except (urllib.error.HTTPError, KeyError):
        url = f"{API}/networks/{NETWORK}/tokens/{TOKEN}/pools?page=1"
        data = get_json(url).get("data", [])
        if not data:
            raise RuntimeError("GeckoTerminal no devuelve ningún pool para CAMO")
        return data[0]


def token_info_payload() -> dict:
    try:
        return get_json(f"{API}/networks/{NETWORK}/tokens/{TOKEN}/info").get("data", {})
    except Exception:
        return {}


def latest_trade(pool_address: str) -> dict | None:
    try:
        data = get_json(
            f"{API}/networks/{NETWORK}/pools/{pool_address}/trades"
        ).get("data", [])
        return data[0] if data else None
    except Exception:
        return None


def latest_ohlcv_timestamp(pool_address: str) -> str | None:
    try:
        url = (
            f"{API}/networks/{NETWORK}/pools/{pool_address}"
            "/ohlcv/day?aggregate=1&limit=1&currency=usd"
        )
        rows = (
            ((get_json(url).get("data") or {}).get("attributes") or {}).get(
                "ohlcv_list"
            )
            or []
        )
        if rows and rows[0]:
            return datetime.fromtimestamp(int(rows[0][0]), tz=timezone.utc).isoformat()
    except Exception:
        pass
    return None


def fnum(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def inum(value):
    try:
        return int(value)
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


def amount(value, symbol=""):
    if value is None:
        return "N/D"
    suffix = f" {symbol}" if symbol else ""
    if abs(value) >= 1_000_000:
        text = f"{value:,.2f}"
    elif abs(value) >= 1:
        text = f"{value:,.6f}".rstrip("0").rstrip(".")
    else:
        text = f"{value:.10f}".rstrip("0").rstrip(".")
    return text + suffix


def percent(value):
    return "N/D" if value is None else f"{value:+.2f}%"


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def age_text(value: str | None) -> str:
    dt = parse_iso(value)
    if not dt:
        return "N/D"
    delta = datetime.now(timezone.utc) - dt.astimezone(timezone.utc)
    seconds = max(0, int(delta.total_seconds()))
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes = rem // 60
    if days:
        return f"{days} d {hours} h"
    if hours:
        return f"{hours} h {minutes} min"
    return f"{minutes} min"


def relationship_address(data: dict, key: str) -> str | None:
    rel = (((data.get("relationships") or {}).get(key) or {}).get("data") or {})
    value = rel.get("id") or ""
    if "_" in value:
        value = value.split("_", 1)[1]
    if value.startswith("0x") and len(value) == 42:
        return value
    return None


def abi_uint(value: str | None) -> int | None:
    if not value or not isinstance(value, str):
        return None
    try:
        return int(value, 16)
    except ValueError:
        return None


def abi_address(value: str | None) -> str | None:
    if not value or not isinstance(value, str):
        return None
    raw = value.removeprefix("0x")
    if len(raw) < 40:
        return None
    return "0x" + raw[-40:]


def rpc_eth_calls(calls: list[tuple[str, str]]) -> list[str | None]:
    payload = [
        {
            "jsonrpc": "2.0",
            "id": i + 1,
            "method": "eth_call",
            "params": [{"to": to, "data": data}, "latest"],
        }
        for i, (to, data) in enumerate(calls)
    ]
    last_error = None
    for url in RPC_URLS:
        try:
            response = post_json(url, payload)
            if not isinstance(response, list):
                raise RuntimeError("respuesta RPC batch inválida")
            indexed = {
                item.get("id"): item for item in response if isinstance(item, dict)
            }
            return [
                (indexed.get(i + 1) or {}).get("result") for i in range(len(calls))
            ]
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"RPC BNB Chain no disponible: {last_error}")


def onchain_snapshot(pool_data: dict) -> dict:
    attr = pool_data.get("attributes") or {}
    base = relationship_address(pool_data, "base_token")
    quote = relationship_address(pool_data, "quote_token")
    pool_address = attr.get("address") or POOL
    if not base or not quote:
        raise RuntimeError("no se pudieron resolver los tokens del pool")

    camo_is_base = base.lower() == TOKEN.lower()
    counter = quote if camo_is_base else base
    calls = [
        (TOKEN, "0x18160ddd"),
        (TOKEN, "0x313ce567"),
        (counter, "0x313ce567"),
        (pool_address, "0x0dfe1681"),
        (pool_address, "0x0902f1ac"),
    ]
    raw = rpc_eth_calls(calls)
    total_raw = abi_uint(raw[0])
    camo_decimals = abi_uint(raw[1])
    counter_decimals = abi_uint(raw[2])
    token0 = abi_address(raw[3])
    reserves_hex = (raw[4] or "").removeprefix("0x")

    if camo_decimals is None:
        camo_decimals = 18
    if counter_decimals is None:
        counter_decimals = 18
    if len(reserves_hex) < 192:
        raise RuntimeError("getReserves() devolvió una respuesta incompleta")

    reserve0 = int(reserves_hex[0:64], 16)
    reserve1 = int(reserves_hex[64:128], 16)
    reserve_ts = int(reserves_hex[128:192], 16)
    camo_is_token0 = (token0 or "").lower() == TOKEN.lower()
    camo_raw = reserve0 if camo_is_token0 else reserve1
    counter_raw = reserve1 if camo_is_token0 else reserve0

    return {
        "supply": (
            total_raw / (10**camo_decimals) if total_raw is not None else None
        ),
        "reserve_camo": camo_raw / (10**camo_decimals),
        "reserve_counter": counter_raw / (10**counter_decimals),
        "counter_address": counter,
        "reserve_timestamp": datetime.fromtimestamp(
            reserve_ts, tz=timezone.utc
        ).isoformat()
        if reserve_ts
        else None,
    }


def liquidity_state(value):
    if value is None:
        return "unknown"
    if value < LIQUIDITY_CRITICAL_USD:
        return "critical"
    if value < LIQUIDITY_LOW_USD:
        return "low"
    return "ok"


def extract(
    pool_data: dict,
    token_info: dict,
    chain: dict | None,
    trade: dict | None,
    fallback_activity: str | None,
) -> dict:
    attr = pool_data.get("attributes") or {}
    rel = pool_data.get("relationships") or {}
    token_lower = TOKEN.lower()
    base_id = (((rel.get("base_token") or {}).get("data") or {}).get("id") or "").lower()
    quote_id = (((rel.get("quote_token") or {}).get("data") or {}).get("id") or "").lower()
    token_is_quote = token_lower in quote_id
    price = fnum(
        attr.get("quote_token_price_usd")
        if token_is_quote
        else attr.get("base_token_price_usd")
    )

    changes = attr.get("price_change_percentage") or {}
    volumes = attr.get("volume_usd") or {}
    txns = attr.get("transactions") or {}
    t24 = txns.get("h24") or {}
    info_attr = token_info.get("attributes") or {}

    holders_data = info_attr.get("holders")
    holders = None
    holders_updated_at = None
    if isinstance(holders_data, dict):
        holders = inum(holders_data.get("count"))
        holders_updated_at = holders_data.get("last_updated")

    trade_attr = (trade or {}).get("attributes") or {}
    last_trade_at = trade_attr.get("block_timestamp") or fallback_activity
    if trade_attr.get("block_timestamp"):
        last_trade_source = "GeckoTerminal trades"
    elif fallback_activity:
        last_trade_source = "GeckoTerminal OHLCV"
    else:
        last_trade_source = None

    pool_name = attr.get("name") or "CAMO pool"
    symbols = [x.strip() for x in pool_name.split("/")]
    if len(symbols) >= 2:
        counter_symbol = symbols[0] if token_is_quote else symbols[1]
    else:
        counter_symbol = "QUOTE"

    liquidity = fnum(attr.get("reserve_in_usd"))
    level = liquidity_state(liquidity)
    warnings = []
    if level == "critical":
        warnings.append(
            f"LIQUIDEZ CRÍTICA: {money(liquidity)} total; umbral {money(LIQUIDITY_CRITICAL_USD)}"
        )
    elif level == "low":
        warnings.append(
            f"liquidez baja: {money(liquidity)} total; umbral {money(LIQUIDITY_LOW_USD)}"
        )

    reserve_camo = (chain or {}).get("reserve_camo")
    if holders == 0 and reserve_camo not in (None, 0):
        warnings.append(
            "holders=0 es inconsistente con las reservas del pool; tratar ese dato como N/D"
        )

    supply = (chain or {}).get("supply")
    if supply is None:
        supply = fnum(info_attr.get("total_supply"))

    return {
        "schema": "camo.status.v2",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "pool_name": pool_name,
        "pool_address": attr.get("address") or POOL,
        "pool_created_at": attr.get("pool_created_at"),
        "pool_age": age_text(attr.get("pool_created_at")),
        "price_usd": price,
        "change_h24": fnum(changes.get("h24")),
        "liquidity_usd": liquidity,
        "liquidity_state": level,
        "volume_h24_usd": fnum(volumes.get("h24")),
        "buys_h24": int(t24.get("buys") or 0),
        "sells_h24": int(t24.get("sells") or 0),
        "fdv_usd": fnum(attr.get("fdv_usd")),
        "market_cap_usd": fnum(attr.get("market_cap_usd")),
        "supply": supply,
        "holders": holders,
        "holders_updated_at": holders_updated_at,
        "reserve_camo": reserve_camo,
        "reserve_quote": (chain or {}).get("reserve_counter"),
        "quote_symbol": counter_symbol,
        "quote_token_address": (chain or {}).get("counter_address"),
        "reserve_timestamp": (chain or {}).get("reserve_timestamp"),
        "last_trade_at": last_trade_at,
        "last_trade_age": age_text(last_trade_at),
        "last_trade_hash": trade_attr.get("tx_hash"),
        "last_trade_source": last_trade_source,
        "health_warnings": warnings,
        "onchain_rpc_ok": chain is not None,
    }


def load_state():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def save_state(status):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(
        json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def self_test() -> int:
    assert round(pct_change(105, 100), 8) == 5.0
    assert pct_change(1, 0) is None
    assert liquidity_state(104.88) == "critical"
    assert liquidity_state(1000) == "low"
    assert liquidity_state(3000) == "ok"
    assert abi_uint("0x03e8") == 1000
    assert (
        abi_address("0x" + "0" * 24 + "1234567890abcdef1234567890abcdef12345678")
        == "0x1234567890abcdef1234567890abcdef12345678"
    )
    assert age_text(None) == "N/D"
    print("OK: camo-status self-test")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Ver estado on-chain/mercado de CAMO")
    parser.add_argument(
        "--quiet", action="store_true", help="mostrar salida sólo si hay alerta de movimiento"
    )
    parser.add_argument("--json", action="store_true", help="salida JSON")
    parser.add_argument("--reset", action="store_true", help="borrar la referencia anterior")
    parser.add_argument(
        "--self-test", action="store_true", help="ejecutar pruebas locales sin red"
    )
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if args.reset:
        STATE.unlink(missing_ok=True)

    try:
        pool_data = pool_payload()
        token_info = token_info_payload()
        pool_address = (pool_data.get("attributes") or {}).get("address") or POOL
        trade = latest_trade(pool_address)
        fallback_activity = None if trade else latest_ohlcv_timestamp(pool_address)
        rpc_warning = None
        try:
            chain = onchain_snapshot(pool_data)
        except Exception as exc:
            chain = None
            rpc_warning = f"RPC on-chain no disponible: {exc}"
        current = extract(pool_data, token_info, chain, trade, fallback_activity)
        if rpc_warning:
            current["health_warnings"].append(rpc_warning)
    except Exception as exc:
        print(f"CAMO ERROR: {exc}", file=sys.stderr)
        return 2

    previous = load_state()
    price_since = pct_change(
        current["price_usd"], previous.get("price_usd") if previous else None
    )
    liq_since = pct_change(
        current["liquidity_usd"], previous.get("liquidity_usd") if previous else None
    )
    vol_since = pct_change(
        current["volume_h24_usd"],
        previous.get("volume_h24_usd") if previous else None,
    )

    reasons = []
    if price_since is not None and abs(price_since) >= 5:
        reasons.append(f"precio {price_since:+.2f}% desde la comprobación anterior")
    if current["change_h24"] is not None and abs(current["change_h24"]) >= 10:
        reasons.append(f"precio {current['change_h24']:+.2f}% en 24 h")
    if liq_since is not None and abs(liq_since) >= 25:
        reasons.append(f"liquidez {liq_since:+.2f}%")
    if vol_since is not None and abs(vol_since) >= 200:
        reasons.append(f"volumen 24 h {vol_since:+.2f}%")

    old_level = (
        liquidity_state(previous.get("liquidity_usd")) if previous else "unknown"
    )
    if current["liquidity_state"] == "critical" and old_level not in (
        "critical",
        "unknown",
    ):
        reasons.append("liquidez cayó a nivel crítico")

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
    print("=" * 52)
    print(f"Pool:        {current['pool_name']}")
    print(f"Precio:      {money(current['price_usd'])}")
    print(f"24 h:        {percent(current['change_h24'])}")
    print(f"Desde ant.:  {percent(price_since)}")
    print(f"Liquidez:    {money(current['liquidity_usd'])} ({percent(liq_since)})")
    print(f"Estado liq.: {current['liquidity_state'].upper()}")
    print(
        "Reservas:    "
        f"{amount(current['reserve_camo'], 'CAMO')} / "
        f"{amount(current['reserve_quote'], current['quote_symbol'])}"
    )
    print(f"Volumen 24h: {money(current['volume_h24_usd'])} ({percent(vol_since)})")
    print(
        f"Tx 24 h:     {current['buys_h24']} compras / {current['sells_h24']} ventas"
    )
    print(f"Supply:      {amount(current['supply'], 'CAMO')}")
    holders = "N/D" if current["holders"] is None else str(current["holders"])
    print(f"Holders:     {holders}")
    print(
        f"Edad pool:   {current['pool_age']} ({current['pool_created_at'] or 'N/D'})"
    )
    if current["last_trade_at"]:
        print(
            f"Última act.: {current['last_trade_age']} · {current['last_trade_at']}"
        )
    else:
        print("Última act.: N/D")
    print(f"Contrato:    {TOKEN}")
    print(f"Pool:        {current['pool_address']}")
    print("Fuentes:     GeckoTerminal API + BNB Chain RPC")

    if current["health_warnings"]:
        print("\nSALUD")
        for warning in current["health_warnings"]:
            print(f"⚠ {warning}")
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
