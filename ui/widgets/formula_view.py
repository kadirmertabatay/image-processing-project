"""
ui/widgets/formula_view.py — LaTeX formula panel + kernel heatmap.
Uses matplotlib mathtext (no LaTeX installation required).
Modern glassmorphism design with gradient accents.
"""
from __future__ import annotations

import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
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
        self._last_kernel_id: int | None = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(6)
        root.setContentsMargins(0, 0, 0, 0)

        # ── Header ──
        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
            QFrame {{
                background: {THEME['surface0']};
                border: 1px solid {THEME['surface1']};
                border-radius: 6px;
                padding: 0;
            }}
        """)
        hlay = QVBoxLayout(header_frame)
        hlay.setContentsMargins(10, 6, 10, 6)
        header = QLabel("Matematiksel Model")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet(
            f"color: {THEME['subtext']}; font-weight: 600; font-size: 10px; background: transparent; letter-spacing: 1px;"
        )
        hlay.addWidget(header)
        root.addWidget(header_frame)

        # ── Formula canvas ──
        formula_frame = QFrame()
        formula_frame.setStyleSheet(f"""
            QFrame {{
                background: {THEME['mantle']};
                border: 1px solid {THEME['surface1']};
                border-radius: 8px;
            }}
        """)
        flay = QVBoxLayout(formula_frame)
        flay.setContentsMargins(4, 4, 4, 4)

        self._formula_fig = Figure(figsize=(3.2, 2.0), facecolor=THEME["mantle"])
        self._formula_canvas = FigureCanvas(self._formula_fig)
        self._formula_canvas.setMinimumHeight(140)
        self._formula_canvas.setStyleSheet("border: none; background: transparent;")
        flay.addWidget(self._formula_canvas)
        root.addWidget(formula_frame, stretch=3)

        # ── Kernel heatmap canvas ──
        kernel_frame = QFrame()
        kernel_frame.setStyleSheet(f"""
            QFrame {{
                background: {THEME['mantle']};
                border: 1px solid {THEME['surface1']};
                border-radius: 8px;
            }}
        """)
        klay = QVBoxLayout(kernel_frame)
        klay.setContentsMargins(4, 4, 4, 4)

        self._kernel_fig = Figure(figsize=(3.2, 2.0), facecolor=THEME["mantle"])
        self._kernel_canvas = FigureCanvas(self._kernel_fig)
        self._kernel_canvas.setMinimumHeight(130)
        self._kernel_canvas.setStyleSheet("border: none; background: transparent;")
        klay.addWidget(self._kernel_canvas)
        root.addWidget(kernel_frame, stretch=2)

        # Initial render
        self.update_formula("identity", None)

    # ─── Public API ──────────────────────────────────────────────────────────

    def update_formula(self, formula_key: str, kernel: np.ndarray | None):
        kernel_id = id(kernel) if kernel is not None else None
        if formula_key == self._last_key and kernel_id == self._last_kernel_id:
            return
        self._last_key = formula_key
        self._last_kernel_id = kernel_id
        info = FORMULA_DATA.get(formula_key, FORMULA_DATA["identity"])
        self._render_formula(info)
        self._render_kernel(info, kernel)

    # ─── Rendering ───────────────────────────────────────────────────────────

    def _render_formula(self, info: dict):
        fig = self._formula_fig
        fig.clear()
        fig.set_layout_engine("none")  # disable tight_layout entirely — prevents crash
        ax = fig.add_axes([0.05, 0.05, 0.9, 0.9])
        ax.set_facecolor(THEME["mantle"])
        ax.axis("off")

        latex_lines: list[str] = info.get("latex", [])
        label: str = info.get("label", "")

        n = len(latex_lines)
        y_positions = np.linspace(0.80, 0.12, max(n, 1))

        # Filter name header — with accent underline
        ax.text(0.5, 0.95, label, transform=ax.transAxes,
                ha="center", va="top", fontsize=10,
                color=THEME["mauve"], fontweight="bold",
                fontfamily="sans-serif")
        ax.axhline(y=0.88, xmin=0.1, xmax=0.9,
                   color=THEME["accent"], linewidth=1.5, alpha=0.5)

        for line, y in zip(latex_lines, y_positions):
            try:
                ax.text(0.5, y, line, transform=ax.transAxes,
                        ha="center", va="center", fontsize=9,
                        color=THEME["text"], usetex=False)
            except Exception:
                plain = line.replace("$", "").replace("\\", "")
                ax.text(0.5, y, plain, transform=ax.transAxes,
                        ha="center", va="center", fontsize=8,
                        color=THEME["subtext"])

        self._formula_canvas.draw_idle()

    def _render_kernel(self, info: dict, kernel: np.ndarray | None):
        fig = self._kernel_fig
        fig.clear()
        fig.set_layout_engine("none")

        if kernel is None or kernel.ndim != 2:
            ax = fig.add_axes([0.05, 0.05, 0.9, 0.9])
            ax.set_facecolor(THEME["mantle"])
            ax.axis("off")
            ax.text(0.5, 0.5, "Kernel matrisi yok", transform=ax.transAxes,
                    ha="center", va="center", color=THEME["overlay0"], fontsize=9,
                    fontstyle="italic")
            self._kernel_canvas.draw_idle()
            return

        ax = fig.add_axes([0.08, 0.08, 0.72, 0.82])
        ax.set_facecolor(THEME["mantle"])

        kdata = kernel.astype(float)
        vmax = max(abs(kdata.max()), abs(kdata.min()), 1e-6)
        norm = mcolors.TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)

        im = ax.imshow(kdata, cmap="RdBu_r", norm=norm, aspect="equal")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title("Kernel Matrisi", color=THEME["text"], fontsize=9, pad=4)
        for spine in ax.spines.values():
            spine.set_color(THEME["surface1"])
            spine.set_linewidth(0.5)

        # Annotate cells
        for r in range(kdata.shape[0]):
            for c in range(kdata.shape[1]):
                val = kdata[r, c]
                color = "white" if abs(val) > vmax * 0.4 else THEME["text"]
                fmt = f"{val:.3f}" if abs(val) < 0.1 else f"{val:.2f}"
                ax.text(c, r, fmt, ha="center", va="center",
                        fontsize=7, color=color, fontweight="bold")

        # Colorbar
        cax = fig.add_axes([0.84, 0.12, 0.04, 0.74])
        cbar = fig.colorbar(im, cax=cax)
        cbar.ax.tick_params(colors=THEME["subtext"], labelsize=6)

        self._kernel_canvas.draw_idle()
