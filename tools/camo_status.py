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
CACHE_DIR = Path.home() / ".cache" / "desarrollamo"
STATE = CACHE_DIR / "camo-status.json"
LIVE_CACHE = CACHE_DIR / "camo-live.json"
META_CACHE = CACHE_DIR / "camo-token-meta.json"
LIVE_CACHE_TTL = 120
META_CACHE_TTL = 21600
HEADERS = {
    "Accept": "application/json;version=20230203",
    "User-Agent": "DesarrollAMO-CAMO-Status/2.1",
}
LIQUIDITY_CRITICAL_USD = 500.0
LIQUIDITY_LOW_USD = 2000.0


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.load(response)


def post_json(url: str, payload):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": HEADERS["User-Agent"]},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.load(response)


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def cache_age_seconds(path: Path):
    try:
        return max(0.0, datetime.now().timestamp() - path.stat().st_mtime)
    except OSError:
        return None


def cache_is_fresh(path: Path, ttl: int) -> bool:
    age = cache_age_seconds(path)
    return age is not None and age <= ttl


def pool_payload() -> dict:
    url = f"{API}/networks/{NETWORK}/pools/{POOL}"
    try:
        return get_json(url)["data"]
    except urllib.error.HTTPError as exc:
        # Un 429 NO debe provocar otra consulta: eso empeora el rate limit.
        if exc.code != 404:
            raise
        url = f"{API}/networks/{NETWORK}/tokens/{TOKEN}/pools?page=1"
        data = get_json(url).get("data", [])
        if not data:
            raise RuntimeError("GeckoTerminal no devuelve ningún pool para CAMO")
        return data[0]
    except KeyError:
        raise RuntimeError("respuesta de pool inválida")


def token_info_payload(force: bool = False) -> tuple[dict, bool]:
    cached = read_json(META_CACHE)
    if cached and not force and cache_is_fresh(META_CACHE, META_CACHE_TTL):
        return cached, True
    try:
        data = get_json(f"{API}/networks/{NETWORK}/tokens/{TOKEN}/info").get("data", {})
        if data:
            write_json(META_CACHE, data)
        return data, False
    except Exception:
        # Holders y metadata cambian lento; si la API limita, conservar el último dato conocido.
        return (cached or {}), bool(cached)


def latest_trade(pool_address: str) -> dict | None:
    try:
        data = get_json(f"{API}/networks/{NETWORK}/pools/{pool_address}/trades").get("data", [])
        return data[0] if data else None
    except Exception:
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
            indexed = {item.get("id"): item for item in response if isinstance(item, dict)}
            return [(indexed.get(i + 1) or {}).get("result") for i in range(len(calls))]
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

    counter = quote if base.lower() == TOKEN.lower() else base
    raw = rpc_eth_calls([
        (TOKEN, "0x18160ddd"),
        (TOKEN, "0x313ce567"),
        (counter, "0x313ce567"),
        (pool_address, "0x0dfe1681"),
        (pool_address, "0x0902f1ac"),
    ])
    total_raw = abi_uint(raw[0])
    camo_decimals = abi_uint(raw[1]) or 18
    counter_decimals = abi_uint(raw[2]) or 18
    token0 = abi_address(raw[3])
    reserves_hex = (raw[4] or "").removeprefix("0x")
    if len(reserves_hex) < 192:
        raise RuntimeError("getReserves() devolvió una respuesta incompleta")

    reserve0 = int(reserves_hex[0:64], 16)
    reserve1 = int(reserves_hex[64:128], 16)
    reserve_ts = int(reserves_hex[128:192], 16)
    camo_is_token0 = (token0 or "").lower() == TOKEN.lower()
    camo_raw = reserve0 if camo_is_token0 else reserve1
    counter_raw = reserve1 if camo_is_token0 else reserve0

    return {
        "supply": total_raw / (10**camo_decimals) if total_raw is not None else None,
        "reserve_camo": camo_raw / (10**camo_decimals),
        "reserve_counter": counter_raw / (10**counter_decimals),
        "counter_address": counter,
        "reserve_timestamp": datetime.fromtimestamp(reserve_ts, tz=timezone.utc).isoformat() if reserve_ts else None,
    }


def liquidity_state(value):
    if value is None:
        return "unknown"
    if value < LIQUIDITY_CRITICAL_USD:
        return "critical"
    if value < LIQUIDITY_LOW_USD:
        return "low"
    return "ok"


