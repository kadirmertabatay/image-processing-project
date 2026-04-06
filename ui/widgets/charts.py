"""
ui/widgets/charts.py — Matplotlib-embedded visualization widgets.

Widgets:
  HistogramWidget  — RGB histograms + CDF (updates every N frames)
  Surface3DWidget  — 3-D intensity surface plot (on-demand)
  FFTWidget        — Magnitude spectrum + radial power profile (on-demand)
  ColorSpaceWidget — Decomposed channel views (HSV / LAB / YCrCb)
"""
from __future__ import annotations

import numpy as np
import cv2
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt

import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from config import THEME


def _style_ax(ax, xlabel: str = "", ylabel: str = ""):
    ax.set_facecolor(THEME["mantle"])
    ax.tick_params(colors=THEME["subtext"], labelsize=7)
    for sp in ax.spines.values():
        sp.set_color(THEME["surface1"])
    if xlabel:
        ax.set_xlabel(xlabel, color=THEME["subtext"], fontsize=7)
    if ylabel:
        ax.set_ylabel(ylabel, color=THEME["subtext"], fontsize=7)


# ─── Histogram Widget ─────────────────────────────────────────────────────────

class HistogramWidget(FigureCanvas):
    """RGB channel histograms + cumulative distribution."""

    def __init__(self, parent=None):
        self.fig = Figure(figsize=(5, 2.6), facecolor=THEME["base"])
        super().__init__(self.fig)
        self.setParent(parent)
        self.ax_hist, self.ax_cdf = self.fig.subplots(1, 2)
        self._initialise()
        self.fig.tight_layout(pad=1.0)

    def _initialise(self):
        for ax in (self.ax_hist, self.ax_cdf):
            _style_ax(ax)
        self.ax_hist.set_title("RGB Histogram", color=THEME["text"], fontsize=8)
        self.ax_cdf.set_title("CDF", color=THEME["text"], fontsize=8)

    def update_frame(self, frame: np.ndarray):
        if frame is None:
            return
        self.ax_hist.clear()
        self.ax_cdf.clear()
        _style_ax(self.ax_hist, "Yoğunluk", "Frekans")
        _style_ax(self.ax_cdf, "Yoğunluk", "Kümülâtif")

        channels = cv2.split(frame)  # B, G, R
        colors   = [THEME["blue"], THEME["green"], THEME["red"]]
        labels   = ["B", "G", "R"]

        for ch, col, lbl in zip(channels, colors, labels):
            hist = cv2.calcHist([ch], [0], None, [256], [0, 256]).flatten()
            self.ax_hist.plot(hist, color=col, linewidth=0.8, alpha=0.85, label=lbl)
            cdf = hist.cumsum()
            cdf = cdf / (cdf[-1] + 1e-9)
            self.ax_cdf.plot(cdf, color=col, linewidth=0.8, alpha=0.85, label=lbl)

        self.ax_hist.legend(loc="upper right", fontsize=6,
                            facecolor=THEME["surface0"], labelcolor=THEME["text"])
        self.ax_hist.set_xlim([0, 255])
        self.ax_cdf.set_xlim([0, 255])
        self.ax_cdf.set_ylim([0, 1])
        self.fig.tight_layout(pad=1.0)
        self.draw_idle()


# ─── 3-D Surface Widget ───────────────────────────────────────────────────────

class Surface3DWidget(FigureCanvas):
    """On-demand 3-D intensity surface plot."""

    def __init__(self, parent=None):
        self.fig = Figure(figsize=(5, 3.5), facecolor=THEME["base"])
        super().__init__(self.fig)
        self.setParent(parent)
        self._show_placeholder()

    def _show_placeholder(self):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor(THEME["mantle"])
        ax.axis("off")
        ax.text(0.5, 0.5, "▶  Derin Analiz çalıştırın",
                transform=ax.transAxes, ha="center", va="center",
                color=THEME["overlay0"], fontsize=11)
        self.fig.tight_layout(pad=0.5)
        self.draw_idle()

    def update_surface(self, z: np.ndarray):
        """z — 2-D float array from MathModels.compute_surface3d()"""
        if z is None or z.ndim != 2:
            return
        self.fig.clear()
        ax = self.fig.add_subplot(111, projection="3d")
        ax.set_facecolor(THEME["mantle"])
        ax.xaxis.pane.fill = False
        ax.yaxis.pane.fill = False
        ax.zaxis.pane.fill = False

        xs = np.arange(z.shape[1])
        ys = np.arange(z.shape[0])
        X, Y = np.meshgrid(xs, ys)
        surf = ax.plot_surface(X, Y, z, cmap="plasma", linewidth=0, antialiased=True, alpha=0.9)

        ax.set_xlabel("X", color=THEME["subtext"], fontsize=7, labelpad=2)
        ax.set_ylabel("Y", color=THEME["subtext"], fontsize=7, labelpad=2)
        ax.set_zlabel("Yoğunluk", color=THEME["subtext"], fontsize=7, labelpad=2)
        ax.tick_params(colors=THEME["subtext"], labelsize=6)
        ax.set_title("3-D Yoğunluk Yüzeyi", color=THEME["text"], fontsize=9)

        cbar = self.fig.colorbar(surf, ax=ax, shrink=0.5, pad=0.08)
        cbar.ax.tick_params(colors=THEME["subtext"], labelsize=6)

        self.fig.tight_layout(pad=0.5)
        self.draw_idle()


