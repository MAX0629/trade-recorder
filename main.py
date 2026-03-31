"""Trade Recorder — Open-source multi-exchange trade recorder.

Records every single trade from 16 exchanges via WebSocket.
Export to CSV with zero data loss.

Usage:
    python main.py
"""
import sys
import logging


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(name)s] %(levelname)s %(message)s',
        datefmt='%H:%M:%S',
    )

    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    from window import TradeRecorderWindow
    win = TradeRecorderWindow()
    win.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
