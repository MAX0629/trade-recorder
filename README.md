# Trade Recorder

[中文](#中文說明) | [English](#english)

---

## 中文說明

開源多交易所加密貨幣成交記錄器。透過 WebSocket 即時記錄每一筆成交，匯出 CSV。
**內建交易驗證功能** — 用於防詐騙，驗證他人聲稱的交易是否真實存在。

### 功能

- **16 間交易所** — Binance、Bybit、OKX、Bitget、Gate.io、MEXC、Hyperliquid、Deribit、BitMEX、dYdX、Phemex、Bitunix、Kraken、BingX、Coinbase、HTX
- **多幣種同時記錄** — 輸入 `BTCUSDT,ETHUSDT,SOLUSDT` 同時監控
- **每筆零遺失** — 經過 16 間交易所、6,967 筆交易精確度驗證
- **Trade ID** — 記錄交易所原生交易 ID，可用於反查驗證
- **交易驗證模式** — 輸入價格+數量+方向，搜尋是否有匹配的成交（防詐騙）
- **大單偵測** — >$10K 黃色高亮、>$100K 紅色高亮
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

#### 1. 記錄成交

1. 在 **Symbols** 欄位輸入幣種（逗號分隔多個）
   - 單幣種: `BTCUSDT`
   - 多幣種: `BTCUSDT,ETHUSDT,SOLUSDT`
2. **勾選交易所** — 選擇要記錄的交易所（可多選）
3. 按 **Start Recording** — 成交即時顯示在表格中
4. 按 **Stop** 停止記錄

#### 2. 匯出 CSV

- **手動匯出**: 按 `Export CSV` → 選擇儲存位置
- **自動匯出**: 勾選 `Auto Export (1hr)` → 每小時自動儲存到 `data/` 資料夾

#### 3. 交易驗證（防詐騙）

> 有人說「我在 Bybit 做空 SIREN，價格 $2.51，數量 12632」— 怎麼驗證？

1. 先開啟 Trade Recorder，勾選 Bybit，輸入 `SIRENUSDT`，按 Start Recording
2. 在 **Trade Verification** 區域填入：
   - **Price**: `2.51`
   - **Qty**: `12632`
   - **Side**: `sell`
3. 按 **Verify Trade**
4. 結果：
   - **FOUND** = 在紀錄中找到匹配的成交 → 可能是真的
   - **NO MATCH** = 找不到 → **這筆交易可能是假的**

> 注意：只能驗證記錄期間內的交易。如果他說的交易發生在你開始記錄之前，需要提前開啟記錄。

#### 4. 大單篩選

- 按 **Show Large (>$10K)** → 只顯示大於 $10,000 的成交，按金額排序
- 表格中 **>$100K 紅色粗體**、**>$10K 黃色粗體** 自動標記
- 按 **Show All** 回到即時模式

### 介面說明

```
┌──────────────────────────────────────────────────────────┐
│  TRADE RECORDER                                          │
│                                                          │
│  Symbols: [BTCUSDT,ETHUSDT,SOLUSDT]                      │
│  Exchanges: ☑ Binance ☑ Bybit ☑ OKX ☐ Bitget ...        │
│                                                          │
│  [Start Recording] [Stop] [Export CSV] [Clear]           │
│  ☑ Auto Export (1hr)                                     │
│                                                          │
│  Trades: 45,678 | Buy: $125.2M | Sell: $118.7M          │
│  ● Binance (28,201) ● Bybit (12,345) ● OKX (5,132)     │
│                                                          │
│  ┌─ Trade Verification / Search ───────────────────────┐ │
│  │ Price: [2.51] Qty: [12632] Side: [sell] MinUSD: []  │ │
│  │ Tolerance: [0.5] %                                  │ │
│  │ [Verify Trade] [Show Large (>$10K)] [Show All]      │ │
│  │                                                      │ │
│  │ FOUND 3 matching trades | Total: $31,714 |          │ │
│  │ Exchanges: Bybit | Buy: 0 Sell: 3                   │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                          │
│  Time      Exchange  Symbol   Trade ID    Price   Side   │
│  12:01:23  Binance   BTCUSDT  891234567  $66,500  BUY   │
│  12:01:23  Bybit     ETHUSDT  6665d04..  $1,988   SELL  │
│  12:01:22  OKX       SOLUSDT  12345678   $81.52   BUY   │
│  ...                                                     │
└──────────────────────────────────────────────────────────┘
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
| usd_value | 美元價值 (price x qty) | 1416.45 |

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

| 幣種 x 交易所 | WS 連線數 | RAM | CPU |
|---------------|-----------|-----|-----|
| 3 x 3 | 9 | ~50MB | ~1% |
| 10 x 3 | 30 | ~100MB | ~2% |
| 50 x 3 | 150 | ~300MB | ~5% |
| 100 x 1 | 100 | ~200MB | ~3% |

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

### 防詐騙使用場景

**場景 1: 有人展示獲利截圖**
> 「我在 Bybit 做空 SIREN $2.51，賺了 $19,000」

1. 開啟 Trade Recorder，記錄 SIRENUSDT（勾 Bybit）
2. 要求對方**即時操作一筆小額交易**給你看
3. 用 Verify Trade 搜尋是否出現匹配紀錄
4. 找不到 = 對方在造假

**場景 2: 驗證大額成交**
> 有人聲稱進行了一筆 $50,000 的交易

1. 提前記錄該幣種
2. 按 Show Large (>$10K) 篩選大單
3. 比對時間、價格、數量、交易所是否吻合

**場景 3: 長期監控**
1. 勾選 Auto Export (1hr) 持續記錄
2. 所有成交存入 CSV，事後可用 Excel 篩選分析
3. Trade ID 可在交易所網站/API 反查確認

### 限制

- 只能驗證**記錄期間內**的交易，無法回溯歷史
- 只支援**永續合約**（Perpetual Futures），不支援現貨
- 部分交易所可能需要 VPN
- Trade ID 格式因交易所而異，某些所只有 timestamp 作為 ID

### 常見問題

**Q: 為什麼某些交易所顯示灰色（未連線）？**
A: 該幣種在該交易所可能不存在，或需要 VPN。

**Q: 可以驗證過去的交易嗎？**
A: 不行。必須在交易發生時已經在記錄。建議提前開啟。

**Q: CSV 檔案會很大嗎？**
A: BTC 單幣單所約 4MB/小時。3 幣 x 3 所約 20MB/小時。

**Q: 資料會遺失嗎？**
A: 經過 16 間交易所精確度測試，6,967 筆交易零遺失。斷線自動重連。

**Q: 如何更可靠地驗證他人的交易？**
A: 最可靠的方法是要求對方提供交易所的 **Read-Only API Key** 或**官方分享連結**。Trade Recorder 是輔助驗證工具。

---

## English

Open-source multi-exchange cryptocurrency trade recorder with CSV export.
**Built-in trade verification** for anti-fraud — verify if claimed trades actually exist.

### Features

- **16 exchanges** — Binance, Bybit, OKX, Bitget, Gate.io, MEXC, Hyperliquid, Deribit, BitMEX, dYdX, Phemex, Bitunix, Kraken, BingX, Coinbase, HTX
- **Multi-symbol** — record multiple coins simultaneously (e.g. `BTCUSDT,ETHUSDT,SOLUSDT`)
- **Zero data loss** — verified across 16 exchanges, 6,967 trades with 100% accuracy
- **Trade ID** — each trade includes the exchange's native trade ID for verification
- **Trade Verification** — input price + qty + side to search for matching trades (anti-fraud)
- **Large Trade Detection** — >$10K yellow highlight, >$100K red highlight
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

#### 1. Record Trades

1. Enter symbols (comma-separated): `BTCUSDT,ETHUSDT,SOLUSDT`
2. Check the exchanges you want to monitor
3. Click **Start Recording**
4. Click **Stop** to stop

#### 2. Export CSV

- **Manual**: click `Export CSV` → choose file location
- **Auto**: check `Auto Export (1hr)` → saves to `data/` every hour

#### 3. Verify a Trade (Anti-Fraud)

> Someone claims "I shorted SIREN at $2.51, qty 12632 on Bybit" — how to verify?

1. Start recording `SIRENUSDT` on Bybit
2. In **Trade Verification** section, enter:
   - **Price**: `2.51`
   - **Qty**: `12632`
   - **Side**: `sell`
3. Click **Verify Trade**
4. Result:
   - **FOUND** = matching trades exist in the records
   - **NO MATCH** = **trade may be FAKE**

> Note: can only verify trades during the recording period.

#### 4. Large Trade Filter

- Click **Show Large (>$10K)** → shows only trades above $10,000
- Table highlights: **>$100K red bold**, **>$10K yellow bold**
- Click **Show All** to return to real-time view

### Anti-Fraud Use Cases

**Case 1: Someone shows a PnL screenshot**
> "I shorted SIREN at $2.51 on Bybit and made $19,000"

1. Open Trade Recorder, record SIRENUSDT (check Bybit)
2. Ask them to **make a small trade right now** while you watch
3. Use Verify Trade to check if the trade appears
4. No match = they're faking

**Case 2: Verify a large trade**
> Someone claims a $50,000 trade

1. Record the symbol in advance
2. Click Show Large (>$10K)
3. Check if time, price, quantity, and exchange match

**Case 3: Long-term monitoring**
1. Enable Auto Export (1hr)
2. All trades saved to CSV for later analysis in Excel
3. Trade IDs can be cross-referenced on exchange websites/APIs

### CSV Columns

| Column | Description | Example |
|--------|-------------|---------|
| timestamp_ms | Unix timestamp (ms) | 1774955316870 |
| datetime | Human readable | 2026-04-01 12:01:23 |
| exchange | Exchange name | Binance |
| symbol | Trading pair | BTCUSDT |
| trade_id | Exchange native ID | 891234567 |
| price | Trade price | 66500.0 |
| qty | Trade quantity | 0.0213 |
| side | Taker direction | buy / sell |
| usd_value | USD value | 1416.45 |

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

| Symbols x Exchanges | Connections | RAM | CPU |
|---------------------|------------|-----|-----|
| 3 x 3 | 9 | ~50MB | ~1% |
| 10 x 3 | 30 | ~100MB | ~2% |
| 50 x 3 | 150 | ~300MB | ~5% |
| 100 x 1 | 100 | ~200MB | ~3% |

### Supported Exchanges

| Exchange | WebSocket | Symbol | Notes |
|----------|-----------|--------|-------|
| Binance | `fstream.binance.com` | BTCUSDT | — |
| Bybit | `stream.bybit.com` | BTCUSDT | — |
| OKX | `ws.okx.com` | BTC-USDT-SWAP | Auto-converted |
| Bitget | `ws.bitget.com` | BTCUSDT | Ping 15s |
| Gate.io | `fx-ws.gateio.ws` | BTC_USDT | Auto-converted |
| MEXC | `contract.mexc.com` | BTC_USDT | Ping 15s |
| Hyperliquid | `api.hyperliquid.xyz` | BTC | Text frame |
| Deribit | `deribit.com` | BTC-PERPETUAL | Auto-converted |
| BitMEX | `bitmex.com` | XBTUSD | XBT→BTC |
| dYdX | `indexer.dydx.trade` | BTC-USD | Auto-converted |
| Phemex | `ws.phemex.com` | BTCUSDT | Ping 5s |
| Bitunix | `fapi.bitunix.com` | BTCUSDT | Ping 20s |
| Kraken | `futures.kraken.com` | PI_XBTUSD | Auto-converted |
| BingX | `open-api-swap.bingx.com` | BTC-USDT | Auto-converted |
| Coinbase | `ws-feed.exchange.coinbase.com` | BTC-USD | Side reversed |
| HTX | `api.hbdm.com` | BTC-USDT | Gzip compressed |

> Just enter `BTCUSDT` format — auto-converts to each exchange's format.

### Limitations

- Can only verify trades **during the recording period** — no historical lookback
- Only supports **perpetual futures**, not spot
- Some exchanges may require VPN
- Trade ID format varies by exchange; some use timestamps as fallback

### FAQ

**Q: Exchange shows gray (disconnected)?**
A: Symbol may not exist on that exchange, or VPN needed.

**Q: Can I verify past trades?**
A: No. Must be recording when the trade happens. Start recording in advance.

**Q: How large are CSV files?**
A: BTC single exchange ≈ 4MB/hour. 3 symbols x 3 exchanges ≈ 20MB/hour.

**Q: Any data loss?**
A: Zero loss verified across 16 exchanges (6,967 trades). Auto-reconnect on disconnect.

**Q: Most reliable way to verify someone's trades?**
A: Ask for their exchange **Read-Only API Key** or **official share link**. Trade Recorder is a supplementary verification tool.

## License

MIT
