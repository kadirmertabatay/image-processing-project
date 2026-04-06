"""
ui/main_window.py — MVC coordinator: wires processor, threads, and widgets.
"""
from __future__ import annotations

import os
import cv2
import numpy as np

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QGroupBox, QScrollArea, QFrame,
    QTabWidget, QGridLayout, QSizePolicy, QTextEdit, QSplitter,
)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QImage, QPixmap, QFont

from config import THEME
from core.processor import ImageProcessor
from utils.stream import FrameGrabber, AnalysisWorker
from utils.logger import setup_logger
from ui.widgets.control_panel import ControlPanel
from ui.widgets.formula_view import FormulaView
from ui.widgets.charts import HistogramWidget, Surface3DWidget, FFTWidget, ColorSpaceWidget


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _make_group(title: str) -> tuple[QGroupBox, QVBoxLayout]:
    g = QGroupBox(title)
    g.setStyleSheet(f"""
        QGroupBox {{
            color: {THEME['text']};
            border: 1px solid {THEME['surface1']};
            border-radius: 6px;
            margin-top: 8px;
            padding-top: 4px;
            font-weight: bold;
            font-size: 11px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 8px;
            padding: 0 4px;
        }}
    """)
    lay = QVBoxLayout(g)
    lay.setSpacing(4)
    lay.setContentsMargins(6, 12, 6, 6)
    return g, lay


def _btn(label: str, color: str = THEME["surface0"]) -> QPushButton:
    b = QPushButton(label)
    b.setStyleSheet(f"""
        QPushButton {{
            background: {color};
            color: {THEME['text']};
            border: 1px solid {THEME['surface1']};
            border-radius: 6px;
            padding: 7px 10px;
            font-size: 10px;
            text-align: left;
        }}
        QPushButton:hover   {{ background: {THEME['surface1']}; border-color: {THEME['mauve']}; }}
        QPushButton:pressed {{ background: {THEME['accent']};   border-color: {THEME['mauve']}; }}
    """)
    return b


def _frame_to_pixmap(frame: np.ndarray, label: QLabel) -> QPixmap:
    rgb  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
    return QPixmap.fromImage(qimg).scaled(
        label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
    )


