# Trade Recorder

Open-source multi-exchange cryptocurrency trade recorder with CSV export.

Records every single trade from 16 exchanges via WebSocket in real-time.

## Features

- **16 exchanges** — Binance, Bybit, OKX, Bitget, Gate.io, MEXC, Hyperliquid, Deribit, BitMEX, dYdX, Phemex, Bitunix, Kraken, BingX, Coinbase, HTX
- **Every trade recorded** — zero data loss, verified across all exchanges
- **CSV export** — manual or auto-export every 1 hour
- **Real-time UI** — live trade table, per-exchange connection status, buy/sell stats
- **Standalone** — no API keys needed, all public WebSocket endpoints

## Screenshot

```
┌──────────────────────────────────────────────────┐
│  TRADE RECORDER                                  │
│                                                  │
│  Symbol: [BTCUSDT]                               │
│  Exchanges: ☑ Binance ☑ Bybit ☑ OKX ☐ Bitget... │
│                                                  │
│  [Start Recording] [Stop] [Export CSV] [Clear]   │
│  ☐ Auto Export (1hr)                             │
│                                                  │
│  Trades: 12,345 | Buy: $45.2M | Sell: $43.1M    │
│  ● Binance (8,201) ● Bybit (3,012) ● OKX (1,132)│
│                                                  │
│  Time        Exchange  Price      Qty     Side   │
│  12:01:23    Binance   $66,500    0.0213  BUY    │
│  12:01:23    Bybit     $66,501    0.0500  SELL   │
│  12:01:22    OKX       $66,499    0.1000  BUY    │
│  ...                                             │
└──────────────────────────────────────────────────┘
```

## Install

```bash
pip install PyQt6 websockets orjson
```

## Usage

```bash
python main.py
```

Or as module:
```bash
python -m trade_recorder_qt.main
```

## CSV Format

| Column | Description |
|--------|-------------|
| timestamp_ms | Unix timestamp in milliseconds |
| datetime | Human readable (YYYY-MM-DD HH:MM:SS) |
| exchange | Exchange name (Binance, Bybit, etc.) |
| symbol | Trading pair (BTCUSDT, BTC-USDT-SWAP, etc.) |
| price | Trade price |
| qty | Trade quantity |
| side | buy or sell (taker direction) |
| usd_value | price × qty |

## Supported Exchanges

| Exchange | WebSocket | Symbol Format |
|----------|-----------|---------------|
| Binance | `fstream.binance.com` | BTCUSDT |
| Bybit | `stream.bybit.com` | BTCUSDT |
| OKX | `ws.okx.com` | BTC-USDT-SWAP |
| Bitget | `ws.bitget.com` | BTCUSDT |
| Gate.io | `fx-ws.gateio.ws` | BTC_USDT |
| MEXC | `contract.mexc.com` | BTC_USDT |
| Hyperliquid | `api.hyperliquid.xyz` | BTC |
| Deribit | `deribit.com` | BTC-PERPETUAL |
| BitMEX | `bitmex.com` | XBTUSD |
| dYdX | `indexer.dydx.trade` | BTC-USD |
| Phemex | `ws.phemex.com` | BTCUSDT |
| Bitunix | `fapi.bitunix.com` | BTCUSDT |
| Kraken | `futures.kraken.com` | PI_XBTUSD |
| BingX | `open-api-swap.bingx.com` | BTC-USDT |
| Coinbase | `ws-feed.exchange.coinbase.com` | BTC-USD |
| HTX | `api.hbdm.com` | BTC-USDT |

## License

MIT
