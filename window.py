"""TradeRecorderWindow — 成交記錄器主視窗."""
import time
import os

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QComboBox, QLineEdit, QFileDialog,
                              QTableWidget, QTableWidgetItem, QHeaderView,
                              QCheckBox, QGroupBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QPalette, QFont

try:
    from trade_recorder_qt.recorder import (
        TradeRecorder, RecorderWorker, EXCHANGE_CONFIG)
except ImportError:
    from recorder import TradeRecorder, RecorderWorker, EXCHANGE_CONFIG


_BG = '#0a0a14'
_CYAN = '#00ccff'
_GREEN = '#26a69a'
_RED = '#ef5350'
_YELLOW = '#ffd700'
_WHITE = '#e0e0e0'
_GRAY = '#555555'
_FONT = 'Consolas'


class TradeRecorderWindow(QWidget):
    """成交記錄器主視窗."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Trade Recorder — Open Source')
        self.resize(900, 650)
        self.setMinimumSize(700, 450)

        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor(_BG))
        pal.setColor(QPalette.ColorRole.WindowText, QColor(_WHITE))
        self.setPalette(pal)
        self.setStyleSheet(f"""
            QWidget {{ background: {_BG}; color: {_WHITE}; font-family: {_FONT}; font-size: 10px; }}
            QPushButton {{ background: #1a1a3a; color: {_CYAN}; border: 1px solid {_CYAN};
                           padding: 6px 14px; font-weight: bold; }}
            QPushButton:hover {{ background: #2a2a5a; }}
            QPushButton:disabled {{ color: {_GRAY}; border-color: {_GRAY}; }}
            QComboBox, QLineEdit {{ background: #12122a; color: {_WHITE}; border: 1px solid #333;
                                    padding: 4px; }}
            QTableWidget {{ background: #0d0d1a; color: {_WHITE}; gridline-color: #1a1a2e;
                            selection-background-color: #1a2a4a; }}
            QHeaderView::section {{ background: #12122a; color: {_CYAN}; border: 1px solid #1a1a2e;
                                    font-weight: bold; padding: 4px; }}
            QGroupBox {{ border: 1px solid #333; margin-top: 8px; padding-top: 12px;
                         color: {_CYAN}; font-weight: bold; }}
            QCheckBox {{ color: {_WHITE}; }}
        """)

        self._recorder = TradeRecorder()
        self._workers: list[RecorderWorker] = []

        self._build_ui()

        # 更新 timer
        self._timer = QTimer(self)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self._update_ui)
        self._timer.start()

        # 自動匯出 timer (1 小時)
        self._auto_export_timer = QTimer(self)
        self._auto_export_timer.setInterval(3600 * 1000)  # 1hr
        self._auto_export_timer.timeout.connect(self._auto_export)
        self._auto_export_enabled = False

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # ── Title ──
        title = QLabel('TRADE RECORDER')
        title.setFont(QFont(_FONT, 16, QFont.Weight.Bold))
        title.setStyleSheet(f'color: {_CYAN};')
        layout.addWidget(title)

        # ── Config ──
        config_group = QGroupBox('Configuration')
        config_layout = QVBoxLayout(config_group)

        # Row 1: Symbols (comma-separated)
        row1 = QHBoxLayout()
        row1.addWidget(QLabel('Symbols:'))
        self._symbol_input = QLineEdit('BTCUSDT,ETHUSDT,SOLUSDT')
        self._symbol_input.setFixedWidth(300)
        self._symbol_input.setPlaceholderText('e.g. BTCUSDT,ETHUSDT,SOLUSDT')
        row1.addWidget(self._symbol_input)
        row1.addStretch()
        config_layout.addLayout(row1)

        # Row 2: Exchanges (checkboxes)
        row2 = QHBoxLayout()
        row2.addWidget(QLabel('Exchanges:'))
        self._exchange_checks: dict[str, QCheckBox] = {}

        # 分兩行顯示
        ex_grid = QVBoxLayout()
        ex_row1 = QHBoxLayout()
        ex_row2 = QHBoxLayout()
        all_exchanges = list(EXCHANGE_CONFIG.keys())
        mid = (len(all_exchanges) + 1) // 2
        for i, ex_id in enumerate(all_exchanges):
            name = EXCHANGE_CONFIG[ex_id]['name']
            cb = QCheckBox(name)
            if ex_id in ('binance', 'bybit', 'okx'):
                cb.setChecked(True)
            self._exchange_checks[ex_id] = cb
            if i < mid:
                ex_row1.addWidget(cb)
            else:
                ex_row2.addWidget(cb)
        ex_row1.addStretch()
        ex_row2.addStretch()
        ex_grid.addLayout(ex_row1)
        ex_grid.addLayout(ex_row2)
        row2.addLayout(ex_grid)
        config_layout.addLayout(row2)

        layout.addWidget(config_group)

        # ── Buttons ──
        btn_row = QHBoxLayout()

        self._btn_start = QPushButton('Start Recording')
        self._btn_start.clicked.connect(self._start_recording)
        btn_row.addWidget(self._btn_start)

        self._btn_stop = QPushButton('Stop')
        self._btn_stop.setEnabled(False)
        self._btn_stop.clicked.connect(self._stop_recording)
        btn_row.addWidget(self._btn_stop)

        self._btn_export = QPushButton('Export CSV')
        self._btn_export.clicked.connect(self._export_csv)
        btn_row.addWidget(self._btn_export)

        self._btn_clear = QPushButton('Clear')
        self._btn_clear.clicked.connect(self._clear_data)
        btn_row.addWidget(self._btn_clear)

        self._auto_export_cb = QCheckBox('Auto Export (1hr)')
        self._auto_export_cb.toggled.connect(self._toggle_auto_export)
        btn_row.addWidget(self._auto_export_cb)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        # ── Stats ──
        self._stats_label = QLabel('Ready')
        self._stats_label.setFont(QFont(_FONT, 10))
        self._stats_label.setStyleSheet(f'color: {_CYAN};')
        layout.addWidget(self._stats_label)

        # ── Connection Status ──
        self._conn_label = QLabel('')
        self._conn_label.setFont(QFont(_FONT, 9))
        layout.addWidget(self._conn_label)

        # ── Verify / Search Panel ──
        verify_group = QGroupBox('Trade Verification / Search')
        verify_layout = QVBoxLayout(verify_group)

        # Row 1: Price + Qty + Time range
        vrow1 = QHBoxLayout()
        vrow1.addWidget(QLabel('Price:'))
        self._v_price = QLineEdit()
        self._v_price.setFixedWidth(90)
        self._v_price.setPlaceholderText('e.g. 2.51')
        vrow1.addWidget(self._v_price)

        vrow1.addWidget(QLabel('Qty:'))
        self._v_qty = QLineEdit()
        self._v_qty.setFixedWidth(80)
        self._v_qty.setPlaceholderText('e.g. 12632')
        vrow1.addWidget(self._v_qty)

        vrow1.addWidget(QLabel('Side:'))
        self._v_side = QComboBox()
        self._v_side.addItems(['Any', 'buy', 'sell'])
        self._v_side.setFixedWidth(60)
        vrow1.addWidget(self._v_side)

        vrow1.addWidget(QLabel('Min USD:'))
        self._v_min_usd = QLineEdit()
        self._v_min_usd.setFixedWidth(80)
        self._v_min_usd.setPlaceholderText('e.g. 10000')
        vrow1.addWidget(self._v_min_usd)

        vrow1.addStretch()
        verify_layout.addLayout(vrow1)

        # Row 2: Tolerance + buttons
        vrow2 = QHBoxLayout()
        vrow2.addWidget(QLabel('Price tolerance:'))
        self._v_tol = QLineEdit('0.5')
        self._v_tol.setFixedWidth(50)
        self._v_tol.setToolTip('Price match tolerance in %')
        vrow2.addWidget(self._v_tol)
        vrow2.addWidget(QLabel('%'))

        self._btn_verify = QPushButton('Verify Trade')
        self._btn_verify.setStyleSheet(
            f'background: #1a3a1a; color: {_GREEN}; border: 1px solid {_GREEN};'
            f' font-weight: bold; padding: 6px 14px;')
        self._btn_verify.clicked.connect(self._verify_trade)
        vrow2.addWidget(self._btn_verify)

        self._btn_show_large = QPushButton('Show Large (>$10K)')
        self._btn_show_large.clicked.connect(self._show_large_trades)
        vrow2.addWidget(self._btn_show_large)

        self._btn_show_all = QPushButton('Show All')
        self._btn_show_all.clicked.connect(self._show_all_trades)
        vrow2.addWidget(self._btn_show_all)

        vrow2.addStretch()
        verify_layout.addLayout(vrow2)

        # Verify result
        self._verify_result = QLabel('')
        self._verify_result.setWordWrap(True)
        self._verify_result.setFont(QFont(_FONT, 9))
        verify_layout.addWidget(self._verify_result)

        layout.addWidget(verify_group)

        # ── Recent Trades Table ──
        self._filtered_trades = None  # None = show recent, list = filtered
        self._table = QTableWidget(0, 8)
        self._table.setHorizontalHeaderLabels(
            ['Time', 'Exchange', 'Symbol', 'Trade ID', 'Price', 'Qty', 'Side', 'USD'])
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet(
            'alternate-background-color: #10102a; '
            'selection-background-color: #1a2a4a;')
        layout.addWidget(self._table)

    def _start_recording(self):
        raw = self._symbol_input.text().strip().upper()
        if not raw:
            return
        symbols = [s.strip() for s in raw.split(',') if s.strip()]
        if not symbols:
            return

        selected = [ex_id for ex_id, cb in self._exchange_checks.items()
                    if cb.isChecked()]
        if not selected:
            return

        # 清掉舊的 workers
        self._stop_workers()

        # 每個交易所 × 每個幣種 = 一個 worker
        for ex_id in selected:
            for symbol in symbols:
                w = RecorderWorker(self._recorder, ex_id, symbol)
                w.start()
                self._workers.append(w)

        self._btn_start.setEnabled(False)
        self._btn_stop.setEnabled(True)
        self._symbol_input.setEnabled(False)
        for cb in self._exchange_checks.values():
            cb.setEnabled(False)

    def _stop_recording(self):
        self._stop_workers()
        self._btn_start.setEnabled(True)
        self._btn_stop.setEnabled(False)
        self._symbol_input.setEnabled(True)
        for cb in self._exchange_checks.values():
            cb.setEnabled(True)

    def _stop_workers(self):
        for w in self._workers:
            w.stop()
        # 等待結束 (非阻塞, daemon threads)
        self._workers.clear()

    def _export_csv(self):
        count = self._recorder.get_count()
        if count == 0:
            self._stats_label.setText('No trades to export')
            return

        default_name = f'trades_{self._symbol_input.text()}_{time.strftime("%Y%m%d_%H%M%S")}.csv'
        filepath, _ = QFileDialog.getSaveFileName(
            self, 'Export CSV', default_name, 'CSV Files (*.csv)')
        if filepath:
            n = self._recorder.export_csv(filepath)
            self._stats_label.setText(f'Exported {n:,} trades to {os.path.basename(filepath)}')

    def _clear_data(self):
        self._recorder.clear()
        self._table.setRowCount(0)
        self._stats_label.setText('Cleared')

    def _toggle_auto_export(self, checked: bool):
        self._auto_export_enabled = checked
        if checked:
            self._auto_export_timer.start()
            self._stats_label.setText('Auto export: every 1 hour')
        else:
            self._auto_export_timer.stop()

    def _auto_export(self):
        count = self._recorder.get_count()
        if count == 0:
            return
        raw = self._symbol_input.text().strip().replace(',', '_') or 'UNKNOWN'
        ts = time.strftime('%Y%m%d_%H%M%S')
        filepath = os.path.join('data', f'trades_{raw}_{ts}.csv')
        os.makedirs('data', exist_ok=True)
        n = self._recorder.export_csv(filepath)
        self._stats_label.setText(f'Auto exported {n:,} trades → {filepath}')

    def _update_ui(self):
        stats = self._recorder.get_stats()
        count = stats['count']
        buy = stats['buy_usd']
        sell = stats['sell_usd']
        dur = stats['duration_sec']

        if dur > 0:
            rate = count / dur
            self._stats_label.setText(
                f'Trades: {count:,} | '
                f'Buy: ${buy:,.0f} | Sell: ${sell:,.0f} | '
                f'Delta: ${buy - sell:+,.0f} | '
                f'Rate: {rate:.1f}/s | '
                f'Duration: {dur / 60:.1f}min')

        # Connection status
        parts = []
        for w in self._workers:
            cfg = EXCHANGE_CONFIG.get(w._exchange, {})
            name = cfg.get('name', w._exchange)
            if w.connected:
                parts.append(f'<span style="color:{_GREEN}">● {name} ({w.trade_count:,})</span>')
            else:
                parts.append(f'<span style="color:{_RED}">○ {name}</span>')
        self._conn_label.setText('  '.join(parts))

        # Update table
        if self._filtered_trades is not None:
            trades = self._filtered_trades
        else:
            trades = list(reversed(self._recorder.get_recent(50)))

        self._table.setRowCount(len(trades))
        for row, t in enumerate(trades):
            self._table.setItem(row, 0, QTableWidgetItem(t['datetime']))
            self._table.setItem(row, 1, QTableWidgetItem(t['exchange']))
            self._table.setItem(row, 2, QTableWidgetItem(t['symbol']))
            self._table.setItem(row, 3, QTableWidgetItem(t.get('trade_id', '')))
            self._table.setItem(row, 4, QTableWidgetItem(f"${t['price']:,.2f}"))

            qty_item = QTableWidgetItem(f"{t['qty']:.6f}")
            self._table.setItem(row, 5, qty_item)

            side_item = QTableWidgetItem(t['side'].upper())
            side_item.setForeground(QColor(_GREEN) if t['side'] == 'buy' else QColor(_RED))
            self._table.setItem(row, 6, side_item)

            usd = t['usd_value']
            usd_item = QTableWidgetItem(f"${usd:,.2f}")
            # Large trade highlight
            if usd >= 100_000:
                usd_item.setForeground(QColor('#ff1744'))
                usd_item.setFont(QFont(_FONT, 10, QFont.Weight.Bold))
            elif usd >= 10_000:
                usd_item.setForeground(QColor(_YELLOW))
                usd_item.setFont(QFont(_FONT, 10, QFont.Weight.Bold))
            self._table.setItem(row, 7, usd_item)

    def _verify_trade(self):
        """交易驗證 — 搜尋匹配的成交紀錄."""
        with self._recorder._lock:
            all_trades = list(self._recorder._trades)

        if not all_trades:
            self._verify_result.setText(
                '<span style="color:#ef5350">No trades recorded yet. '
                'Start recording first.</span>')
            return

        # 解析搜尋條件
        price_str = self._v_price.text().strip()
        qty_str = self._v_qty.text().strip()
        side_filter = self._v_side.currentText()
        min_usd_str = self._v_min_usd.text().strip()
        tol_str = self._v_tol.text().strip()

        target_price = float(price_str) if price_str else 0
        target_qty = float(qty_str) if qty_str else 0
        min_usd = float(min_usd_str) if min_usd_str else 0
        tol_pct = float(tol_str) if tol_str else 0.5

        # 篩選
        matches = []
        for t in all_trades:
            # Side filter
            if side_filter != 'Any' and t['side'] != side_filter:
                continue
            # Min USD filter
            if min_usd > 0 and t['usd_value'] < min_usd:
                continue
            # Price match (within tolerance %)
            if target_price > 0:
                diff_pct = abs(t['price'] - target_price) / target_price * 100
                if diff_pct > tol_pct:
                    continue
            # Qty match (within 10%)
            if target_qty > 0:
                diff_qty = abs(t['qty'] - target_qty) / target_qty * 100
                if diff_qty > 10:
                    continue
            matches.append(t)

        # 顯示結果
        if matches:
            # 統計
            total_usd = sum(m['usd_value'] for m in matches)
            exchanges = set(m['exchange'] for m in matches)
            buy_ct = sum(1 for m in matches if m['side'] == 'buy')
            sell_ct = sum(1 for m in matches if m['side'] == 'sell')
            largest = max(matches, key=lambda m: m['usd_value'])

            self._verify_result.setText(
                f'<span style="color:{_GREEN}">'
                f'FOUND {len(matches)} matching trades | '
                f'Total: ${total_usd:,.2f} | '
                f'Buy: {buy_ct} Sell: {sell_ct} | '
                f'Exchanges: {", ".join(exchanges)} | '
                f'Largest: ${largest["usd_value"]:,.2f} @ {largest["exchange"]}'
                f'</span>')

            # 在表格顯示匹配結果
            self._filtered_trades = list(reversed(matches))
        else:
            conditions = []
            if target_price > 0:
                conditions.append(f'price=${target_price} +/-{tol_pct}%')
            if target_qty > 0:
                conditions.append(f'qty={target_qty} +/-10%')
            if side_filter != 'Any':
                conditions.append(f'side={side_filter}')
            if min_usd > 0:
                conditions.append(f'min ${min_usd:,.0f}')

            self._verify_result.setText(
                f'<span style="color:{_RED}">'
                f'NO MATCH found in {len(all_trades):,} trades. '
                f'Conditions: {", ".join(conditions) or "none"} | '
                f'Trade may be FAKE or not recorded during this session.'
                f'</span>')
            self._filtered_trades = []

    def _show_large_trades(self):
        """顯示所有 > $10K 的大單."""
        with self._recorder._lock:
            all_trades = list(self._recorder._trades)

        large = [t for t in all_trades if t['usd_value'] >= 10_000]
        large.sort(key=lambda t: t['usd_value'], reverse=True)

        if large:
            total = sum(t['usd_value'] for t in large)
            self._verify_result.setText(
                f'<span style="color:{_YELLOW}">'
                f'{len(large)} large trades (>$10K) | '
                f'Total: ${total:,.0f} | '
                f'Largest: ${large[0]["usd_value"]:,.0f} '
                f'@ {large[0]["exchange"]} {large[0]["symbol"]}'
                f'</span>')
            self._filtered_trades = large
        else:
            self._verify_result.setText(
                f'<span style="color:{_GRAY}">No trades >$10K found</span>')
            self._filtered_trades = []

    def _show_all_trades(self):
        """回到即時模式（最新 50 筆）."""
        self._filtered_trades = None
        self._verify_result.setText('')

    def closeEvent(self, event):
        self._timer.stop()
        self._stop_workers()
        super().closeEvent(event)