# ─── Main Window ─────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Görüntü İşleme Laboratuvarı  v2.0")
        self.resize(1500, 920)
        self.setStyleSheet(f"background: {THEME['base']}; color: {THEME['text']};")

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
        root = QHBoxLayout(central)
        root.setSpacing(8)
        root.setContentsMargins(8, 8, 8, 8)

        root.addWidget(self._build_left_panel(), 0)
        root.addWidget(self._build_center_panel(), 1)
        root.addWidget(self._build_right_panel(), 0)

    # ── Left panel ───────────────────────────────────────────────────────────

    def _build_left_panel(self) -> QWidget:
        w = QWidget()
        w.setFixedWidth(300)
        vbox = QVBoxLayout(w)
        vbox.setSpacing(8)
        vbox.setContentsMargins(0, 0, 0, 0)

        # Source controls
        vbox.addWidget(self._build_source_panel())

        # Scrollable control panel
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea           {{ border: none; background: transparent; }}
            QScrollBar:vertical   {{ background: {THEME['surface0']}; width: 7px; border-radius: 3px; }}
            QScrollBar::handle:vertical {{ background: {THEME['surface2']}; border-radius: 3px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)
        self._control_panel = ControlPanel()
        self._control_panel.params_changed.connect(self._on_params_changed)
        scroll.setWidget(self._control_panel)
        vbox.addWidget(scroll, 1)

        # Log viewer
        log_grp, log_lay = _make_group("İşlem Günlüğü")
        self._log_widget = QTextEdit()
        self._log_widget.setReadOnly(True)
        self._log_widget.setMaximumHeight(130)
        self._log_widget.setStyleSheet(
            f"background: {THEME['mantle']}; color: {THEME['subtext']}; "
            f"border: none; font-size: 9px; font-family: monospace;"
        )
        log_lay.addWidget(self._log_widget)
        vbox.addWidget(log_grp)
        return w

    def _build_source_panel(self) -> QGroupBox:
        grp, lay = _make_group("Giriş Kaynağı")

        self._webcam_btn = _btn("📷  Webcam Başlat / Durdur")
        self._webcam_btn.clicked.connect(self._toggle_webcam)
        lay.addWidget(self._webcam_btn)

        img_btn = _btn("🖼  Fotoğraf Yükle...")
        img_btn.clicked.connect(self._load_image)
        lay.addWidget(img_btn)

        vid_btn = _btn("🎞  Video Yükle...")
        vid_btn.clicked.connect(self._load_video)
        lay.addWidget(vid_btn)

        save_btn = _btn("💾  İşlenmiş Görüntüyü Kaydet", THEME["mantle"])
        save_btn.clicked.connect(self._save_image)
        lay.addWidget(save_btn)

        report_btn = _btn("📄  PDF Rapor Dışa Aktar", THEME["mantle"])
        report_btn.clicked.connect(self._export_report)
        lay.addWidget(report_btn)

        analyse_btn = _btn("🔬  Derin Analiz Çalıştır", THEME["crust"])
        analyse_btn.setToolTip("3-D yüzey, FFT ve detaylı istatistikler hesaplanır (arka plan)")
        analyse_btn.clicked.connect(self._run_deep_analysis)
        lay.addWidget(analyse_btn)

        self._status_lbl = QLabel("Hazır")
        self._status_lbl.setStyleSheet(
            f"color: {THEME['overlay0']}; font-size: 9px; padding: 2px;"
        )
        self._status_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(self._status_lbl)
        return grp

    # ── Center panel ─────────────────────────────────────────────────────────

    def _build_center_panel(self) -> QWidget:
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setSpacing(6)
        vbox.setContentsMargins(0, 0, 0, 0)

        # Image display row
        img_row = QHBoxLayout()
        img_row.addWidget(self._make_image_display("Orijinal",   "original"))
        img_row.addWidget(self._make_image_display("İşlenmiş",   "processed"))
        vbox.addLayout(img_row, stretch=3)

        # Analysis tabs
        self._analysis_tabs = QTabWidget()
        self._analysis_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {THEME['surface1']};
                border-radius: 6px;
                background: {THEME['mantle']};
            }}
            QTabBar::tab {{
                background: {THEME['surface0']};
                color: {THEME['subtext']};
                border: 1px solid {THEME['surface1']};
                border-bottom: none;
                border-radius: 4px 4px 0 0;
                padding: 4px 10px;
                font-size: 10px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background: {THEME['mantle']};
                color: {THEME['mauve']};
                font-weight: bold;
            }}
        """)

        self._histogram_widget = HistogramWidget()
        self._surface3d_widget = Surface3DWidget()
        self._fft_widget       = FFTWidget()
        self._colorspace_widget= ColorSpaceWidget()

        self._analysis_tabs.addTab(self._histogram_widget,  "Histogram")
        self._analysis_tabs.addTab(self._surface3d_widget,  "3-D Yüzey")
        self._analysis_tabs.addTab(self._fft_widget,        "FFT Spektrum")
        self._analysis_tabs.addTab(self._colorspace_widget, "Renk Uzayı")
        self._analysis_tabs.currentChanged.connect(self._on_tab_changed)

        vbox.addWidget(self._analysis_tabs, stretch=2)
        return w

    def _make_image_display(self, title: str, key: str) -> QWidget:
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setSpacing(2)
        vbox.setContentsMargins(0, 0, 0, 0)

        title_lbl = QLabel(title)
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet(
            f"color: {THEME['text']}; font-size: 11px; font-weight: bold; "
            f"background: {THEME['surface0']}; border-radius: 4px; padding: 3px;"
        )
        vbox.addWidget(title_lbl)

        img_lbl = QLabel()
        img_lbl.setAlignment(Qt.AlignCenter)
        img_lbl.setStyleSheet(f"background: {THEME['mantle']}; border-radius: 6px;")
        img_lbl.setMinimumSize(360, 260)
        img_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        vbox.addWidget(img_lbl)

        if key == "original":
            self._original_lbl = img_lbl
        else:
            self._processed_lbl = img_lbl

        return container

    # ── Right panel ──────────────────────────────────────────────────────────

    def _build_right_panel(self) -> QWidget:
        w = QWidget()
        w.setFixedWidth(280)
        vbox = QVBoxLayout(w)
        vbox.setSpacing(8)
        vbox.setContentsMargins(0, 0, 0, 0)

        # Formula view
        self._formula_view = FormulaView()
        vbox.addWidget(self._formula_view, stretch=3)

        # Stats panel
        stats_frame = QFrame()
        stats_frame.setStyleSheet(
            f"background: {THEME['mantle']}; border-radius: 8px; border: 1px solid {THEME['surface1']};"
        )
        stats_lay = QVBoxLayout(stats_frame)
        stats_lay.setSpacing(4)
        stats_lay.setContentsMargins(8, 8, 8, 8)

        stitle = QLabel("Görüntü İstatistikleri")
        stitle.setStyleSheet(f"color: {THEME['mauve']}; font-weight: bold; font-size: 11px; border: none;")
        stats_lay.addWidget(stitle)

        self._stats_labels: dict[str, QLabel] = {}
        grid = QGridLayout()
        grid.setSpacing(3)

        fields = [
            ("resolution",   "Çözünürlük"),
            ("channels",     "Kanallar"),
            ("bit_depth",    "Bit Derinliği"),
            ("r_mean",       "R Ort."),
            ("g_mean",       "G Ort."),
            ("b_mean",       "B Ort."),
            ("r_std",        "R Std"),
            ("g_std",        "G Std"),
            ("b_std",        "B Std"),
            ("overall_mean", "Genel Ort."),
            ("overall_std",  "Genel Std"),
            ("min",          "Min Piksel"),
            ("max",          "Max Piksel"),
            ("entropy",      "Entropi (bit)"),
            ("snr",          "SNR"),
        ]
        for row, (key, label) in enumerate(fields):
            lbl = QLabel(label + ":")
            lbl.setStyleSheet(f"color: {THEME['subtext']}; font-size: 9px; border: none;")
            val = QLabel("—")
            val.setStyleSheet(f"color: {THEME['text']}; font-size: 9px; font-weight: bold; border: none;")
            val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            grid.addWidget(lbl, row, 0)
            grid.addWidget(val, row, 1)
            self._stats_labels[key] = val

        stats_lay.addLayout(grid)
        vbox.addWidget(stats_frame, stretch=2)
        return w

    # ─── Event handlers ──────────────────────────────────────────────────────

    def _toggle_webcam(self):
        if self._grabber and self._grabber.isRunning():
            self._stop_grabber()
            self._status_lbl.setText("Webcam durduruldu")
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
            self._status_lbl.setText("Görüntü yüklenemedi!")
            return
        self._log.info(f"Fotoğraf yüklendi: {os.path.basename(path)}")
        self._status_lbl.setText(f"Foto: {os.path.basename(path)}")
        self._start_grabber(frame)  # emit once

    def _load_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Video Seç", "",
            "Video Dosyaları (*.mp4 *.avi *.mov *.mkv *.wmv)"
        )
        if not path:
            return
        self._stop_grabber()
        self._log.info(f"Video yüklendi: {os.path.basename(path)}")
        self._status_lbl.setText(f"Video: {os.path.basename(path)}")
        self._start_grabber(path)

    def _save_image(self):
        if self._last_result is None or self._last_result.frame is None:
            self._status_lbl.setText("Kaydedilecek görüntü yok.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Kaydet", "processed.png", "PNG (*.png);;JPEG (*.jpg)"
        )
        if path:
            cv2.imwrite(path, self._last_result.frame)
            self._log.info(f"Kaydedildi: {path}")
            self._status_lbl.setText(f"Kaydedildi: {os.path.basename(path)}")

    def _export_report(self):
        if self.current_frame is None:
            self._status_lbl.setText("Önce bir görüntü yükleyin.")
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
            self._status_lbl.setText("PDF hazır!")
        else:
            self._status_lbl.setText("PDF oluşturulamadı!")

    def _run_deep_analysis(self):
        if self.current_frame is None:
            self._status_lbl.setText("Önce bir görüntü yükleyin.")
            return
        if self._worker and self._worker.isRunning():
            return
        self._status_lbl.setText("Analiz çalışıyor…")
        self._log.info("Derin analiz başlatıldı.")
        self._worker = AnalysisWorker(
            self.current_frame,
            {"fft", "surface3d", "stats"},
        )
        self._worker.result_ready.connect(self._on_analysis_done)
        self._worker.start()

    @pyqtSlot(dict)
    def _on_analysis_done(self, result: dict):
        self._status_lbl.setText("Analiz tamamlandı.")
        self._log.info("Derin analiz tamamlandı.")

        if "surface3d" in result:
            self._surface3d_widget.update_surface(result["surface3d"])

        if "fft" in result:
            self._fft_widget.update_fft(result["fft"])

        if "stats" in result:
            self._update_stats_display(result["stats"])

    def _on_tab_changed(self, idx: int):
        """Update color space tab when it becomes active."""
        tab_title = self._analysis_tabs.tabText(idx)
        if tab_title == "Renk Uzayı" and self.current_frame is not None:
            self._colorspace_widget.update_frame(
                self.current_frame, self._current_color_space
            )

    @pyqtSlot(dict)
    def _on_params_changed(self, params: dict):
        # Track color space separately for the chart tab
        self._current_color_space = params.get("color_space", "BGR")
        self.processor.update_params(params)
        # Re-process current frame if not streaming
        if self.current_frame is not None and (
            self._grabber is None or not self._grabber.isRunning()
        ):
            self._process_and_display()

    # ─── Frame pipeline ──────────────────────────────────────────────────────

    def _start_grabber(self, source):
        self._grabber = FrameGrabber(source)
        self._grabber.frame_ready.connect(self._on_frame)
        self._grabber.error.connect(lambda e: (
            self._status_lbl.setText(e),
            self._log.error(e)
        ))
        self._grabber.start()
        if isinstance(source, int):
            self._status_lbl.setText("Webcam aktif")
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

        # Formula panel (only redraws when key changes)
        self._formula_view.update_formula(result.formula_key, result.kernel)

        # Throttle expensive updates for live video
        self._frame_ticker += 1
        if self._frame_ticker % 5 == 0 or (
            self._grabber is None or not self._grabber.isRunning()
        ):
            self._frame_ticker = 0
            # Histogram always
            self._histogram_widget.update_frame(self.current_frame)

            # Color space — only if tab visible
            if self._analysis_tabs.currentIndex() == 3:
                self._colorspace_widget.update_frame(
                    self.current_frame, self._current_color_space
                )

            # Quick stats from core stats module (lightweight)
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