def extract(pool_data: dict, token_info: dict, chain: dict | None, trade: dict | None, previous: dict | None) -> dict:
    attr = pool_data.get("attributes") or {}
    rel = pool_data.get("relationships") or {}
    token_lower = TOKEN.lower()
    quote_id = (((rel.get("quote_token") or {}).get("data") or {}).get("id") or "").lower()
    token_is_quote = token_lower in quote_id
    price = fnum(attr.get("quote_token_price_usd") if token_is_quote else attr.get("base_token_price_usd"))

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
    if trade_attr.get("block_timestamp"):
        last_trade_at = trade_attr.get("block_timestamp")
        last_trade_hash = trade_attr.get("tx_hash")
        last_trade_source = "GeckoTerminal trades"
    else:
        last_trade_at = (previous or {}).get("last_trade_at")
        last_trade_hash = (previous or {}).get("last_trade_hash")
        last_trade_source = (previous or {}).get("last_trade_source")

    pool_name = attr.get("name") or "CAMO pool"
    symbols = [x.strip() for x in pool_name.split("/")]
    counter_symbol = (symbols[0] if token_is_quote else symbols[1]) if len(symbols) >= 2 else "QUOTE"

    liquidity = fnum(attr.get("reserve_in_usd"))
    level = liquidity_state(liquidity)
    warnings = []
    if level == "critical":
        warnings.append(f"LIQUIDEZ CRÍTICA: {money(liquidity)} total; umbral {money(LIQUIDITY_CRITICAL_USD)}")
    elif level == "low":
        warnings.append(f"liquidez baja: {money(liquidity)} total; umbral {money(LIQUIDITY_LOW_USD)}")

    reserve_camo = (chain or {}).get("reserve_camo")
    if holders == 0 and reserve_camo not in (None, 0):
        warnings.append("holders=0 es inconsistente con las reservas del pool; tratar ese dato como N/D")

    supply = (chain or {}).get("supply")
    if supply is None:
        supply = fnum(info_attr.get("total_supply"))

    reserve_timestamp = (chain or {}).get("reserve_timestamp")
    return {
        "schema": "camo.status.v2.1",
        "checked_at": now_iso(),
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
        "reserve_timestamp": reserve_timestamp,
        "reserve_age": age_text(reserve_timestamp),
        "last_trade_at": last_trade_at,
        "last_trade_age": age_text(last_trade_at),
        "last_trade_hash": last_trade_hash,
        "last_trade_source": last_trade_source,
        "health_warnings": warnings,
        "onchain_rpc_ok": chain is not None,
        "cache_used": False,
        "cache_age_seconds": 0.0,
        "rate_limit_fallback": False,
    }


def refresh_ages(status: dict):
    status["pool_age"] = age_text(status.get("pool_created_at"))
    status["reserve_age"] = age_text(status.get("reserve_timestamp"))
    status["last_trade_age"] = age_text(status.get("last_trade_at"))
    return status


def cached_status(stale: bool = False, reason: str | None = None):
    cached = read_json(LIVE_CACHE)
    if not cached:
        return None
    cached = refresh_ages(dict(cached))
    cached["cache_used"] = True
    cached["cache_age_seconds"] = round(cache_age_seconds(LIVE_CACHE) or 0.0, 1)
    cached["rate_limit_fallback"] = stale
    if reason:
        warnings = list(cached.get("health_warnings") or [])
        msg = f"API limitada/no disponible; usando caché de {cached['cache_age_seconds']:.0f}s ({reason})"
        if msg not in warnings:
            warnings.append(msg)
        cached["health_warnings"] = warnings
    return cached


def fetch_live(previous: dict | None, force_meta: bool = False) -> dict:
    pool_data = pool_payload()
    token_info, meta_cached = token_info_payload(force=force_meta)
    pool_address = (pool_data.get("attributes") or {}).get("address") or POOL

    rpc_warning = None
    try:
        chain = onchain_snapshot(pool_data)
    except Exception as exc:
        chain = None
        rpc_warning = f"RPC on-chain no disponible: {exc}"

    # Sólo pedir /trades si Gecko ya informa operaciones recientes.
    # Con 0 tx/24h evitamos una consulta inútil en cada ejecución.
    t24 = (((pool_data.get("attributes") or {}).get("transactions") or {}).get("h24") or {})
    tx_count = int(t24.get("buys") or 0) + int(t24.get("sells") or 0)
    trade = latest_trade(pool_address) if tx_count else None

    current = extract(pool_data, token_info, chain, trade, previous)
    current["metadata_cache_used"] = meta_cached
    if rpc_warning:
        current["health_warnings"].append(rpc_warning)
    write_json(LIVE_CACHE, current)
    return current


