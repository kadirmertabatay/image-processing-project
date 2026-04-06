"""
ui/main_window.py — MVC coordinator: wires processor, threads, and widgets.
Modern dark glassmorphism design with gradient accents.
"""
from __future__ import annotations

import os
import cv2
import numpy as np

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QGroupBox, QScrollArea, QFrame,
    QTabWidget, QGridLayout, QSizePolicy, QTextEdit, QSplitter,
    QGraphicsDropShadowEffect,
)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QImage, QPixmap, QFont, QColor

from config import THEME
from core.processor import ImageProcessor
from utils.stream import FrameGrabber, AnalysisWorker
from utils.logger import setup_logger
from ui.widgets.control_panel import ControlPanel
from ui.widgets.formula_view import FormulaView
from ui.widgets.charts import HistogramWidget, Surface3DWidget, FFTWidget, ColorSpaceWidget


# ─── Style Constants ─────────────────────────────────────────────────────────

CARD_STYLE = f"""
    QFrame {{
        background: {THEME['mantle']};
        border: 1px solid {THEME['surface1']};
        border-radius: 10px;
    }}
"""

GROUP_STYLE = f"""
    QGroupBox {{
        color: {THEME['text']};
        border: 1px solid {THEME['surface1']};
        border-radius: 10px;
        margin-top: 10px;
        padding-top: 6px;
        font-weight: bold;
        font-size: 11px;
        background: {THEME['mantle']};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
        color: {THEME['lavender']};
    }}
"""

TAB_STYLE = f"""
    QTabWidget::pane {{
        border: 1px solid {THEME['surface1']};
        border-radius: 8px;
        background: {THEME['mantle']};
        top: -1px;
    }}
    QTabBar::tab {{
        background: {THEME['surface0']};
        color: {THEME['subtext']};
        border: 1px solid {THEME['surface1']};
        border-bottom: none;
        border-radius: 6px 6px 0 0;
        padding: 6px 14px;
        font-size: 10px;
        margin-right: 2px;
        min-width: 60px;
    }}
    QTabBar::tab:hover {{
        background: {THEME['surface1']};
        color: {THEME['text']};
    }}
    QTabBar::tab:selected {{
        background: {THEME['mantle']};
        color: {THEME['mauve']};
        font-weight: bold;
        border-bottom: 2px solid {THEME['mauve']};
    }}
"""

BTN_PRIMARY = f"""
    QPushButton {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {THEME['accent']}, stop:1 {THEME['mauve']});
        color: white;
        border: none;
        border-radius: 8px;
        padding: 9px 12px;
        font-size: 11px;
        font-weight: bold;
        text-align: left;
    }}
    QPushButton:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {THEME['mauve']}, stop:1 {THEME['pink']});
    }}
    QPushButton:pressed {{
        background: {THEME['accent']};
    }}
"""

BTN_SECONDARY = f"""
    QPushButton {{
        background: {THEME['surface0']};
        color: {THEME['text']};
        border: 1px solid {THEME['surface1']};
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 10px;
        text-align: left;
    }}
    QPushButton:hover {{
        background: {THEME['surface1']};
        border-color: {THEME['mauve']};
        color: {THEME['lavender']};
    }}
    QPushButton:pressed {{
        background: {THEME['accent']};
        color: white;
    }}
"""

BTN_GHOST = f"""
    QPushButton {{
        background: transparent;
        color: {THEME['subtext']};
        border: 1px solid {THEME['surface1']};
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 10px;
        text-align: left;
    }}
    QPushButton:hover {{
        background: {THEME['surface0']};
        border-color: {THEME['teal']};
        color: {THEME['teal']};
    }}
    QPushButton:pressed {{
        background: {THEME['surface1']};
    }}
"""


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _frame_to_pixmap(frame: np.ndarray, label: QLabel) -> QPixmap:
    rgb  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
    return QPixmap.fromImage(qimg).scaled(
        label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
    )


def _add_glow(widget: QWidget, color: str = THEME["accent"], radius: int = 20):
    """Add a subtle drop shadow / glow to a widget."""
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(radius)
    shadow.setColor(QColor(color))
    shadow.setOffset(0, 2)
    widget.setGraphicsEffect(shadow)


