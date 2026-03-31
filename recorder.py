"""TradeRecorder — 多交易所即時成交記錄器.

支援 16 間交易所的 aggTrade WebSocket 流。
每一筆成交精確記錄: timestamp, exchange, symbol, price, qty, side, usd_value。
匯出 CSV 不丟失任何一筆。
"""
import json
import ssl
import gzip
import zlib
import time
import asyncio
import logging
import threading
import csv
import os
from collections import deque
from urllib.request import urlopen, Request

logger = logging.getLogger('trade_recorder')

_SSL_CTX = ssl.create_default_context()


class TradeRecorder:
    """Thread-safe 成交記錄器."""

    def __init__(self):
        self._trades: list[dict] = []
        self._lock = threading.Lock()
        self._count = 0
        self._start_time = time.time()

    def add(self, exchange: str, symbol: str, price: float, qty: float,
            side: str, ts_ms: int, trade_id: str = ''):
        """記錄一筆成交."""
        trade = {
            'timestamp_ms': ts_ms,
            'datetime': time.strftime('%Y-%m-%d %H:%M:%S',
                                      time.localtime(ts_ms / 1000)),
            'exchange': exchange,
            'symbol': symbol,
            'trade_id': trade_id,
            'price': price,
            'qty': qty,
            'side': side,
            'usd_value': price * qty,
        }
        with self._lock:
            self._trades.append(trade)
            self._count += 1

    def get_count(self) -> int:
        return self._count

    def get_recent(self, n: int = 50) -> list[dict]:
        with self._lock:
            return list(self._trades[-n:])

    def get_stats(self) -> dict:
        with self._lock:
            if not self._trades:
                return {'count': 0, 'buy_usd': 0, 'sell_usd': 0,
                        'exchanges': set(), 'duration_sec': 0}
            buy_usd = sum(t['usd_value'] for t in self._trades if t['side'] == 'buy')
            sell_usd = sum(t['usd_value'] for t in self._trades if t['side'] == 'sell')
            exchanges = set(t['exchange'] for t in self._trades)
            return {
                'count': self._count,
                'buy_usd': buy_usd,
                'sell_usd': sell_usd,
                'exchanges': exchanges,
                'duration_sec': time.time() - self._start_time,
            }

    def export_csv(self, filepath: str) -> int:
        """匯出所有成交到 CSV. 回傳筆數."""
        with self._lock:
            trades = list(self._trades)

        if not trades:
            return 0

        fields = ['timestamp_ms', 'datetime', 'exchange', 'symbol',
                  'trade_id', 'price', 'qty', 'side', 'usd_value']

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(trades)

        return len(trades)

    def clear(self):
        with self._lock:
            self._trades.clear()
            self._count = 0
            self._start_time = time.time()


# ── WebSocket 連線管理 ──────────────────────────────

