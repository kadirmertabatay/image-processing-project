"""
utils/logger.py — Python logging bridge → QTextEdit widget.
"""
from __future__ import annotations

import logging
from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtCore import QMetaObject, Qt, Q_ARG
from PyQt5.QtGui import QColor


class _QTextEditHandler(logging.Handler):
    """Thread-safe logging handler that appends to a QTextEdit."""

    LEVEL_COLORS = {
        logging.DEBUG:   "#89b4fa",   # blue
        logging.INFO:    "#a6e3a1",   # green
        logging.WARNING: "#f9e2af",   # yellow
        logging.ERROR:   "#f38ba8",   # red
        logging.CRITICAL:"#cba6f7",   # mauve
    }

    def __init__(self, widget: QTextEdit):
        super().__init__()
        self._widget = widget

    def emit(self, record: logging.LogRecord):
        try:
            msg  = self.format(record)
            color = self.LEVEL_COLORS.get(record.levelno, "#cdd6f4")
            html  = f'<span style="color:{color}; font-family:monospace; font-size:10px;">{msg}</span>'
            # Thread-safe: post to main thread
            QMetaObject.invokeMethod(
                self._widget, "append",
                Qt.QueuedConnection,
                Q_ARG(str, html),
            )
        except Exception:
            self.handleError(record)


def setup_logger(name: str = "isp", widget: QTextEdit | None = None) -> logging.Logger:
    """
    Create (or retrieve) a named logger.
    If widget is provided, attaches a QTextEdit handler to it.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already configured

    logger.setLevel(logging.DEBUG)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(ch)

    # Widget handler
    if widget is not None:
        wh = _QTextEditHandler(widget)
        wh.setLevel(logging.DEBUG)
        wh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S"))
        logger.addHandler(wh)

    return logger
