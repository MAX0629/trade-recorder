# Trade Recorder

[中文](#中文說明) | [English](#english)

---

## 中文說明

開源多交易所加密貨幣成交記錄器。透過 WebSocket 即時記錄每一筆成交，匯出 CSV。

### 功能

- **16 間交易所** — Binance、Bybit、OKX、Bitget、Gate.io、MEXC、Hyperliquid、Deribit、BitMEX、dYdX、Phemex、Bitunix、Kraken、BingX、Coinbase、HTX
- **多幣種同時記錄** — 輸入 `BTCUSDT,ETHUSDT,SOLUSDT` 即可同時監控多個幣種
- **每筆零遺失** — 經過 16 間交易所、6,967 筆交易精確度驗證
- **Trade ID** — 記錄交易所原生交易 ID，可用於反查驗證
- **CSV 匯出** — 手動匯出或自動每 1 小時匯出
- **免費公開 API** — 不需要任何 API Key

### 安裝

**方法 1: 直接下載 EXE（推薦）**

前往 [Releases](https://github.com/MAX0629/trade-recorder/releases) 下載 `TradeRecorder.exe`，雙擊即可執行，不需要安裝 Python。

**方法 2: 從原始碼執行**

```bash
git clone https://github.com/MAX0629/trade-recorder.git
cd trade-recorder
pip install -r requirements.txt
python main.py
```

### 使用方式

1. **輸入幣種** — 在 Symbols 欄位輸入一個或多個幣種，用逗號分隔
   - 單幣種: `BTCUSDT`
   - 多幣種: `BTCUSDT,ETHUSDT,SOLUSDT`
   - 支援任何 USDT 合約: `DOGEUSDT,XRPUSDT,PEPEUSDT`

2. **勾選交易所** — 選擇要記錄的交易所（可多選）

3. **按 Start Recording** — 開始即時記錄

4. **匯出 CSV**
   - 手動: 按 `Export CSV` 選擇儲存位置
   - 自動: 勾選 `Auto Export (1hr)` 每小時自動儲存到 `data/` 資料夾

### 介面說明

```
┌──────────────────────────────────────────────────────┐
│  TRADE RECORDER                                      │
│                                                      │
│  Symbols: [BTCUSDT,ETHUSDT,SOLUSDT]                  │
│  Exchanges: ☑ Binance ☑ Bybit ☑ OKX ☐ Bitget ...    │
│                                                      │
│  [Start Recording] [Stop] [Export CSV] [Clear]       │
│  ☑ Auto Export (1hr)                                 │
│                                                      │
│  Trades: 45,678 | Buy: $125.2M | Sell: $118.7M      │
│  ● Binance (28,201) ● Bybit (12,345) ● OKX (5,132) │
│                                                      │
│  Time      Exchange  Symbol    Trade ID     Price    │
│  12:01:23  Binance   BTCUSDT   891234567   $66,500  │
│  12:01:23  Bybit     ETHUSDT   6665d04d..  $1,988   │
│  12:01:22  OKX       SOLUSDT   12345678    $81.52   │
│  ...                                                 │
└──────────────────────────────────────────────────────┘
```

### CSV 欄位

| 欄位 | 說明 | 範例 |
|------|------|------|
| timestamp_ms | Unix 時間戳（毫秒） | 1774955316870 |
| datetime | 可讀時間 | 2026-04-01 12:01:23 |
| exchange | 交易所名稱 | Binance |
| symbol | 交易對 | BTCUSDT |
| trade_id | 交易所原生交易 ID | 891234567 |
| price | 成交價格 | 66500.0 |
| qty | 成交數量 | 0.0213 |
| side | 買/賣方向（Taker 方向） | buy / sell |
| usd_value | 美元價值 (price × qty) | 1416.45 |

### Trade ID 對照表

| 交易所 | ID 欄位 | 格式 |
|--------|---------|------|
| Binance | aggTradeId | `891234567` |
| Bybit | execId | `6665d04d-e4cc-5270-...` |
| OKX | tradeId | `12345678` |
| Bitget | tradeId | `12345678` |
| Gate.io | id | `12345` |
| MEXC | timestamp | `1774955316` |
| Hyperliquid | tid/hash | `0xabc...` |
| Deribit | trade_id | `ETH-123456` |
| BitMEX | trdMatchID | `abc-def-123-...` |
| dYdX | id | `12345` |
| Phemex | timestamp | `1774955316870` |
| Bitunix | id | `12345` |
| Kraken | uid | `abc123` |
| BingX | timestamp | `1774955316870` |
| Coinbase | trade_id | `987654` |
| HTX | id | `12345678` |

### 效能參考

| 幣種 × 交易所 | WS 連線數 | RAM | CPU |
|---------------|-----------|-----|-----|
| 3 × 3 | 9 | ~50MB | ~1% |
| 10 × 3 | 30 | ~100MB | ~2% |
| 50 × 3 | 150 | ~300MB | ~5% |
| 100 × 1 | 100 | ~200MB | ~3% |

### 支援交易所

| 交易所 | WebSocket | 幣種格式 | 特殊處理 |
|--------|-----------|----------|---------|
| Binance | `fstream.binance.com` | BTCUSDT | — |
| Bybit | `stream.bybit.com` | BTCUSDT | — |
| OKX | `ws.okx.com` | BTC-USDT-SWAP | 自動轉換 |
| Bitget | `ws.bitget.com` | BTCUSDT | Ping 15s |
| Gate.io | `fx-ws.gateio.ws` | BTC_USDT | 自動轉換 |
| MEXC | `contract.mexc.com` | BTC_USDT | Ping 15s |
| Hyperliquid | `api.hyperliquid.xyz` | BTC | Text frame |
| Deribit | `deribit.com` | BTC-PERPETUAL | 自動轉換 |
| BitMEX | `bitmex.com` | XBTUSD | XBT→BTC |
| dYdX | `indexer.dydx.trade` | BTC-USD | 自動轉換 |
| Phemex | `ws.phemex.com` | BTCUSDT | Ping 5s |
| Bitunix | `fapi.bitunix.com` | BTCUSDT | Ping 20s |
| Kraken | `futures.kraken.com` | PI_XBTUSD | 自動轉換 |
| BingX | `open-api-swap.bingx.com` | BTC-USDT | 自動轉換 |
| Coinbase | `ws-feed.exchange.coinbase.com` | BTC-USD | Side 反轉 |
| HTX | `api.hbdm.com` | BTC-USDT | Gzip 壓縮 |

> 你只需要輸入 `BTCUSDT` 格式，程式會自動轉換成各交易所的格式。

### 常見問題

**Q: 為什麼某些交易所顯示 ○ 灰色（未連線）？**
A: 部分交易所可能需要 VPN，或該幣種在該交易所不存在。

**Q: 可以記錄現貨（Spot）嗎？**
A: 目前只支援永續合約（Perpetual Futures）。幣種格式以 USDT 結尾。

**Q: CSV 檔案會很大嗎？**
A: BTC 單幣單所約 4MB/小時。3 幣 × 3 所約 20MB/小時。

**Q: 資料會遺失嗎？**
A: 經過 16 間交易所精確度測試，6,967 筆交易零遺失。WebSocket 斷線會自動重連。

---

## English

Open-source multi-exchange cryptocurrency trade recorder with CSV export.

Records every single trade from 16 exchanges via WebSocket in real-time.

### Features

- **16 exchanges** — Binance, Bybit, OKX, Bitget, Gate.io, MEXC, Hyperliquid, Deribit, BitMEX, dYdX, Phemex, Bitunix, Kraken, BingX, Coinbase, HTX
- **Multi-symbol** — record multiple coins simultaneously (e.g. `BTCUSDT,ETHUSDT,SOLUSDT`)
- **Zero data loss** — verified across 16 exchanges, 6,967 trades with 100% accuracy
- **Trade ID** — each trade includes the exchange's native trade ID for verification
- **CSV export** — manual export or auto-export every 1 hour
- **No API keys** — all public WebSocket endpoints, completely free

### Install

**Option 1: Download EXE (recommended)**

Go to [Releases](https://github.com/MAX0629/trade-recorder/releases) and download `TradeRecorder.exe`. Double-click to run — no Python needed.

**Option 2: Run from source**

```bash
git clone https://github.com/MAX0629/trade-recorder.git
cd trade-recorder
pip install -r requirements.txt
python main.py
```

### How to Use

1. **Enter symbols** — type one or more symbols separated by commas
   - Single: `BTCUSDT`
   - Multiple: `BTCUSDT,ETHUSDT,SOLUSDT`

2. **Select exchanges** — check the exchanges you want to record from

3. **Click Start Recording** — trades appear in real-time

4. **Export CSV**
   - Manual: click `Export CSV` and choose save location
   - Auto: check `Auto Export (1hr)` to save to `data/` folder every hour

### CSV Columns

| Column | Description | Example |
|--------|-------------|---------|
| timestamp_ms | Unix timestamp (milliseconds) | 1774955316870 |
| datetime | Human readable time | 2026-04-01 12:01:23 |
| exchange | Exchange name | Binance |
| symbol | Trading pair | BTCUSDT |
| trade_id | Exchange native trade ID | 891234567 |
| price | Trade price | 66500.0 |
| qty | Trade quantity | 0.0213 |
| side | Taker direction | buy / sell |
| usd_value | USD value (price × qty) | 1416.45 |

### Trade ID Reference

| Exchange | Field | Format |
|----------|-------|--------|
| Binance | aggTradeId | `891234567` |
| Bybit | execId | `6665d04d-e4cc-...` |
| OKX | tradeId | `12345678` |
| Bitget | tradeId | `12345678` |
| Gate.io | id | `12345` |
| Deribit | trade_id | `ETH-123456` |
| BitMEX | trdMatchID | `abc-def-...` |
| Coinbase | trade_id | `987654` |
| HTX | id | `12345678` |

### Performance

| Symbols × Exchanges | WS Connections | RAM | CPU |
|---------------------|---------------|-----|-----|
| 3 × 3 | 9 | ~50MB | ~1% |
| 10 × 3 | 30 | ~100MB | ~2% |
| 50 × 3 | 150 | ~300MB | ~5% |
| 100 × 1 | 100 | ~200MB | ~3% |

### Supported Exchanges

| Exchange | WebSocket | Symbol Format | Notes |
|----------|-----------|---------------|-------|
| Binance | `fstream.binance.com` | BTCUSDT | — |
| Bybit | `stream.bybit.com` | BTCUSDT | — |
| OKX | `ws.okx.com` | BTC-USDT-SWAP | Auto-converted |
| Bitget | `ws.bitget.com` | BTCUSDT | Ping 15s |
| Gate.io | `fx-ws.gateio.ws` | BTC_USDT | Auto-converted |
| MEXC | `contract.mexc.com` | BTC_USDT | Ping 15s |
| Hyperliquid | `api.hyperliquid.xyz` | BTC | Text frame |
| Deribit | `deribit.com` | BTC-PERPETUAL | Auto-converted |
| BitMEX | `bitmex.com` | XBTUSD | XBT→BTC alias |
| dYdX | `indexer.dydx.trade` | BTC-USD | Auto-converted |
| Phemex | `ws.phemex.com` | BTCUSDT | Ping 5s |
| Bitunix | `fapi.bitunix.com` | BTCUSDT | Ping 20s |
| Kraken | `futures.kraken.com` | PI_XBTUSD | Auto-converted |
| BingX | `open-api-swap.bingx.com` | BTC-USDT | Auto-converted |
| Coinbase | `ws-feed.exchange.coinbase.com` | BTC-USD | Side reversed |
| HTX | `api.hbdm.com` | BTC-USDT | Gzip compressed |

> Just enter `BTCUSDT` format — the program auto-converts to each exchange's format.

### FAQ

**Q: Why does an exchange show ○ gray (disconnected)?**
A: Some exchanges may require VPN, or the symbol doesn't exist on that exchange.

**Q: Can I record spot trades?**
A: Currently only perpetual futures are supported. Symbols should end with USDT.

**Q: How large are the CSV files?**
A: BTC single exchange ≈ 4MB/hour. 3 symbols × 3 exchanges ≈ 20MB/hour.

**Q: Will I lose any trades?**
A: Verified zero data loss across 16 exchanges (6,967 trades). Auto-reconnect on disconnect.

## License

MIT
