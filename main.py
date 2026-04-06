"""
Görüntü İşleme Projesi
Image Processing Tool - PyQt5 + OpenCV + Matplotlib

Özellikler:
- 3 farklı giriş kaynağı: Webcam, Fotoğraf, Video
- Gerçek zamanlı görüntü işleme
- Blur, Parlaklık, Kontrast, Keskinlik ayarları
- R/G/B kanal kontrolü
- Histogram eşitleme
- Kenar tespiti (Canny/Sobel)
- Canlı histogram grafikleri
- Piksel istatistikleri
"""

import sys
import os
import numpy as np
import cv2
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSlider, QComboBox, QFileDialog, QGroupBox,
    QGridLayout, QCheckBox, QTabWidget, QScrollArea, QSizePolicy,
    QFrame, QButtonGroup, QRadioButton, QSpacerItem
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QImage, QPixmap, QFont, QPalette, QColor
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


# ─────────────────────────────────────────────
#  Görüntü İşleyici
# ─────────────────────────────────────────────
class ImageProcessor:
    """Tüm görüntü işleme operasyonlarını yürüten sınıf."""

    def __init__(self):
        self.reset_params()

    def reset_params(self):
        self.blur_amount = 0          # 0-20 (çift sayı kernel)
        self.brightness = 0           # -100 to +100
        self.contrast = 1.0           # 0.5 to 2.5
        self.sharpen = 0              # 0-10
        self.r_gain = 1.0             # 0.0-2.0
        self.g_gain = 1.0
        self.b_gain = 1.0
        self.hist_eq = False
        self.edge_mode = 'none'       # 'none', 'canny', 'sobel'
        self.canny_low = 50
        self.canny_high = 150
        self.flip_h = False
        self.flip_v = False
        self.grayscale = False

    def process(self, frame: np.ndarray) -> np.ndarray:
        if frame is None:
            return None

        img = frame.copy()

        # ── Gri tonlama ──
        if self.grayscale:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            img = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

        # ── Kanal kazanç (RGB) ──
        if self.r_gain != 1.0 or self.g_gain != 1.0 or self.b_gain != 1.0:
            b, g, r = cv2.split(img.astype(np.float32))
            b = np.clip(b * self.b_gain, 0, 255)
            g = np.clip(g * self.g_gain, 0, 255)
            r = np.clip(r * self.r_gain, 0, 255)
            img = cv2.merge([b, g, r]).astype(np.uint8)

        # ── Histogram eşitleme ──
        if self.hist_eq:
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l, a, b_ch = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            lab = cv2.merge([l, a, b_ch])
            img = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

        # ── Parlaklık / Kontrast ──
        if self.brightness != 0 or self.contrast != 1.0:
            img = cv2.convertScaleAbs(img, alpha=self.contrast, beta=self.brightness)

        # ── Keskinleştirme ──
        if self.sharpen > 0:
            strength = self.sharpen / 10.0
            kernel = np.array([
                [0, -strength, 0],
                [-strength, 1 + 4 * strength, -strength],
                [0, -strength, 0]
            ])
            img = cv2.filter2D(img, -1, kernel)
            img = np.clip(img, 0, 255).astype(np.uint8)

        # ── Bulanıklaştırma ──
        if self.blur_amount > 0:
            k = self.blur_amount * 2 + 1
            img = cv2.GaussianBlur(img, (k, k), 0)

        # ── Kenar tespiti ──
        if self.edge_mode == 'canny':
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, self.canny_low, self.canny_high)
            img = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        elif self.edge_mode == 'sobel':
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            sx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            sobel = np.sqrt(sx**2 + sy**2)
            sobel = np.clip(sobel / sobel.max() * 255, 0, 255).astype(np.uint8)
            img = cv2.cvtColor(sobel, cv2.COLOR_GRAY2BGR)

        # ── Çevirme ──
        if self.flip_h:
            img = cv2.flip(img, 1)
        if self.flip_v:
            img = cv2.flip(img, 0)

        return img

    def get_stats(self, frame: np.ndarray) -> dict:
        if frame is None:
            return {}
        h, w = frame.shape[:2]
        channels = frame.shape[2] if len(frame.shape) == 3 else 1
        b, g, r = cv2.split(frame) if channels == 3 else (frame, frame, frame)

        stats = {
            'width': w,
            'height': h,
            'channels': channels,
            'bit_depth': frame.dtype.itemsize * 8,
            'r_mean': float(np.mean(r)),
            'g_mean': float(np.mean(g)),
            'b_mean': float(np.mean(b)),
            'r_std': float(np.std(r)),
            'g_std': float(np.std(g)),
            'b_std': float(np.std(b)),
            'min': int(frame.min()),
            'max': int(frame.max()),
            'overall_mean': float(np.mean(frame)),
        }
        # Entropi hesaplama
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if channels == 3 else frame
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
        hist = hist / hist.sum()
        hist = hist[hist > 0]
        stats['entropy'] = float(-np.sum(hist * np.log2(hist)))
        return stats


