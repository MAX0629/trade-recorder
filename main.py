"""Trade Recorder — Open-source multi-exchange trade recorder.

Records every single trade from 16 exchanges via WebSocket.
Export to CSV with zero data loss.

Usage:
    python main.py
"""
import sys
import os
import logging

# Ensure module directory is in path (for both source and frozen EXE)
_dir = os.path.dirname(os.path.abspath(__file__))
if _dir not in sys.path:
    sys.path.insert(0, _dir)


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