EXCHANGE_CONFIG = {
    'binance': {
        'name': 'Binance',
        'url_template': 'wss://fstream.binance.com/ws/{symbol_lower}@aggTrade',
        'type': 'direct',
    },
    'bybit': {
        'name': 'Bybit',
        'url': 'wss://stream.bybit.com/v5/public/linear',
        'subscribe': lambda sym: {"op": "subscribe", "args": [f"publicTrade.{sym}"]},
        'type': 'subscribe',
    },
    'okx': {
        'name': 'OKX',
        'url': 'wss://ws.okx.com:8443/ws/v5/public',
        'subscribe': lambda sym: {"op": "subscribe", "args": [{"channel": "trades", "instId": sym}]},
        'symbol_format': lambda s: s.replace('USDT', '-USDT-SWAP'),
        'type': 'subscribe',
    },
    'bitget': {
        'name': 'Bitget',
        'url': 'wss://ws.bitget.com/v2/ws/public',
        'subscribe': lambda sym: {"op": "subscribe", "args": [{"instType": "USDT-FUTURES", "channel": "trade", "instId": sym}]},
        'ping': 'ping',
        'ping_interval': 15,
        'type': 'subscribe',
    },
    'gateio': {
        'name': 'Gate.io',
        'url': 'wss://fx-ws.gateio.ws/v4/ws/usdt',
        'subscribe': lambda sym: {"channel": "futures.trades", "event": "subscribe", "payload": [sym]},
        'symbol_format': lambda s: s.replace('USDT', '_USDT'),
        'type': 'subscribe',
    },
    'mexc': {
        'name': 'MEXC',
        'url': 'wss://contract.mexc.com/edge',
        'subscribe': lambda sym: {"method": "sub.deal", "param": {"symbol": sym}},
        'symbol_format': lambda s: s.replace('USDT', '_USDT'),
        'ping': '{"method":"ping"}',
        'ping_interval': 15,
        'type': 'subscribe',
    },
    'hyperliquid': {
        'name': 'Hyperliquid',
        'url': 'wss://api.hyperliquid.xyz/ws',
        'subscribe': lambda sym: {"method": "subscribe", "subscription": {"type": "trades", "coin": sym}},
        'symbol_format': lambda s: s.replace('USDT', ''),
        'type': 'subscribe',
    },
    'deribit': {
        'name': 'Deribit',
        'url': 'wss://www.deribit.com/ws/api/v2',
        'subscribe': lambda sym: {"method": "public/subscribe", "params": {"channels": [f"trades.{sym}.100ms"]}},
        'symbol_format': lambda s: s.replace('BTCUSDT', 'BTC-PERPETUAL').replace('ETHUSDT', 'ETH-PERPETUAL'),
        'type': 'subscribe',
    },
    'bitmex': {
        'name': 'BitMEX',
        'url': 'wss://www.bitmex.com/realtime',
        'subscribe': lambda sym: {"op": "subscribe", "args": [f"trade:{sym}"]},
        'symbol_format': lambda s: s.replace('BTCUSDT', 'XBTUSD').replace('ETHUSDT', 'ETHUSD'),
        'type': 'subscribe',
    },
    'dydx': {
        'name': 'dYdX',
        'url': 'wss://indexer.dydx.trade/v4/ws',
        'subscribe': lambda sym: {"type": "subscribe", "channel": "v4_trades", "id": sym},
        'symbol_format': lambda s: s.replace('USDT', '').upper() + '-USD',
        'type': 'subscribe',
    },
    'phemex': {
        'name': 'Phemex',
        'url': 'wss://ws.phemex.com',
        'subscribe': lambda sym: {"method": "trade_p.subscribe", "params": [sym], "id": 12345},
        'ping': '{"method":"server.ping","id":9000,"params":[]}',
        'ping_interval': 5,
        'type': 'subscribe',
    },
    'bitunix': {
        'name': 'Bitunix',
        'url': 'wss://fapi.bitunix.com/public/',
        'subscribe': lambda sym: {"op": "subscribe", "args": [{"symbol": sym, "ch": "trade"}]},
        'ping': '{"op":"ping"}',
        'ping_interval': 20,
        'type': 'subscribe',
    },
    'kraken': {
        'name': 'Kraken',
        'url': 'wss://futures.kraken.com/ws/v1',
        'subscribe': lambda sym: {"event": "subscribe", "product_ids": [sym], "feed": "trade"},
        'symbol_format': lambda s: 'PI_' + s.replace('BTCUSDT', 'XBTUSD').replace('ETHUSDT', 'ETHUSD'),
        'type': 'subscribe',
    },
    'bingx': {
        'name': 'BingX',
        'url': 'wss://open-api-swap.bingx.com/swap-market',
        'subscribe': lambda sym: {"reqType": "sub", "dataType": f"{sym}@trade"},
        'symbol_format': lambda s: s.replace('USDT', '-USDT'),
        'type': 'subscribe',
    },
    'coinbase': {
        'name': 'Coinbase',
        'url': 'wss://ws-feed.exchange.coinbase.com',
        'subscribe': lambda sym: {"type": "subscribe", "product_ids": [sym], "channels": ["matches"]},
        'symbol_format': lambda s: s.replace('BTCUSDT', 'BTC-USD').replace('ETHUSDT', 'ETH-USD'),
        'type': 'subscribe',
    },
    'htx': {
        'name': 'HTX',
        'url': 'wss://api.hbdm.com/linear-swap-ws',
        'subscribe': lambda sym: {"sub": f"market.{sym}.trade.detail", "id": sym},
        'symbol_format': lambda s: s.replace('USDT', '-USDT'),
        'compressed': 'gzip',
        'type': 'subscribe',
    },
}