# ─────────────────────────────────────────────
#  Histogram Widget (Matplotlib embed)
# ─────────────────────────────────────────────
class HistogramWidget(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(5, 2.5), facecolor='#1e1e2e')
        super().__init__(self.fig)
        self.setParent(parent)
        self.ax = self.fig.add_subplot(111)
        self._style_ax()
        self.fig.tight_layout(pad=1.0)

    def _style_ax(self):
        self.ax.set_facecolor('#1e1e2e')
        self.ax.tick_params(colors='#cdd6f4', labelsize=7)
        for spine in self.ax.spines.values():
            spine.set_color('#45475a')
        self.ax.set_xlabel('Piksel Yoğunluğu', color='#cdd6f4', fontsize=7)
        self.ax.set_ylabel('Frekans', color='#cdd6f4', fontsize=7)

    def update_histogram(self, frame: np.ndarray):
        if frame is None:
            return
        self.ax.clear()
        self._style_ax()

        colors = [('#f38ba8', 'R Kanal'), ('#a6e3a1', 'G Kanal'), ('#89b4fa', 'B Kanal')]
        b, g, r = cv2.split(frame)

        for ch, (color, label) in zip([r, g, b], colors):
            hist = cv2.calcHist([ch], [0], None, [256], [0, 256]).flatten()
            self.ax.plot(hist, color=color, linewidth=0.8, alpha=0.85, label=label)

        self.ax.legend(loc='upper right', fontsize=6, facecolor='#313244',
                       labelcolor='#cdd6f4', framealpha=0.8)
        self.ax.set_xlim([0, 255])
        self.fig.tight_layout(pad=1.0)
        self.draw()


# ─────────────────────────────────────────────
#  Piksel Yoğunluk Dağılımı (bar chart)
# ─────────────────────────────────────────────
class IntensityWidget(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(5, 1.8), facecolor='#1e1e2e')
        super().__init__(self.fig)
        self.setParent(parent)
        self.ax = self.fig.add_subplot(111)
        self._style_ax()
        self.fig.tight_layout(pad=1.0)

    def _style_ax(self):
        self.ax.set_facecolor('#181825')
        self.ax.tick_params(colors='#cdd6f4', labelsize=7)
        for spine in self.ax.spines.values():
            spine.set_color('#45475a')

    def update_intensity(self, frame: np.ndarray):
        if frame is None:
            return
        self.ax.clear()
        self._style_ax()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Bölgelere göre ortalama yoğunluk (4x4 grid)
        h, w = gray.shape
        grid_h, grid_w = h // 4, w // 4
        intensities = []
        for i in range(4):
            for j in range(4):
                region = gray[i*grid_h:(i+1)*grid_h, j*grid_w:(j+1)*grid_w]
                intensities.append(float(np.mean(region)))

        bars = self.ax.bar(range(16), intensities, color='#cba6f7', width=0.7)
        # Renk gradyanı
        for bar, val in zip(bars, intensities):
            normalized = val / 255.0
            bar.set_facecolor((normalized * 0.4 + 0.3, normalized * 0.2 + 0.2, normalized * 0.6 + 0.4))

        self.ax.set_xticks([])
        self.ax.set_title('Bölge Yoğunluk Haritası (4×4)', color='#cdd6f4', fontsize=7)
        self.fig.tight_layout(pad=0.5)
        self.draw()


