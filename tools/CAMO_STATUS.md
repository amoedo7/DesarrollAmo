# CAMO Status en Termux

Monitor de CoinAMO (CAMO) de DesarrollAMO en BNB Chain.

- Token: `0x14ade63350ce5C6723Fd180Ec22A99699bA42894`
- Pool histórico CAMO/USDT: `0xfA4B3835E58d73B06Cc99c0Ed2B1223b74625faD`
- Fuente de mercado: GeckoTerminal Public API
- Sin API key y sin dependencias Python externas.

## Instalar desde fish

```fish
curl -fsSL https://raw.githubusercontent.com/amoedo7/DesarrollAmo/main/tools/install_camo_status.fish | source
camo-status
```

La primera ejecución guarda una referencia en `~/.cache/desarrollamo/camo-status.json`. Las siguientes muestran el cambio desde la comprobación anterior.

## Opciones

```fish
camo-status             # estado completo
camo-status --json      # salida JSON
camo-status --quiet     # sólo imprime si detecta alerta
camo-status --reset     # reinicia la referencia local
```

Una alerta se activa con >=5% de cambio de precio desde la lectura anterior, >=10% en 24 h, >=25% de cambio de liquidez o >=200% de cambio del volumen de 24 h.