# ─── Main Window ─────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Görüntü İşleme Laboratuvarı  v2.0")
        self.resize(1500, 940)
        self.setStyleSheet(f"""
            QMainWindow {{
                background: {THEME['base']};
                color: {THEME['text']};
            }}
            QToolTip {{
                background: {THEME['surface0']};
                color: {THEME['text']};
                border: 1px solid {THEME['surface1']};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 10px;
            }}
        """)

        # State
        self.processor       = ImageProcessor()
        self.current_frame:  np.ndarray | None = None
        self._last_result                       = None
        self._frame_ticker                      = 0
        self._grabber:       FrameGrabber | None = None
        self._worker:        AnalysisWorker | None = None
        self._current_color_space               = "BGR"

        # Build
        self._build_ui()

        # Logger (widget available after _build_ui)
        self._log = setup_logger("isp", self._log_widget)
        self._log.info("Uygulama başlatıldı.")

    # ─── UI construction ────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # ── Header bar ──
        main_layout.addWidget(self._build_header())

        # ── Content area ──
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setSpacing(10)
        content_layout.setContentsMargins(10, 10, 10, 10)

        content_layout.addWidget(self._build_left_panel(), 0)
        content_layout.addWidget(self._build_center_panel(), 1)
        content_layout.addWidget(self._build_right_panel(), 0)

        main_layout.addWidget(content, 1)

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setFixedHeight(52)
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {THEME['crust']}, stop:0.5 {THEME['base']}, stop:1 {THEME['crust']});
                border-bottom: 1px solid {THEME['surface1']};
            }}
        """)
        hlay = QHBoxLayout(header)
        hlay.setContentsMargins(16, 0, 16, 0)

        # Logo / title
        logo = QLabel("◉")
        logo.setStyleSheet(f"""
            color: {THEME['mauve']};
            font-size: 22px;
            font-weight: bold;
            padding-right: 6px;
        """)
        hlay.addWidget(logo)

        title = QLabel("Görüntü İşleme Laboratuvarı")
        title.setStyleSheet(f"""
            color: {THEME['text']};
            font-size: 15px;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        hlay.addWidget(title)

        version = QLabel("v2.0")
        version.setStyleSheet(f"""
            color: {THEME['overlay0']};
            font-size: 10px;
            padding-left: 4px;
            padding-top: 4px;
        """)
        hlay.addWidget(version)

        hlay.addStretch()

        # Status indicator
        self._header_status = QLabel("● Hazır")
        self._header_status.setStyleSheet(f"""
            color: {THEME['green']};
            font-size: 10px;
            font-weight: bold;
        """)
        hlay.addWidget(self._header_status)

        return header

    # ── Left panel ───────────────────────────────────────────────────────────

    def _build_left_panel(self) -> QWidget:
        w = QWidget()
        w.setFixedWidth(305)
        vbox = QVBoxLayout(w)
        vbox.setSpacing(8)
        vbox.setContentsMargins(0, 0, 0, 0)

        # Source controls
        vbox.addWidget(self._build_source_panel())

        # Scrollable control panel
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {THEME['surface1']};
                border-radius: 10px;
                background: {THEME['mantle']};
            }}
            QScrollBar:vertical {{
                background: {THEME['mantle']};
                width: 6px;
                border-radius: 3px;
                margin: 4px 0;
            }}
            QScrollBar::handle:vertical {{
                background: {THEME['surface2']};
                border-radius: 3px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {THEME['mauve']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)
        self._control_panel = ControlPanel()
        self._control_panel.params_changed.connect(self._on_params_changed)
        scroll.setWidget(self._control_panel)
        vbox.addWidget(scroll, 1)

        # Log viewer
        log_frame = QFrame()
        log_frame.setStyleSheet(CARD_STYLE)
        log_lay = QVBoxLayout(log_frame)
        log_lay.setContentsMargins(8, 8, 8, 8)
        log_lay.setSpacing(4)

        log_title = QLabel("📋  İşlem Günlüğü")
        log_title.setStyleSheet(f"color: {THEME['lavender']}; font-weight: bold; font-size: 10px; border: none;")
        log_lay.addWidget(log_title)

        self._log_widget = QTextEdit()
        self._log_widget.setReadOnly(True)
        self._log_widget.setMaximumHeight(110)
        self._log_widget.setStyleSheet(f"""
            QTextEdit {{
                background: {THEME['crust']};
                color: {THEME['subtext']};
                border: 1px solid {THEME['surface0']};
                border-radius: 6px;
                font-size: 9px;
                font-family: 'SF Mono', 'Menlo', 'Monaco', monospace;
                padding: 4px;
            }}
        """)
        log_lay.addWidget(self._log_widget)
        vbox.addWidget(log_frame)
        return w

    def _build_source_panel(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(CARD_STYLE)
        lay = QVBoxLayout(frame)
        lay.setSpacing(6)
        lay.setContentsMargins(10, 10, 10, 10)

        src_title = QLabel("🎯  Giriş Kaynağı")
        src_title.setStyleSheet(f"color: {THEME['lavender']}; font-weight: bold; font-size: 11px; border: none;")
        lay.addWidget(src_title)

        # Webcam button — primary style
        self._webcam_btn = QPushButton("📷  Webcam Başlat / Durdur")
        self._webcam_btn.setStyleSheet(BTN_PRIMARY)
        self._webcam_btn.clicked.connect(self._toggle_webcam)
        lay.addWidget(self._webcam_btn)

        img_btn = QPushButton("🖼  Fotoğraf Yükle...")
        img_btn.setStyleSheet(BTN_SECONDARY)
        img_btn.clicked.connect(self._load_image)
        lay.addWidget(img_btn)

        vid_btn = QPushButton("🎞  Video Yükle...")
        vid_btn.setStyleSheet(BTN_SECONDARY)
        vid_btn.clicked.connect(self._load_video)
        lay.addWidget(vid_btn)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"border: none; border-top: 1px solid {THEME['surface1']}; margin: 2px 0;")
        lay.addWidget(sep)

        save_btn = QPushButton("💾  Görüntüyü Kaydet")
        save_btn.setStyleSheet(BTN_GHOST)
        save_btn.clicked.connect(self._save_image)
        lay.addWidget(save_btn)

        report_btn = QPushButton("📄  PDF Rapor Dışa Aktar")
        report_btn.setStyleSheet(BTN_GHOST)
        report_btn.clicked.connect(self._export_report)
        lay.addWidget(report_btn)

        analyse_btn = QPushButton("🔬  Derin Analiz Çalıştır")
        analyse_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {THEME['teal']}, stop:1 {THEME['sapphire']});
                color: {THEME['crust']};
                border: none;
                border-radius: 8px;
                padding: 9px 12px;
                font-size: 10px;
                font-weight: bold;
                text-align: left;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {THEME['green']}, stop:1 {THEME['teal']});
            }}
            QPushButton:pressed {{ background: {THEME['teal']}; }}
        """)
        analyse_btn.setToolTip("3-D yüzey, FFT ve detaylı istatistikler hesaplanır (arka plan)")
        analyse_btn.clicked.connect(self._run_deep_analysis)
        lay.addWidget(analyse_btn)

        self._status_lbl = QLabel("● Hazır")
        self._status_lbl.setStyleSheet(f"color: {THEME['green']}; font-size: 9px; padding: 3px; border: none;")
        self._status_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(self._status_lbl)
        return frame

    # ── Center panel ─────────────────────────────────────────────────────────

    def _build_center_panel(self) -> QWidget:
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setSpacing(8)
        vbox.setContentsMargins(0, 0, 0, 0)

        # Image display row
        img_row = QHBoxLayout()
        img_row.setSpacing(8)
        img_row.addWidget(self._make_image_display("Orijinal Görüntü", "original"))
        img_row.addWidget(self._make_image_display("İşlenmiş Görüntü", "processed"))
        vbox.addLayout(img_row, stretch=3)

        # Analysis tabs
        self._analysis_tabs = QTabWidget()
        self._analysis_tabs.setStyleSheet(TAB_STYLE)

        self._histogram_widget = HistogramWidget()
        self._surface3d_widget = Surface3DWidget()
        self._fft_widget       = FFTWidget()
        self._colorspace_widget= ColorSpaceWidget()

        self._analysis_tabs.addTab(self._histogram_widget,  "📊  Histogram")
        self._analysis_tabs.addTab(self._surface3d_widget,  "🏔  3-D Yüzey")
        self._analysis_tabs.addTab(self._fft_widget,        "🌊  FFT Spektrum")
        self._analysis_tabs.addTab(self._colorspace_widget, "🎨  Renk Uzayı")
        self._analysis_tabs.currentChanged.connect(self._on_tab_changed)

        vbox.addWidget(self._analysis_tabs, stretch=2)
        return w

    def _make_image_display(self, title: str, key: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(CARD_STYLE)
        vbox = QVBoxLayout(card)
        vbox.setSpacing(4)
        vbox.setContentsMargins(6, 6, 6, 6)

        # Title bar with gradient
        title_frame = QFrame()
        accent = THEME["blue"] if key == "original" else THEME["green"]
        title_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {accent}44, stop:1 transparent);
                border-radius: 6px;
                border: none;
            }}
        """)
        tlay = QHBoxLayout(title_frame)
        tlay.setContentsMargins(8, 4, 8, 4)

        indicator = QLabel("●")
        indicator.setStyleSheet(f"color: {accent}; font-size: 8px; border: none;")
        tlay.addWidget(indicator)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"""
            color: {THEME['text']};
            font-size: 11px;
            font-weight: bold;
            border: none;
        """)
        tlay.addWidget(title_lbl)
        tlay.addStretch()

        vbox.addWidget(title_frame)

        img_lbl = QLabel()
        img_lbl.setAlignment(Qt.AlignCenter)
        img_lbl.setStyleSheet(f"""
            background: {THEME['crust']};
            border-radius: 8px;
            border: 1px solid {THEME['surface0']};
        """)
        img_lbl.setMinimumSize(360, 260)
        img_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        vbox.addWidget(img_lbl)

        if key == "original":
            self._original_lbl = img_lbl
        else:
            self._processed_lbl = img_lbl

        return card

    # ── Right panel ──────────────────────────────────────────────────────────

    def _build_right_panel(self) -> QWidget:
        w = QWidget()
        w.setFixedWidth(285)
        vbox = QVBoxLayout(w)
        vbox.setSpacing(8)
        vbox.setContentsMargins(0, 0, 0, 0)

        # Formula view
        self._formula_view = FormulaView()
        vbox.addWidget(self._formula_view, stretch=3)

        # Stats panel
        stats_frame = QFrame()
        stats_frame.setStyleSheet(CARD_STYLE)
        stats_lay = QVBoxLayout(stats_frame)
        stats_lay.setSpacing(4)
        stats_lay.setContentsMargins(10, 10, 10, 10)

        # Stats header
        stats_header = QFrame()
        stats_header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {THEME['yellow']}33, stop:1 transparent);
                border-radius: 6px;
                border: none;
            }}
        """)
        shlay = QHBoxLayout(stats_header)
        shlay.setContentsMargins(8, 4, 8, 4)
        stitle = QLabel("📐  Görüntü İstatistikleri")
        stitle.setStyleSheet(f"color: {THEME['yellow']}; font-weight: bold; font-size: 11px; border: none;")
        shlay.addWidget(stitle)
        stats_lay.addWidget(stats_header)

        self._stats_labels: dict[str, QLabel] = {}
        grid = QGridLayout()
        grid.setSpacing(3)

        fields = [
            ("resolution",   "Çözünürlük",   THEME["text"]),
            ("channels",     "Kanallar",     THEME["text"]),
            ("bit_depth",    "Bit Derinliği",THEME["text"]),
            ("r_mean",       "R Ort.",       THEME["red"]),
            ("g_mean",       "G Ort.",       THEME["green"]),
            ("b_mean",       "B Ort.",       THEME["blue"]),
            ("r_std",        "R Std",        THEME["red"]),
            ("g_std",        "G Std",        THEME["green"]),
            ("b_std",        "B Std",        THEME["blue"]),
            ("overall_mean", "Genel Ort.",   THEME["lavender"]),
            ("overall_std",  "Genel Std",    THEME["lavender"]),
            ("min",          "Min Piksel",   THEME["text"]),
            ("max",          "Max Piksel",   THEME["text"]),
            ("entropy",      "Entropi",      THEME["peach"]),
            ("snr",          "SNR",          THEME["peach"]),
        ]
        for row, (key, label, val_color) in enumerate(fields):
            lbl = QLabel(label + ":")
            lbl.setStyleSheet(f"color: {THEME['subtext']}; font-size: 9px; border: none;")
            val = QLabel("—")
            val.setStyleSheet(f"color: {val_color}; font-size: 9px; font-weight: bold; border: none;")
            val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            grid.addWidget(lbl, row, 0)
            grid.addWidget(val, row, 1)
            self._stats_labels[key] = val

        stats_lay.addLayout(grid)
        vbox.addWidget(stats_frame, stretch=2)
        return w

    # ─── Event handlers ──────────────────────────────────────────────────────

    def _set_status(self, text: str, color: str = THEME["green"]):
        self._status_lbl.setText(f"● {text}")
        self._status_lbl.setStyleSheet(f"color: {color}; font-size: 9px; padding: 3px; border: none;")
        self._header_status.setText(f"● {text}")
        self._header_status.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: bold;")

    def _toggle_webcam(self):
        if self._grabber and self._grabber.isRunning():
            self._stop_grabber()
            self._set_status("Webcam durduruldu", THEME["yellow"])
            self._log.info("Webcam durduruldu.")
        else:
            self._stop_grabber()
            self._start_grabber(0)

    def _load_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Fotoğraf Seç", "",
            "Görüntü Dosyaları (*.png *.jpg *.jpeg *.bmp *.tiff *.webp)"
        )
        if not path:
            return
        self._stop_grabber()
        frame = cv2.imread(path)
        if frame is None:
            self._set_status("Görüntü yüklenemedi!", THEME["red"])
            return
        self._log.info(f"Fotoğraf yüklendi: {os.path.basename(path)}")
        self._set_status(f"Foto: {os.path.basename(path)}", THEME["blue"])
        self._start_grabber(frame)

    def _load_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Video Seç", "",
            "Video Dosyaları (*.mp4 *.avi *.mov *.mkv *.wmv)"
        )
        if not path:
            return
        self._stop_grabber()
        self._log.info(f"Video yüklendi: {os.path.basename(path)}")
        self._set_status(f"Video: {os.path.basename(path)}", THEME["sapphire"])
        self._start_grabber(path)

    def _save_image(self):
        if self._last_result is None or self._last_result.frame is None:
            self._set_status("Kaydedilecek görüntü yok.", THEME["yellow"])
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Kaydet", "processed.png", "PNG (*.png);;JPEG (*.jpg)"
        )
        if path:
            cv2.imwrite(path, self._last_result.frame)
            self._log.info(f"Kaydedildi: {path}")
            self._set_status(f"Kaydedildi ✓", THEME["green"])

    def _export_report(self):
        if self.current_frame is None:
            self._set_status("Önce bir görüntü yükleyin.", THEME["yellow"])
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "PDF Kaydet", "rapor.pdf", "PDF (*.pdf)"
        )
        if not path:
            return
        from core.statistics import ImageStats, ReportExporter
        stats = ImageStats.compute(self.current_frame)
        ops   = self._last_result.active_ops if self._last_result else []
        processed = self._last_result.frame if self._last_result else None
        ok = ReportExporter.export_pdf(
            path, self.current_frame, processed,
            stats, {"active_ops": ops}
        )
        if ok:
            self._log.info(f"PDF raporu kaydedildi: {path}")
            self._set_status("PDF hazır ✓", THEME["green"])
        else:
            self._set_status("PDF oluşturulamadı!", THEME["red"])

    def _run_deep_analysis(self):
        if self.current_frame is None:
            self._set_status("Önce bir görüntü yükleyin.", THEME["yellow"])
            return
        if self._worker and self._worker.isRunning():
            return
        self._set_status("Analiz çalışıyor…", THEME["sapphire"])
        self._log.info("Derin analiz başlatıldı.")
        self._worker = AnalysisWorker(
            self.current_frame,
            {"fft", "surface3d", "stats"},
        )
        self._worker.result_ready.connect(self._on_analysis_done)
        self._worker.start()

    @pyqtSlot(dict)
    def _on_analysis_done(self, result: dict):
        self._set_status("Analiz tamamlandı ✓", THEME["green"])
        self._log.info("Derin analiz tamamlandı.")

        if "surface3d" in result:
            self._surface3d_widget.update_surface(result["surface3d"])

        if "fft" in result:
            self._fft_widget.update_fft(result["fft"])

        if "stats" in result:
            self._update_stats_display(result["stats"])

    def _on_tab_changed(self, idx: int):
        tab_title = self._analysis_tabs.tabText(idx)
        if "Renk Uzayı" in tab_title and self.current_frame is not None:
            self._colorspace_widget.update_frame(
                self.current_frame, self._current_color_space
            )

    @pyqtSlot(dict)
    def _on_params_changed(self, params: dict):
        self._current_color_space = params.get("color_space", "BGR")
        self.processor.update_params(params)
        if self.current_frame is not None and (
            self._grabber is None or not self._grabber.isRunning()
        ):
            self._process_and_display()

    # ─── Frame pipeline ──────────────────────────────────────────────────────

    def _start_grabber(self, source):
        self._grabber = FrameGrabber(source)
        self._grabber.frame_ready.connect(self._on_frame)
        self._grabber.error.connect(lambda e: (
            self._set_status(e, THEME["red"]),
            self._log.error(e)
        ))
        self._grabber.start()
        if isinstance(source, int):
            self._set_status("Webcam aktif", THEME["green"])
            self._log.info("Webcam başlatıldı.")

    def _stop_grabber(self):
        if self._grabber:
            self._grabber.stop()
            self._grabber = None

    @pyqtSlot(object)
    def _on_frame(self, frame: np.ndarray):
        self.current_frame = frame
        self._process_and_display()

    def _process_and_display(self):
        if self.current_frame is None:
            return

        result = self.processor.process(self.current_frame)
        self._last_result = result

        # Show images
        self._original_lbl.setPixmap(
            _frame_to_pixmap(self.current_frame, self._original_lbl)
        )
        self._processed_lbl.setPixmap(
            _frame_to_pixmap(result.frame, self._processed_lbl)
        )

        # Formula panel
        self._formula_view.update_formula(result.formula_key, result.kernel)

        # Throttle expensive updates for live video
        self._frame_ticker += 1
        if self._frame_ticker % 5 == 0 or (
            self._grabber is None or not self._grabber.isRunning()
        ):
            self._frame_ticker = 0
            self._histogram_widget.update_frame(self.current_frame)

            if self._analysis_tabs.currentIndex() == 3:
                self._colorspace_widget.update_frame(
                    self.current_frame, self._current_color_space
                )

            from core.statistics import ImageStats
            stats = ImageStats.compute(self.current_frame)
            self._update_stats_display(stats)

    # ─── Stats display ───────────────────────────────────────────────────────

    def _update_stats_display(self, stats: dict):
        if not stats:
            return
        L = self._stats_labels
        L["resolution"].setText(f"{stats.get('width','?')} × {stats.get('height','?')}")
        L["channels"].setText(f"{stats.get('channels','?')} ch")
        L["bit_depth"].setText(f"{stats.get('bit_depth','?')} bit")
        L["r_mean"].setText(f"{stats.get('r_mean',0):.1f}")
        L["g_mean"].setText(f"{stats.get('g_mean',0):.1f}")
        L["b_mean"].setText(f"{stats.get('b_mean',0):.1f}")
        L["r_std"].setText(f"{stats.get('r_std',0):.1f}")
        L["g_std"].setText(f"{stats.get('g_std',0):.1f}")
        L["b_std"].setText(f"{stats.get('b_std',0):.1f}")
        L["overall_mean"].setText(f"{stats.get('overall_mean',0):.1f}")
        L["overall_std"].setText(f"{stats.get('overall_std',0):.1f}")
        L["min"].setText(str(stats.get('min', '?')))
        L["max"].setText(str(stats.get('max', '?')))
        L["entropy"].setText(f"{stats.get('entropy',0):.3f}")
        L["snr"].setText(f"{stats.get('snr',0):.2f}")

    # ─── Lifecycle ───────────────────────────────────────────────────────────

    def closeEvent(self, event):
        self._log.info("Uygulama kapatılıyor…")
        self._stop_grabber()
        if self._worker and self._worker.isRunning():
            self._worker.wait(2000)
        super().closeEvent(event)