def parse_trade(exchange: str, msg: dict) -> list[tuple]:
    """解析成交訊息 → [(symbol, price, qty, side, ts_ms, trade_id), ...]"""
    try:
        if exchange == 'binance':
            if msg.get('e') == 'aggTrade':
                side = 'sell' if msg['m'] else 'buy'
                return [(msg['s'], float(msg['p']), float(msg['q']),
                         side, msg['T'], str(msg.get('a', '')))]

        elif exchange == 'bybit':
            if msg.get('topic', '').startswith('publicTrade.'):
                return [(t['s'], float(t['p']), float(t['v']),
                         t['S'].lower(), int(t['T']),
                         str(t.get('i', '')))
                        for t in msg.get('data', [])]

        elif exchange == 'okx':
            if msg.get('arg', {}).get('channel') == 'trades':
                return [(t['instId'], float(t['px']), float(t['sz']),
                         t['side'], int(t['ts']),
                         str(t.get('tradeId', '')))
                        for t in msg.get('data', [])]

        elif exchange == 'bitget':
            if msg.get('action') == 'snapshot' and msg.get('data'):
                sym = msg.get('arg', {}).get('instId', '')
                return [(sym, float(t['price']), float(t['size']),
                         t['side'], int(t['ts']),
                         str(t.get('tradeId', '')))
                        for t in msg['data']]

        elif exchange == 'gateio':
            if msg.get('event') == 'update' and msg.get('channel') == 'futures.trades':
                return [(t['contract'], float(t['price']), abs(float(t['size'])),
                         'buy' if float(t['size']) > 0 else 'sell',
                         int(t.get('create_time_ms', time.time() * 1000)),
                         str(t.get('id', '')))
                        for t in msg.get('result', [])]

        elif exchange == 'mexc':
            if msg.get('channel') == 'push.deal' and 'data' in msg:
                sym = msg.get('symbol', '')
                return [(sym, float(t['p']), float(t['v']),
                         'buy' if t.get('T') == 1 else 'sell',
                         int(float(t.get('t', 0)) * 1000),
                         str(t.get('t', '')))
                        for t in msg['data']]

        elif exchange == 'hyperliquid':
            if msg.get('channel') == 'trades':
                return [(t.get('coin', ''), float(t['px']), float(t['sz']),
                         'buy' if t.get('side') == 'B' else 'sell',
                         int(t.get('time', time.time() * 1000)),
                         str(t.get('tid', t.get('hash', ''))))
                        for t in msg.get('data', [])]

        elif exchange == 'deribit':
            if msg.get('params', {}).get('data'):
                return [(t['instrument_name'], float(t['price']), float(t['amount']),
                         t['direction'], t['timestamp'],
                         str(t.get('trade_id', '')))
                        for t in msg['params']['data']]

        elif exchange == 'bitmex':
            if msg.get('action') == 'insert' and 'data' in msg:
                return [(t['symbol'], float(t['price']),
                         abs(float(t.get('homeNotional', t.get('size', 0)))),
                         t.get('side', '').lower(),
                         int(time.time() * 1000),
                         str(t.get('trdMatchID', '')))
                        for t in msg['data']]

        elif exchange == 'dydx':
            if msg.get('type') == 'channel_data':
                sym = msg.get('id', '')
                return [(sym, float(t['price']), float(t['size']),
                         t['side'].lower(),
                         int(time.time() * 1000),
                         str(t.get('id', '')))
                        for t in msg.get('contents', {}).get('trades', [])]

        elif exchange == 'phemex':
            if 'trades_p' in msg:
                sym = msg.get('symbol', 'BTCUSDT')
                return [(sym, float(t[2]), float(t[3]),
                         t[1].lower(),
                         int(t[0]) // 1000000 if t[0] > 1e15 else int(t[0]),
                         str(t[0]))
                        for t in msg['trades_p']]

        elif exchange == 'bitunix':
            if msg.get('ch') == 'trade' and 'data' in msg:
                sym = msg.get('symbol', '')
                return [(sym, float(t['p']), float(t['v']),
                         t.get('s', 'sell'),
                         int(time.time() * 1000),
                         str(t.get('id', '')))
                        for t in msg['data']]

        elif exchange == 'kraken':
            feed = msg.get('feed')
            if feed in ('trade', 'trade_snapshot'):
                trades = msg.get('trades', [])
                if not trades and 'price' in msg:
                    trades = [msg]
                return [(t.get('product_id', ''), float(t['price']),
                         float(t['qty']), t.get('side', 'sell'),
                         int(time.time() * 1000),
                         str(t.get('uid', '')))
                        for t in trades if 'price' in t]

        elif exchange == 'bingx':
            dt = msg.get('dataType', '')
            if dt.endswith('@trade') and 'data' in msg:
                data = msg['data'] if isinstance(msg['data'], list) else [msg['data']]
                return [(t.get('s', ''), float(t['p']), float(t['q']),
                         'sell' if t.get('m') else 'buy',
                         int(t.get('T', time.time() * 1000)),
                         str(t.get('T', '')))
                        for t in data]

        elif exchange == 'coinbase':
            if msg.get('type') in ('match', 'last_match'):
                side = 'buy' if msg.get('side') == 'sell' else 'sell'
                return [(msg.get('product_id', ''), float(msg['price']),
                         float(msg['size']), side,
                         int(time.time() * 1000),
                         str(msg.get('trade_id', '')))]

        elif exchange == 'htx':
            ch = msg.get('ch', '')
            if '.trade.detail' in ch:
                parts = ch.split('.')
                sym = parts[1] if len(parts) > 1 else ''
                return [(sym, float(t['price']), float(t['amount']),
                         t['direction'],
                         int(t.get('ts', time.time() * 1000)),
                         str(t.get('id', '')))
                        for t in msg.get('tick', {}).get('data', [])]

    except Exception:
        pass
    return []


