"""
app.py — Entry point for the modular Image Processing Laboratory.

Run:
    python app.py
"""
import os
import sys

# macOS: let the Qt main loop handle AVFoundation camera auth
os.environ.setdefault("OPENCV_AVFOUNDATION_SKIP_AUTH", "1")
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt

from config import THEME
from ui.main_window import MainWindow


def build_palette() -> QPalette:
    p = QPalette()
    p.setColor(QPalette.Window,          QColor(THEME["base"]))
    p.setColor(QPalette.WindowText,      QColor(THEME["text"]))
    p.setColor(QPalette.Base,            QColor(THEME["mantle"]))
    p.setColor(QPalette.AlternateBase,   QColor(THEME["surface0"]))
    p.setColor(QPalette.ToolTipBase,     QColor(THEME["surface0"]))
    p.setColor(QPalette.ToolTipText,     QColor(THEME["text"]))
    p.setColor(QPalette.Text,            QColor(THEME["text"]))
    p.setColor(QPalette.Button,          QColor(THEME["surface0"]))
    p.setColor(QPalette.ButtonText,      QColor(THEME["text"]))
    p.setColor(QPalette.BrightText,      QColor(THEME["rosewater"]))
    p.setColor(QPalette.Link,            QColor(THEME["blue"]))
    p.setColor(QPalette.Highlight,       QColor(THEME["accent"]))
    p.setColor(QPalette.HighlightedText, QColor(THEME["text"]))
    # Disabled
    p.setColor(QPalette.Disabled, QPalette.Text,       QColor(THEME["overlay0"]))
    p.setColor(QPalette.Disabled, QPalette.ButtonText,  QColor(THEME["overlay0"]))
    p.setColor(QPalette.Disabled, QPalette.WindowText,  QColor(THEME["overlay0"]))
    return p


if __name__ == "__main__":
    # High-DPI support
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps,    True)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setPalette(build_palette())

    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