# ─────────────────────────────────────────────
#  Kontrol Paneli
# ─────────────────────────────────────────────
class ControlPanel(QWidget):
    params_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._connect_signals()

    def _make_group(self, title: str) -> tuple:
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
        """)
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 12, 8, 8)
        return group, layout

    def _make_slider(self, label: str, min_v: int, max_v: int, default: int,
                     layout: QVBoxLayout) -> QSlider:
        row = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setStyleSheet("color: #a6adc8; font-size: 10px; min-width: 80px;")
        val_lbl = QLabel(str(default))
        val_lbl.setStyleSheet("color: #cba6f7; font-size: 10px; min-width: 30px; text-align: right;")
        val_lbl.setAlignment(Qt.AlignRight)

        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(min_v)
        slider.setMaximum(max_v)
        slider.setValue(default)
        slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px;
                background: #45475a;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #cba6f7;
                width: 12px;
                height: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }
            QSlider::sub-page:horizontal {
                background: #7c3aed;
                border-radius: 2px;
            }
        """)
        slider.valueChanged.connect(lambda v: val_lbl.setText(str(v)))
        row.addWidget(lbl)
        row.addWidget(slider)
        row.addWidget(val_lbl)
        layout.addLayout(row)
        return slider

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(4, 4, 4, 4)

        # ── Temel Ayarlar ──
        group1, layout1 = self._make_group("Temel Görüntü Ayarları")
        self.blur_slider = self._make_slider("Blur:", 0, 20, 0, layout1)
        self.brightness_slider = self._make_slider("Parlaklık:", -100, 100, 0, layout1)
        self.contrast_slider = self._make_slider("Kontrast:", 50, 250, 100, layout1)
        self.sharpen_slider = self._make_slider("Keskinlik:", 0, 20, 0, layout1)
        main_layout.addWidget(group1)

        # ── Kanal Kontrolü ──
        group2, layout2 = self._make_group("RGB Kanal Kontrolü")
        self.r_slider = self._make_slider("R Kanalı:", 0, 200, 100, layout2)
        self.g_slider = self._make_slider("G Kanalı:", 0, 200, 100, layout2)
        self.b_slider = self._make_slider("B Kanalı:", 0, 200, 100, layout2)
        main_layout.addWidget(group2)

        # ── Efektler ──
        group3, layout3 = self._make_group("Efektler & Filtreler")

        self.hist_eq_cb = QCheckBox("Histogram Eşitleme (CLAHE)")
        self.hist_eq_cb.setStyleSheet("color: #cdd6f4; font-size: 10px;")
        layout3.addWidget(self.hist_eq_cb)

        self.grayscale_cb = QCheckBox("Gri Tonlama")
        self.grayscale_cb.setStyleSheet("color: #cdd6f4; font-size: 10px;")
        layout3.addWidget(self.grayscale_cb)

        edge_row = QHBoxLayout()
        edge_lbl = QLabel("Kenar Tespiti:")
        edge_lbl.setStyleSheet("color: #a6adc8; font-size: 10px;")
        self.edge_combo = QComboBox()
        self.edge_combo.addItems(["Yok", "Canny", "Sobel"])
        self.edge_combo.setStyleSheet("""
            QComboBox {
                background: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 2px 6px;
                font-size: 10px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background: #313244;
                color: #cdd6f4;
                selection-background-color: #7c3aed;
            }
        """)
        edge_row.addWidget(edge_lbl)
        edge_row.addWidget(self.edge_combo)
        layout3.addLayout(edge_row)

        self.canny_low_slider = self._make_slider("Canny Alt:", 0, 255, 50, layout3)
        self.canny_high_slider = self._make_slider("Canny Üst:", 0, 255, 150, layout3)

        flip_row = QHBoxLayout()
        self.flip_h_cb = QCheckBox("Yatay Çevir")
        self.flip_h_cb.setStyleSheet("color: #cdd6f4; font-size: 10px;")
        self.flip_v_cb = QCheckBox("Dikey Çevir")
        self.flip_v_cb.setStyleSheet("color: #cdd6f4; font-size: 10px;")
        flip_row.addWidget(self.flip_h_cb)
        flip_row.addWidget(self.flip_v_cb)
        layout3.addLayout(flip_row)

        main_layout.addWidget(group3)

        # ── Sıfırlama ──
        reset_btn = QPushButton("Tüm Ayarları Sıfırla")
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #45475a;
                color: #cdd6f4;
                border: none;
                border-radius: 6px;
                padding: 6px;
                font-size: 10px;
            }
            QPushButton:hover { background: #585b70; }
            QPushButton:pressed { background: #313244; }
        """)
        reset_btn.clicked.connect(self._reset_all)
        main_layout.addWidget(reset_btn)
        main_layout.addStretch()

    def _connect_signals(self):
        for slider in [self.blur_slider, self.brightness_slider, self.contrast_slider,
                       self.sharpen_slider, self.r_slider, self.g_slider, self.b_slider,
                       self.canny_low_slider, self.canny_high_slider]:
            slider.valueChanged.connect(self._emit_params)
        for cb in [self.hist_eq_cb, self.grayscale_cb, self.flip_h_cb, self.flip_v_cb]:
            cb.stateChanged.connect(self._emit_params)
        self.edge_combo.currentIndexChanged.connect(self._emit_params)

    def _emit_params(self):
        edge_map = {0: 'none', 1: 'canny', 2: 'sobel'}
        self.params_changed.emit({
            'blur': self.blur_slider.value(),
            'brightness': self.brightness_slider.value(),
            'contrast': self.contrast_slider.value() / 100.0,
            'sharpen': self.sharpen_slider.value(),
            'r_gain': self.r_slider.value() / 100.0,
            'g_gain': self.g_slider.value() / 100.0,
            'b_gain': self.b_slider.value() / 100.0,
            'hist_eq': self.hist_eq_cb.isChecked(),
            'grayscale': self.grayscale_cb.isChecked(),
            'edge_mode': edge_map[self.edge_combo.currentIndex()],
            'canny_low': self.canny_low_slider.value(),
            'canny_high': self.canny_high_slider.value(),
            'flip_h': self.flip_h_cb.isChecked(),
            'flip_v': self.flip_v_cb.isChecked(),
        })

    def _reset_all(self):
        self.blur_slider.setValue(0)
        self.brightness_slider.setValue(0)
        self.contrast_slider.setValue(100)
        self.sharpen_slider.setValue(0)
        self.r_slider.setValue(100)
        self.g_slider.setValue(100)
        self.b_slider.setValue(100)
        self.hist_eq_cb.setChecked(False)
        self.grayscale_cb.setChecked(False)
        self.edge_combo.setCurrentIndex(0)
        self.canny_low_slider.setValue(50)
        self.canny_high_slider.setValue(150)
        self.flip_h_cb.setChecked(False)
        self.flip_v_cb.setChecked(False)


# ─────────────────────────────────────────────
#  İstatistik Paneli
# ─────────────────────────────────────────────
class StatsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 8, 8, 8)

        title = QLabel("Görüntü İstatistikleri")
        title.setStyleSheet("color: #cba6f7; font-weight: bold; font-size: 12px;")
        layout.addWidget(title)

        self.labels = {}
        fields = [
            ('resolution', 'Çözünürlük'),
            ('channels', 'Kanal Sayısı'),
            ('bit_depth', 'Bit Derinliği'),
            ('r_mean', 'R Ortalama'),
            ('g_mean', 'G Ortalama'),
            ('b_mean', 'B Ortalama'),
            ('r_std', 'R Std Sapma'),
            ('g_std', 'G Std Sapma'),
            ('b_std', 'B Std Sapma'),
            ('min', 'Min Piksel'),
            ('max', 'Max Piksel'),
            ('overall_mean', 'Genel Ortalama'),
            ('entropy', 'Entropi (bits)'),
        ]

        grid = QGridLayout()
        grid.setSpacing(4)
        for row, (key, label) in enumerate(fields):
            lbl = QLabel(label + ":")
            lbl.setStyleSheet("color: #a6adc8; font-size: 10px;")
            val = QLabel("—")
            val.setStyleSheet("color: #cdd6f4; font-size: 10px; font-weight: bold;")
            val.setAlignment(Qt.AlignRight)
            grid.addWidget(lbl, row, 0)
            grid.addWidget(val, row, 1)
            self.labels[key] = val

        layout.addLayout(grid)
        layout.addStretch()

    def update_stats(self, stats: dict):
        if not stats:
            return
        self.labels['resolution'].setText(f"{stats.get('width', '?')} × {stats.get('height', '?')}")
        self.labels['channels'].setText(f"{stats.get('channels', '?')} ch")
        self.labels['bit_depth'].setText(f"{stats.get('bit_depth', '?')} bit")
        self.labels['r_mean'].setText(f"{stats.get('r_mean', 0):.1f}")
        self.labels['g_mean'].setText(f"{stats.get('g_mean', 0):.1f}")
        self.labels['b_mean'].setText(f"{stats.get('b_mean', 0):.1f}")
        self.labels['r_std'].setText(f"{stats.get('r_std', 0):.1f}")
        self.labels['g_std'].setText(f"{stats.get('g_std', 0):.1f}")
        self.labels['b_std'].setText(f"{stats.get('b_std', 0):.1f}")
        self.labels['min'].setText(str(stats.get('min', '?')))
        self.labels['max'].setText(str(stats.get('max', '?')))
        self.labels['overall_mean'].setText(f"{stats.get('overall_mean', 0):.1f}")
        self.labels['entropy'].setText(f"{stats.get('entropy', 0):.3f}")


# ─────────────────────────────────────────────
#  Ana Pencere
# ─────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Görüntü İşleme Aracı")
        self.resize(1400, 900)
        self.setStyleSheet("background-color: #1e1e2e; color: #cdd6f4;")

        self.processor = ImageProcessor()
        self.cap = None
        self.current_frame = None
        self.is_playing = False

        self.timer = QTimer()
        self.timer.timeout.connect(self._update_frame)

        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setSpacing(8)
        root.setContentsMargins(8, 8, 8, 8)

        # ── Sol: Giriş + Kontrol ──
        left_widget = QWidget()
        left_widget.setFixedWidth(290)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(8)
        left_layout.setContentsMargins(0, 0, 0, 0)

        left_layout.addWidget(self._build_input_panel())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }"
                             "QScrollBar:vertical { background: #313244; width: 8px; }"
                             "QScrollBar::handle:vertical { background: #585b70; border-radius: 4px; }")
        self.control_panel = ControlPanel()
        self.control_panel.params_changed.connect(self._on_params_changed)
        scroll.setWidget(self.control_panel)
        left_layout.addWidget(scroll)
        root.addWidget(left_widget)

        # ── Orta: Görüntü Ekranları ──
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setSpacing(8)
        center_layout.setContentsMargins(0, 0, 0, 0)

        img_row = QHBoxLayout()
        original_container = self._make_display_label("Orijinal")
        processed_container = self._make_display_label("İşlenmiş")
        img_row.addWidget(original_container)
        img_row.addWidget(processed_container)
        center_layout.addLayout(img_row, stretch=3)

        # Histogram
        hist_group, hist_layout = self._make_group("RGB Histogram")
        self.histogram = HistogramWidget()
        self.histogram.setMinimumHeight(160)
        hist_layout.addWidget(self.histogram)
        center_layout.addWidget(hist_group, stretch=1)

        # Yoğunluk haritası
        int_group, int_layout = self._make_group("Bölgesel Piksel Yoğunluk Haritası")
        self.intensity_widget = IntensityWidget()
        self.intensity_widget.setMinimumHeight(130)
        int_layout.addWidget(self.intensity_widget)
        center_layout.addWidget(int_group, stretch=1)

        root.addWidget(center_widget, stretch=1)

        # ── Sağ: İstatistikler ──
        right_widget = QWidget()
        right_widget.setFixedWidth(220)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        stats_frame = QFrame()
        stats_frame.setStyleSheet("background: #181825; border-radius: 8px;")
        stats_frame_layout = QVBoxLayout(stats_frame)
        self.stats_panel = StatsPanel()
        stats_frame_layout.addWidget(self.stats_panel)
        right_layout.addWidget(stats_frame)
        right_layout.addStretch()
        root.addWidget(right_widget)

    def _make_group(self, title: str) -> tuple:
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
        """)
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        layout.setContentsMargins(6, 12, 6, 6)
        return group, layout

    def _make_display_label(self, title: str) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)

        title_lbl = QLabel(title)
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet("""
            color: #cdd6f4;
            font-size: 11px;
            font-weight: bold;
            background: #313244;
            border-radius: 4px;
            padding: 3px;
        """)
        layout.addWidget(title_lbl)

        img_lbl = QLabel()
        img_lbl.setAlignment(Qt.AlignCenter)
        img_lbl.setStyleSheet("background: #181825; border-radius: 6px;")
        img_lbl.setMinimumSize(320, 240)
        img_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(img_lbl)

        # Store reference
        if title == "Orijinal":
            self.original_label = img_lbl
        else:
            self.processed_label = img_lbl

        return container

    def _build_input_panel(self) -> QWidget:
        group = QGroupBox("Giriş Kaynağı")
        group.setStyleSheet("""
            QGroupBox {
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
        """)
        layout = QVBoxLayout(group)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 12, 8, 8)

        btn_style = """
            QPushButton {
                background: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 7px 10px;
                font-size: 10px;
                text-align: left;
            }
            QPushButton:hover { background: #45475a; border-color: #cba6f7; }
            QPushButton:pressed { background: #7c3aed; border-color: #cba6f7; }
        """

        webcam_btn = QPushButton("Webcam Başlat / Durdur")
        webcam_btn.setStyleSheet(btn_style)
        webcam_btn.clicked.connect(self._toggle_webcam)
        layout.addWidget(webcam_btn)

        img_btn = QPushButton("Fotoğraf Yükle...")
        img_btn.setStyleSheet(btn_style)
        img_btn.clicked.connect(self._load_image)
        layout.addWidget(img_btn)

        video_btn = QPushButton("Video Yükle...")
        video_btn.setStyleSheet(btn_style)
        video_btn.clicked.connect(self._load_video)
        layout.addWidget(video_btn)

        # Kayıt butonu
        save_btn = QPushButton("İşlenmiş Görüntüyü Kaydet")
        save_btn.setStyleSheet(btn_style.replace("#313244", "#1e3a2f").replace("#45475a", "#2d5a3d"))
        save_btn.clicked.connect(self._save_image)
        layout.addWidget(save_btn)

        self.status_lbl = QLabel("Hazır")
        self.status_lbl.setStyleSheet("color: #a6adc8; font-size: 9px; padding: 2px;")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_lbl)

        return group

    # ── Giriş olayları ──
    def _toggle_webcam(self):
        if self.is_playing and self.cap is not None:
            self.timer.stop()
            self.cap.release()
            self.cap = None
            self.is_playing = False
            self.status_lbl.setText("Webcam durduruldu")
        else:
            self._stop_current()
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                self.status_lbl.setText("Webcam açılamadı! (izin gerekebilir)")
                self.cap = None
                return
            # macOS'ta ilk birkaç frame boş gelebilir, test et
            ret, test_frame = self.cap.read()
            if not ret or test_frame is None:
                self.status_lbl.setText("Webcam erişim izni verilmedi!")
                self.cap.release()
                self.cap = None
                return
            self.is_playing = True
            self.status_lbl.setText("Webcam aktif")
            self.timer.start(33)  # ~30 FPS

    def _load_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Fotoğraf Seç", "",
            "Görüntü Dosyaları (*.png *.jpg *.jpeg *.bmp *.tiff *.webp)"
        )
        if not path:
            return
        self._stop_current()
        frame = cv2.imread(path)
        if frame is None:
            self.status_lbl.setText("Görüntü yüklenemedi!")
            return
        self.current_frame = frame
        self.status_lbl.setText(f"Fotoğraf: {os.path.basename(path)}")
        self._process_and_display()

    def _load_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Video Seç", "",
            "Video Dosyaları (*.mp4 *.avi *.mov *.mkv *.wmv)"
        )
        if not path:
            return
        self._stop_current()
        self.cap = cv2.VideoCapture(path)
        if not self.cap.isOpened():
            self.status_lbl.setText("Video açılamadı!")
            return
        fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
        self.is_playing = True
        self.status_lbl.setText(f"Video: {os.path.basename(path)}")
        self.timer.start(int(1000 / fps))

    def _stop_current(self):
        self.timer.stop()
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.is_playing = False

    def _save_image(self):
        if self.current_frame is None:
            return
        processed = self.processor.process(self.current_frame)
        if processed is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Kaydet", "processed.png",
            "PNG (*.png);;JPEG (*.jpg)"
        )
        if path:
            cv2.imwrite(path, processed)
            self.status_lbl.setText(f"Kaydedildi: {os.path.basename(path)}")

    def _update_frame(self):
        if self.cap is None:
            return
        ret, frame = self.cap.read()
        if not ret or frame is None:
            # Video bitti → başa sar; webcam hatası → yoksay
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            return
        if frame.size == 0:
            return
        self.current_frame = frame
        self._process_and_display()

    def _on_params_changed(self, params: dict):
        self.processor.blur_amount = params['blur']
        self.processor.brightness = params['brightness']
        self.processor.contrast = params['contrast']
        self.processor.sharpen = params['sharpen']
        self.processor.r_gain = params['r_gain']
        self.processor.g_gain = params['g_gain']
        self.processor.b_gain = params['b_gain']
        self.processor.hist_eq = params['hist_eq']
        self.processor.grayscale = params['grayscale']
        self.processor.edge_mode = params['edge_mode']
        self.processor.canny_low = params['canny_low']
        self.processor.canny_high = params['canny_high']
        self.processor.flip_h = params['flip_h']
        self.processor.flip_v = params['flip_v']

        if self.current_frame is not None and not self.is_playing:
            self._process_and_display()

    def _process_and_display(self):
        if self.current_frame is None:
            return

        processed = self.processor.process(self.current_frame)

        self._set_image(self.original_label, self.current_frame)
        self._set_image(self.processed_label, processed)

        # İstatistikler ve grafikleri güncelle (her 3 karede bir)
        self._frame_count = getattr(self, '_frame_count', 0) + 1
        if self._frame_count % 3 == 0 or not self.is_playing:
            stats = self.processor.get_stats(self.current_frame)
            self.stats_panel.update_stats(stats)
            self.histogram.update_histogram(self.current_frame)
            self.intensity_widget.update_intensity(self.current_frame)

    @staticmethod
    def _set_image(label: QLabel, frame: np.ndarray):
        if frame is None:
            return
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        label.setPixmap(
            pixmap.scaled(label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )

    def closeEvent(self, event):
        self._stop_current()
        super().closeEvent(event)


# ─────────────────────────────────────────────
#  Başlat
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Koyu Fusion paleti
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#1e1e2e"))
    palette.setColor(QPalette.WindowText, QColor("#cdd6f4"))
    palette.setColor(QPalette.Base, QColor("#181825"))
    palette.setColor(QPalette.AlternateBase, QColor("#313244"))
    palette.setColor(QPalette.ToolTipBase, QColor("#1e1e2e"))
    palette.setColor(QPalette.ToolTipText, QColor("#cdd6f4"))
    palette.setColor(QPalette.Text, QColor("#cdd6f4"))
    palette.setColor(QPalette.Button, QColor("#313244"))
    palette.setColor(QPalette.ButtonText, QColor("#cdd6f4"))
    palette.setColor(QPalette.Highlight, QColor("#7c3aed"))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
