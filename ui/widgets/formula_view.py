"""
ui/widgets/formula_view.py — LaTeX formula panel + kernel heatmap.
Uses matplotlib mathtext (no LaTeX installation required).
"""
from __future__ import annotations

import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt

import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from config import FORMULA_DATA, THEME


class FormulaView(QWidget):
    """
    Two-panel widget:
      • Top half — renders the filter name and LaTeX formula lines
      • Bottom half — kernel heatmap (imshow) with value annotations
    Updates lazily: only redraws when the formula key changes.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._last_key: str | None = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(4)
        root.setContentsMargins(4, 4, 4, 4)

        header = QLabel("Matematiksel Formül Paneli")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet(
            f"color: {THEME['mauve']}; font-weight: bold; font-size: 12px; padding: 4px;"
        )
        root.addWidget(header)

        # Formula canvas
        self._formula_fig = Figure(figsize=(3.5, 2.4), facecolor=THEME["mantle"])
        self._formula_canvas = FigureCanvas(self._formula_fig)
        self._formula_canvas.setMinimumHeight(160)
        root.addWidget(self._formula_canvas)

        # Kernel heatmap canvas
        self._kernel_fig = Figure(figsize=(3.5, 2.2), facecolor=THEME["mantle"])
        self._kernel_canvas = FigureCanvas(self._kernel_fig)
        self._kernel_canvas.setMinimumHeight(140)
        root.addWidget(self._kernel_canvas)

        # Initial "no filter" render
        self.update_formula("identity", None)

    # ─── Public API ──────────────────────────────────────────────────────────

    def update_formula(self, formula_key: str, kernel: np.ndarray | None):
        if formula_key == self._last_key and kernel is None:
            return
        self._last_key = formula_key
        info = FORMULA_DATA.get(formula_key, FORMULA_DATA["identity"])
        self._render_formula(info)
        self._render_kernel(info, kernel)

    # ─── Rendering ───────────────────────────────────────────────────────────

    def _render_formula(self, info: dict):
        fig = self._formula_fig
        fig.clear()
        ax = fig.add_subplot(111)
        ax.set_facecolor(THEME["mantle"])
        ax.axis("off")

        latex_lines: list[str] = info.get("latex", [])
        label: str = info.get("label", "")

        n = len(latex_lines)
        y_positions = np.linspace(0.85, 0.15, max(n, 1))

        # Filter name header
        ax.text(0.5, 0.97, label, transform=ax.transAxes,
                ha="center", va="top", fontsize=10,
                color=THEME["mauve"], fontweight="bold")

        for i, (line, y) in enumerate(zip(latex_lines, y_positions)):
            try:
                ax.text(0.5, y, line, transform=ax.transAxes,
                        ha="center", va="center", fontsize=9,
                        color=THEME["text"],
                        usetex=False)
            except Exception:
                # Fallback: strip dollar signs to plain text
                plain = line.replace("$", "")
                ax.text(0.5, y, plain, transform=ax.transAxes,
                        ha="center", va="center", fontsize=8,
                        color=THEME["subtext"])

        fig.tight_layout(pad=0.5)
        self._formula_canvas.draw_idle()

    def _render_kernel(self, info: dict, kernel: np.ndarray | None):
        fig = self._kernel_fig
        fig.clear()
        ax = fig.add_subplot(111)
        ax.set_facecolor(THEME["mantle"])

        if kernel is None or kernel.ndim != 2:
            ax.axis("off")
            ax.text(0.5, 0.5, "Kernel matrisi yok", transform=ax.transAxes,
                    ha="center", va="center", color=THEME["overlay0"], fontsize=9)
            fig.tight_layout(pad=0.3)
            self._kernel_canvas.draw_idle()
            return

        kdata = kernel.astype(float)
        vmax = max(abs(kdata.max()), abs(kdata.min()), 1e-6)
        norm = mcolors.TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)
        cmap = plt.cm.RdBu_r

        im = ax.imshow(kdata, cmap=cmap, norm=norm)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title("Kernel Matrisi", color=THEME["text"], fontsize=9, pad=4)
        for spine in ax.spines.values():
            spine.set_color(THEME["surface1"])

        # Annotate cells
        for r in range(kdata.shape[0]):
            for c in range(kdata.shape[1]):
                val = kdata[r, c]
                color = "white" if abs(val) < vmax * 0.6 else "black"
                ax.text(c, r, f"{val:.2f}", ha="center", va="center",
                        fontsize=7, color=color)

        cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.ax.tick_params(colors=THEME["subtext"], labelsize=6)

        fig.tight_layout(pad=0.3)
        self._kernel_canvas.draw_idle()
