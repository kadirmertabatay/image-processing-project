"""
ui/widgets/control_panel.py — Tabbed parameter controls with tooltips.
"""
from __future__ import annotations

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
    QCheckBox, QComboBox, QGroupBox, QTabWidget, QPushButton,
)
from PyQt5.QtCore import Qt, pyqtSignal

from config import DEFAULTS, TOOLTIPS, THEME


def _make_group(title: str) -> tuple[QGroupBox, QVBoxLayout]:
    group = QGroupBox(title)
    group.setStyleSheet(f"""
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
    layout = QVBoxLayout(group)
    layout.setSpacing(4)
    layout.setContentsMargins(8, 12, 8, 8)
    return group, layout


def _styled_combo(items: list[str]) -> QComboBox:
    cb = QComboBox()
    cb.addItems(items)
    cb.setStyleSheet(f"""
        QComboBox {{
            background: {THEME['surface0']};
            color: {THEME['text']};
            border: 1px solid {THEME['surface1']};
            border-radius: 4px;
            padding: 2px 6px;
            font-size: 10px;
        }}
        QComboBox::drop-down {{ border: none; width: 16px; }}
        QComboBox QAbstractItemView {{
            background: {THEME['surface0']};
            color: {THEME['text']};
            selection-background-color: {THEME['accent']};
        }}
    """)
    return cb


SLIDER_STYLE = f"""
    QSlider::groove:horizontal {{
        height: 4px;
        background: {THEME['surface1']};
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        background: {THEME['mauve']};
        width: 12px;
        height: 12px;
        margin: -4px 0;
        border-radius: 6px;
    }}
    QSlider::sub-page:horizontal {{
        background: {THEME['accent']};
        border-radius: 2px;
    }}
"""

LABEL_STYLE   = f"color: {THEME['subtext']}; font-size: 10px; min-width: 90px;"
VALUE_STYLE   = f"color: {THEME['mauve']}; font-size: 10px; min-width: 34px;"
CHECK_STYLE   = f"color: {THEME['text']}; font-size: 10px;"


class ControlPanel(QWidget):
    """
    Tabbed control panel. Emits params_changed(dict) on any change.
    """

    params_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._connect_signals()

    # ─── UI construction ─────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(6)
        root.setContentsMargins(4, 4, 4, 4)

        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
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
                padding: 4px 8px;
                font-size: 10px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background: {THEME['mantle']};
                color: {THEME['mauve']};
                font-weight: bold;
            }}
        """)

        tabs.addTab(self._tab_basic(),     "Temel")
        tabs.addTab(self._tab_color(),     "Renk")
        tabs.addTab(self._tab_edge(),      "Kenar")
        tabs.addTab(self._tab_morph(),     "Morfoloji")
        tabs.addTab(self._tab_features(),  "Özellik")

        root.addWidget(tabs)

        reset_btn = QPushButton("↺  Tüm Ayarları Sıfırla")
        reset_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME['surface1']};
                color: {THEME['text']};
                border: none;
                border-radius: 6px;
                padding: 7px;
                font-size: 10px;
            }}
            QPushButton:hover   {{ background: {THEME['surface2']}; }}
            QPushButton:pressed {{ background: {THEME['surface0']}; }}
        """)
        reset_btn.clicked.connect(self.reset_all)
        root.addWidget(reset_btn)

    # ── Tab: Basic ────────────────────────────────────────────────────────────

    def _tab_basic(self) -> QWidget:
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setSpacing(6)
        vbox.setContentsMargins(6, 6, 6, 6)

        grp, lay = _make_group("Uzamsal Filtreler")
        self.blur_slider       = self._slider("Blur:", 0, 20, DEFAULTS["blur"], lay, "blur")
        self.sharpen_slider    = self._slider("Keskinlik:", 0, 20, DEFAULTS["sharpen"], lay, "sharpen")
        vbox.addWidget(grp)

        grp2, lay2 = _make_group("Piksel Dönüşümleri")
        self.brightness_slider = self._slider("Parlaklık:", -100, 100, DEFAULTS["brightness"], lay2, "brightness")
        self.contrast_slider   = self._slider("Kontrast:", 50, 250, DEFAULTS["contrast"], lay2, "contrast")

        self.clahe_cb = QCheckBox("CLAHE (Adaptif Histogram Eşitleme)")
        self.clahe_cb.setStyleSheet(CHECK_STYLE)
        self.clahe_cb.setToolTip(TOOLTIPS.get("clahe", ""))
        lay2.addWidget(self.clahe_cb)

        self.grayscale_cb = QCheckBox("Gri Tonlama")
        self.grayscale_cb.setStyleSheet(CHECK_STYLE)
        self.grayscale_cb.setToolTip(TOOLTIPS.get("grayscale", ""))
        lay2.addWidget(self.grayscale_cb)

        flip_row = QHBoxLayout()
        self.flip_h_cb = QCheckBox("Yatay Çevir")
        self.flip_h_cb.setStyleSheet(CHECK_STYLE)
        self.flip_v_cb = QCheckBox("Dikey Çevir")
        self.flip_v_cb.setStyleSheet(CHECK_STYLE)
        flip_row.addWidget(self.flip_h_cb)
        flip_row.addWidget(self.flip_v_cb)
        lay2.addLayout(flip_row)
        vbox.addWidget(grp2)
        vbox.addStretch()
        return w

    # ── Tab: Color ────────────────────────────────────────────────────────────

    def _tab_color(self) -> QWidget:
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setSpacing(6)
        vbox.setContentsMargins(6, 6, 6, 6)

        grp, lay = _make_group("RGB Kanal Kazancı")
        self.r_slider = self._slider("R Kanalı:", 0, 200, DEFAULTS["r_gain"], lay, "r_gain")
        self.g_slider = self._slider("G Kanalı:", 0, 200, DEFAULTS["g_gain"], lay, "g_gain")
        self.b_slider = self._slider("B Kanalı:", 0, 200, DEFAULTS["b_gain"], lay, "b_gain")
        vbox.addWidget(grp)

        grp2, lay2 = _make_group("Renk Uzayı Görüntüleme")
        row = QHBoxLayout()
        lbl = QLabel("Renk Uzayı:")
        lbl.setStyleSheet(LABEL_STYLE)
        self.color_space_combo = _styled_combo(["BGR", "HSV", "LAB", "YCrCb", "GRAY"])
        row.addWidget(lbl)
        row.addWidget(self.color_space_combo, 1)
        lay2.addLayout(row)
        vbox.addWidget(grp2)
        vbox.addStretch()
        return w

    # ── Tab: Edge ─────────────────────────────────────────────────────────────

    def _tab_edge(self) -> QWidget:
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setSpacing(6)
        vbox.setContentsMargins(6, 6, 6, 6)

        grp, lay = _make_group("Kenar Tespiti")
        row = QHBoxLayout()
        lbl = QLabel("Yöntem:")
        lbl.setStyleSheet(LABEL_STYLE)
        self.edge_combo = _styled_combo(["Yok", "Canny", "Sobel", "Laplacian"])
        row.addWidget(lbl)
        row.addWidget(self.edge_combo, 1)
        lay.addLayout(row)

        self.canny_low_slider  = self._slider("Canny Alt:", 0, 255, DEFAULTS["canny_low"],  lay, "canny_low")
        self.canny_high_slider = self._slider("Canny Üst:", 0, 255, DEFAULTS["canny_high"], lay, "canny_high")
        vbox.addWidget(grp)
        vbox.addStretch()
        return w

    # ── Tab: Morphology ───────────────────────────────────────────────────────

    def _tab_morph(self) -> QWidget:
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setSpacing(6)
        vbox.setContentsMargins(6, 6, 6, 6)

        grp, lay = _make_group("Morfolojik İşlemler")
        row = QHBoxLayout()
        lbl = QLabel("İşlem:")
        lbl.setStyleSheet(LABEL_STYLE)
        self.morph_combo = _styled_combo(["Yok", "Erozyon", "Genişletme", "Açma", "Kapama"])
        self.morph_combo.setToolTip(TOOLTIPS.get("morph_op", ""))
        row.addWidget(lbl)
        row.addWidget(self.morph_combo, 1)
        lay.addLayout(row)

        self.morph_kernel_slider = self._slider("Kernel Boyutu:", 3, 21, DEFAULTS["morph_kernel"], lay, "morph_kernel")
        self.morph_kernel_slider.setToolTip(TOOLTIPS.get("morph_kernel", ""))
        vbox.addWidget(grp)

        grp2, lay2 = _make_group("Eşikleme")
        row2 = QHBoxLayout()
        lbl2 = QLabel("Yöntem:")
        lbl2.setStyleSheet(LABEL_STYLE)
        self.thresh_combo = _styled_combo(["Yok", "Binary", "Adaptif", "Otsu"])
        row2.addWidget(lbl2)
        row2.addWidget(self.thresh_combo, 1)
        lay2.addLayout(row2)

        self.thresh_value_slider = self._slider("Eşik Değeri:", 0, 255, DEFAULTS["thresh_value"], lay2, "thresh_value")
        self.thresh_value_slider.setToolTip(TOOLTIPS.get("thresh_value", ""))
        vbox.addWidget(grp2)
        vbox.addStretch()
        return w

    # ── Tab: Features ─────────────────────────────────────────────────────────

    def _tab_features(self) -> QWidget:
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setSpacing(6)
        vbox.setContentsMargins(6, 6, 6, 6)

        grp, lay = _make_group("Özellik Tespiti")
        self.face_detect_cb = QCheckBox("Yüz Tespiti (Haar Cascade)")
        self.face_detect_cb.setStyleSheet(CHECK_STYLE)
        self.face_detect_cb.setToolTip(TOOLTIPS.get("face_detect", ""))
        lay.addWidget(self.face_detect_cb)

        self.contour_detect_cb = QCheckBox("Kontur Tespiti")
        self.contour_detect_cb.setStyleSheet(CHECK_STYLE)
        self.contour_detect_cb.setToolTip(TOOLTIPS.get("contour", ""))
        lay.addWidget(self.contour_detect_cb)

        self.hough_lines_cb = QCheckBox("Hough Doğruları")
        self.hough_lines_cb.setStyleSheet(CHECK_STYLE)
        lay.addWidget(self.hough_lines_cb)

        self.hough_thresh_slider = self._slider("Hough Eşiği:", 20, 300, DEFAULTS["hough_thresh"], lay, "hough_thresh")
        self.hough_thresh_slider.setToolTip(TOOLTIPS.get("hough_thresh", ""))
        vbox.addWidget(grp)
        vbox.addStretch()
        return w

    # ─── Slider factory ──────────────────────────────────────────────────────

    def _slider(self, label: str, min_v: int, max_v: int, default: int,
                layout: QVBoxLayout, tooltip_key: str = "") -> QSlider:
        row = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setStyleSheet(LABEL_STYLE)
        val_lbl = QLabel(str(default))
        val_lbl.setStyleSheet(VALUE_STYLE)
        val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        sl = QSlider(Qt.Horizontal)
        sl.setMinimum(min_v)
        sl.setMaximum(max_v)
        sl.setValue(default)
        sl.setStyleSheet(SLIDER_STYLE)
        if tooltip_key:
            sl.setToolTip(TOOLTIPS.get(tooltip_key, ""))
            lbl.setToolTip(TOOLTIPS.get(tooltip_key, ""))
        sl.valueChanged.connect(lambda v: val_lbl.setText(str(v)))

        row.addWidget(lbl)
        row.addWidget(sl)
        row.addWidget(val_lbl)
        layout.addLayout(row)
        return sl

    # ─── Signal wiring ───────────────────────────────────────────────────────

    def _connect_signals(self):
        sliders = [
            self.blur_slider, self.sharpen_slider,
            self.brightness_slider, self.contrast_slider,
            self.r_slider, self.g_slider, self.b_slider,
            self.canny_low_slider, self.canny_high_slider,
            self.morph_kernel_slider, self.thresh_value_slider,
            self.hough_thresh_slider,
        ]
        for sl in sliders:
            sl.valueChanged.connect(self._emit)

        checkboxes = [
            self.clahe_cb, self.grayscale_cb,
            self.flip_h_cb, self.flip_v_cb,
            self.face_detect_cb, self.contour_detect_cb, self.hough_lines_cb,
        ]
        for cb in checkboxes:
            cb.stateChanged.connect(self._emit)

        combos = [
            self.edge_combo, self.morph_combo,
            self.thresh_combo, self.color_space_combo,
        ]
        for combo in combos:
            combo.currentIndexChanged.connect(self._emit)

    def _emit(self, *_):
        edge_map  = {0: "none", 1: "canny", 2: "sobel", 3: "laplacian"}
        morph_map = {0: "none", 1: "erode", 2: "dilate", 3: "open", 4: "close"}
        thresh_map= {0: "none", 1: "binary", 2: "adaptive", 3: "otsu"}

        self.params_changed.emit({
            "blur_amount":    self.blur_slider.value(),
            "brightness":     self.brightness_slider.value(),
            "contrast":       self.contrast_slider.value() / 100.0,
            "sharpen":        self.sharpen_slider.value(),
            "r_gain":         self.r_slider.value() / 100.0,
            "g_gain":         self.g_slider.value() / 100.0,
            "b_gain":         self.b_slider.value() / 100.0,
            "clahe":          self.clahe_cb.isChecked(),
            "grayscale":      self.grayscale_cb.isChecked(),
            "edge_mode":      edge_map[self.edge_combo.currentIndex()],
            "canny_low":      self.canny_low_slider.value(),
            "canny_high":     self.canny_high_slider.value(),
            "morph_op":       morph_map[self.morph_combo.currentIndex()],
            "morph_kernel":   self.morph_kernel_slider.value(),
            "thresh_mode":    thresh_map[self.thresh_combo.currentIndex()],
            "thresh_value":   self.thresh_value_slider.value(),
            "face_detect":    self.face_detect_cb.isChecked(),
            "contour_detect": self.contour_detect_cb.isChecked(),
            "hough_lines":    self.hough_lines_cb.isChecked(),
            "hough_thresh":   self.hough_thresh_slider.value(),
            "color_space":    self.color_space_combo.currentText(),
            "flip_h":         self.flip_h_cb.isChecked(),
            "flip_v":         self.flip_v_cb.isChecked(),
        })

    # ─── Reset ───────────────────────────────────────────────────────────────

    def reset_all(self):
        d = DEFAULTS
        self.blur_slider.setValue(d["blur"])
        self.sharpen_slider.setValue(d["sharpen"])
        self.brightness_slider.setValue(d["brightness"])
        self.contrast_slider.setValue(d["contrast"])
        self.r_slider.setValue(d["r_gain"])
        self.g_slider.setValue(d["g_gain"])
        self.b_slider.setValue(d["b_gain"])
        self.clahe_cb.setChecked(d["clahe"])
        self.grayscale_cb.setChecked(d["grayscale"])
        self.flip_h_cb.setChecked(d["flip_h"])
        self.flip_v_cb.setChecked(d["flip_v"])
        self.edge_combo.setCurrentIndex(0)
        self.canny_low_slider.setValue(d["canny_low"])
        self.canny_high_slider.setValue(d["canny_high"])
        self.morph_combo.setCurrentIndex(0)
        self.morph_kernel_slider.setValue(d["morph_kernel"])
        self.thresh_combo.setCurrentIndex(0)
        self.thresh_value_slider.setValue(d["thresh_value"])
        self.face_detect_cb.setChecked(d["face_detect"])
        self.contour_detect_cb.setChecked(d["contour_detect"])
        self.hough_lines_cb.setChecked(d["hough_lines"])
        self.hough_thresh_slider.setValue(d["hough_thresh"])
        self.color_space_combo.setCurrentIndex(0)