# ─── FFT Widget ───────────────────────────────────────────────────────────────

class FFTWidget(FigureCanvas):
    """On-demand FFT magnitude + radial power profile."""

    def __init__(self, parent=None):
        self.fig = Figure(figsize=(5, 3.0), facecolor=THEME["base"])
        super().__init__(self.fig)
        self.setParent(parent)
        self._show_placeholder()

    def _show_placeholder(self):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor(THEME["mantle"])
        ax.axis("off")
        ax.text(0.5, 0.5, "▶  Derin Analiz çalıştırın",
                transform=ax.transAxes, ha="center", va="center",
                color=THEME["overlay0"], fontsize=11)
        self.fig.tight_layout(pad=0.5)
        self.draw_idle()

    def update_fft(self, fft_data: dict):
        if not fft_data:
            return
        self.fig.clear()
        ax1, ax2 = self.fig.subplots(1, 2)

        # Magnitude spectrum
        mag = fft_data.get("magnitude")
        if mag is not None:
            ax1.imshow(mag, cmap="inferno")
            ax1.set_title("Frekans Spektrumu (log)", color=THEME["text"], fontsize=8)
            ax1.axis("off")

        # Radial power profile
        radial = fft_data.get("radial_profile")
        if radial is not None:
            _style_ax(ax2, "Radyal Mesafe (px)", "Güç")
            ax2.plot(radial, color=THEME["mauve"], linewidth=0.9)
            ax2.set_title("Radyal Güç Profili", color=THEME["text"], fontsize=8)
            lo = fft_data.get("low_energy", 0)
            hi = fft_data.get("high_energy", 0)
            ax2.text(0.97, 0.95, f"Düşük: {lo:.1%}\nYüksek: {hi:.1%}",
                     transform=ax2.transAxes, ha="right", va="top",
                     fontsize=7, color=THEME["subtext"])

        self.fig.tight_layout(pad=1.0)
        self.draw_idle()


# ─── Color Space Widget ───────────────────────────────────────────────────────

class ColorSpaceWidget(FigureCanvas):
    """Decompose a frame into 3 channels of the selected color space."""

    SPACE_CONFIGS = {
        "HSV":   (cv2.COLOR_BGR2HSV,   ["H (Ton)",  "S (Doygunluk)", "V (Parlaklık)"]),
        "LAB":   (cv2.COLOR_BGR2LAB,   ["L (Açıklık)","A (Yeşil-Kırmızı)","B (Mavi-Sarı)"]),
        "YCrCb": (cv2.COLOR_BGR2YCrCb, ["Y (Parlaklık)","Cr (Kırmızı Fark)","Cb (Mavi Fark)"]),
        "GRAY":  (None,                ["Gri"]),
    }

    def __init__(self, parent=None):
        self.fig = Figure(figsize=(5, 3.0), facecolor=THEME["base"])
        super().__init__(self.fig)
        self.setParent(parent)
        self._show_placeholder()

    def _show_placeholder(self):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor(THEME["mantle"])
        ax.axis("off")
        ax.text(0.5, 0.5, "Sol panelden renk uzayı seçin",
                transform=ax.transAxes, ha="center", va="center",
                color=THEME["overlay0"], fontsize=11)
        self.fig.tight_layout(pad=0.5)
        self.draw_idle()

    def update_frame(self, frame: np.ndarray, space: str = "HSV"):
        if frame is None or space == "BGR":
            self._show_placeholder()
            return

        cfg = self.SPACE_CONFIGS.get(space)
        if cfg is None:
            return

        conv_code, ch_names = cfg

        if space == "GRAY":
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            channels = [gray]
        else:
            converted = cv2.cvtColor(frame, conv_code)
            channels = cv2.split(converted)

        self.fig.clear()
        n = len(channels)
        axes = self.fig.subplots(1, n)
        if n == 1:
            axes = [axes]

        for ax, ch, name in zip(axes, channels, ch_names):
            ax.imshow(ch, cmap="gray")
            ax.set_title(name, color=THEME["text"], fontsize=7)
            ax.axis("off")

        self.fig.suptitle(f"Renk Uzayı: {space}", color=THEME["mauve"],
                          fontsize=9, fontweight="bold")
        self.fig.tight_layout(pad=0.8)
        self.draw_idle()
