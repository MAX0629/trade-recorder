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

        # Row 1: Symbol
        row1 = QHBoxLayout()
        row1.addWidget(QLabel('Symbol:'))
        self._symbol_input = QLineEdit('BTCUSDT')
        self._symbol_input.setFixedWidth(120)
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

        # ── Recent Trades Table ──
        self._table = QTableWidget(0, 7)
        self._table.setHorizontalHeaderLabels(
            ['Time', 'Exchange', 'Symbol', 'Price', 'Qty', 'Side', 'USD'])
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
        symbol = self._symbol_input.text().strip().upper()
        if not symbol:
            return

        selected = [ex_id for ex_id, cb in self._exchange_checks.items()
                    if cb.isChecked()]
        if not selected:
            return

        # 清掉舊的 workers
        self._stop_workers()

        # 啟動新 workers
        for ex_id in selected:
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
        sym = self._symbol_input.text().strip() or 'UNKNOWN'
        ts = time.strftime('%Y%m%d_%H%M%S')
        filepath = os.path.join('data', f'trades_{sym}_{ts}.csv')
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

        # Update table (last 50)
        recent = self._recorder.get_recent(50)
        self._table.setRowCount(len(recent))
        for i, t in enumerate(reversed(recent)):
            row = i
            self._table.setItem(row, 0, QTableWidgetItem(t['datetime']))
            self._table.setItem(row, 1, QTableWidgetItem(t['exchange']))
            self._table.setItem(row, 2, QTableWidgetItem(t['symbol']))
            self._table.setItem(row, 3, QTableWidgetItem(f"${t['price']:,.2f}"))

            qty_item = QTableWidgetItem(f"{t['qty']:.6f}")
            self._table.setItem(row, 4, qty_item)

            side_item = QTableWidgetItem(t['side'].upper())
            side_item.setForeground(QColor(_GREEN) if t['side'] == 'buy' else QColor(_RED))
            self._table.setItem(row, 5, side_item)

            self._table.setItem(row, 6, QTableWidgetItem(f"${t['usd_value']:,.2f}"))

    def closeEvent(self, event):
        self._timer.stop()
        self._stop_workers()
        super().closeEvent(event)