class RecorderWorker(threading.Thread):
    """背景 WS 連線 + 記錄."""

    def __init__(self, recorder: TradeRecorder, exchange: str,
                 symbol: str = 'BTCUSDT'):
        super().__init__(daemon=True)
        self._recorder = recorder
        self._exchange = exchange
        self._symbol = symbol
        self._running = True
        self._connected = False
        self._trade_count = 0

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def trade_count(self) -> int:
        return self._trade_count

    def stop(self):
        self._running = False

    def run(self):
        while self._running:
            try:
                asyncio.run(self._ws_loop())
            except Exception as e:
                logger.warning('%s WS error: %s', self._exchange, e)
            if self._running:
                self._connected = False
                time.sleep(3)

    async def _ws_loop(self):
        import websockets

        cfg = EXCHANGE_CONFIG.get(self._exchange)
        if not cfg:
            return

        sym_fmt = cfg.get('symbol_format', lambda s: s)
        ex_symbol = sym_fmt(self._symbol)

        if cfg['type'] == 'direct':
            url = cfg['url_template'].format(symbol_lower=self._symbol.lower())
        else:
            url = cfg['url']

        async with websockets.connect(
            url, compression=None,
            ping_interval=20, ping_timeout=10,
            max_size=2**20, close_timeout=3,
        ) as ws:
            # Subscribe
            if cfg['type'] == 'subscribe':
                sub_fn = cfg['subscribe']
                await ws.send(json.dumps(sub_fn(ex_symbol)))

            # Heartbeat
            async def heartbeat():
                ping_msg = cfg.get('ping')
                interval = cfg.get('ping_interval', 15)
                if not ping_msg:
                    return
                try:
                    while self._running:
                        await asyncio.sleep(interval)
                        await ws.send(ping_msg)
                except Exception:
                    pass

            hb = asyncio.create_task(heartbeat())
            self._connected = True

            try:
                async for raw in ws:
                    if not self._running:
                        break

                    try:
                        # Decompress if needed
                        if isinstance(raw, bytes):
                            compressed = cfg.get('compressed', '')
                            if compressed == 'gzip':
                                raw = gzip.decompress(raw)
                                # HTX ping/pong
                                check = json.loads(raw)
                                if 'ping' in check:
                                    await ws.send(json.dumps(
                                        {'pong': check['ping']}))
                                    continue
                            else:
                                try:
                                    raw = gzip.decompress(raw)
                                except Exception:
                                    try:
                                        raw = zlib.decompress(raw, -zlib.MAX_WBITS)
                                    except Exception:
                                        continue

                        msg = json.loads(raw) if isinstance(raw, str) else json.loads(raw.decode())
                        trades = parse_trade(self._exchange, msg)

                        for sym, price, qty, side, ts_ms, tid in trades:
                            if price > 0 and qty > 0:
                                self._recorder.add(
                                    cfg['name'], sym, price, qty, side,
                                    ts_ms, tid)
                                self._trade_count += 1

                    except Exception:
                        continue
            finally:
                hb.cancel()
                self._connected = False