def get_current(previous: dict | None, fresh: bool = False) -> dict:
    if not fresh and cache_is_fresh(LIVE_CACHE, LIVE_CACHE_TTL):
        cached = cached_status()
        if cached:
            return cached
    try:
        return fetch_live(previous)
    except urllib.error.HTTPError as exc:
        cached = cached_status(stale=True, reason=f"HTTP {exc.code}")
        if cached:
            return cached
        raise
    except Exception as exc:
        cached = cached_status(stale=True, reason=type(exc).__name__)
        if cached:
            return cached
        raise


def load_state():
    return read_json(STATE)


def save_state(status):
    write_json(STATE, status)


def self_test() -> int:
    assert round(pct_change(105, 100), 8) == 5.0
    assert pct_change(1, 0) is None
    assert liquidity_state(104.88) == "critical"
    assert liquidity_state(1000) == "low"
    assert liquidity_state(3000) == "ok"
    assert abi_uint("0x03e8") == 1000
    assert abi_address("0x" + "0" * 24 + "1234567890abcdef1234567890abcdef12345678") == "0x1234567890abcdef1234567890abcdef12345678"
    assert age_text(None) == "N/D"
    assert LIVE_CACHE_TTL >= 60
    assert META_CACHE_TTL > LIVE_CACHE_TTL
    print("OK: camo-status self-test")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Ver estado on-chain/mercado de CAMO")
    parser.add_argument("--quiet", action="store_true", help="mostrar salida sólo si hay alerta de movimiento")
    parser.add_argument("--json", action="store_true", help="salida JSON")
    parser.add_argument("--reset", action="store_true", help="borrar referencias y caché")
    parser.add_argument("--fresh", action="store_true", help="forzar una lectura nueva ignorando caché de 120 s")
    parser.add_argument("--self-test", action="store_true", help="ejecutar pruebas locales sin red")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if args.reset:
        for path in (STATE, LIVE_CACHE, META_CACHE):
            path.unlink(missing_ok=True)

    previous = load_state()
    try:
        current = get_current(previous, fresh=args.fresh)
    except Exception as exc:
        print(f"CAMO ERROR: {exc}", file=sys.stderr)
        return 2

    price_since = pct_change(current.get("price_usd"), previous.get("price_usd") if previous else None)
    liq_since = pct_change(current.get("liquidity_usd"), previous.get("liquidity_usd") if previous else None)
    vol_since = pct_change(current.get("volume_h24_usd"), previous.get("volume_h24_usd") if previous else None)

    reasons = []
    if price_since is not None and abs(price_since) >= 5:
        reasons.append(f"precio {price_since:+.2f}% desde la comprobación anterior")
    if current.get("change_h24") is not None and abs(current["change_h24"]) >= 10:
        reasons.append(f"precio {current['change_h24']:+.2f}% en 24 h")
    if liq_since is not None and abs(liq_since) >= 25:
        reasons.append(f"liquidez {liq_since:+.2f}%")
    if vol_since is not None and abs(vol_since) >= 200:
        reasons.append(f"volumen 24 h {vol_since:+.2f}%")

    old_level = liquidity_state(previous.get("liquidity_usd")) if previous else "unknown"
    if current.get("liquidity_state") == "critical" and old_level not in ("critical", "unknown"):
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
    print(f"Reservas:    {amount(current['reserve_camo'], 'CAMO')} / {amount(current['reserve_quote'], current['quote_symbol'])}")
    print(f"Volumen 24h: {money(current['volume_h24_usd'])} ({percent(vol_since)})")
    print(f"Tx 24 h:     {current['buys_h24']} compras / {current['sells_h24']} ventas")
    print(f"Supply:      {amount(current['supply'], 'CAMO')}")
    holders = "N/D" if current.get("holders") is None else str(current["holders"])
    print(f"Holders:     {holders}")
    print(f"Edad pool:   {current['pool_age']} ({current.get('pool_created_at') or 'N/D'})")
    print(f"Reservas act:{current.get('reserve_age') or 'N/D'} · {current.get('reserve_timestamp') or 'N/D'}")
    if current.get("last_trade_at"):
        print(f"Último trade:{current['last_trade_age']} · {current['last_trade_at']}")
    else:
        print("Último trade:N/D")
    print(f"Contrato:    {TOKEN}")
    print(f"Pool:        {current['pool_address']}")
    source = "GeckoTerminal + BNB Chain RPC"
    if current.get("cache_used"):
        source += f" · caché {current.get('cache_age_seconds', 0):.0f}s"
    print(f"Fuentes:     {source}")

    if current.get("health_warnings"):
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
