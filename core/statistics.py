"""
core/statistics.py — Rich image statistics and PDF report export.
No Qt imports allowed here.
"""
from __future__ import annotations

import cv2
import numpy as np
from typing import Optional


class ImageStats:
    """Compute comprehensive statistics for a BGR frame."""

    @staticmethod
    def compute(frame: np.ndarray) -> dict:
        if frame is None or frame.size == 0:
            return {}

        h, w = frame.shape[:2]
        channels = frame.shape[2] if frame.ndim == 3 else 1

        if channels == 3:
            b, g, r = cv2.split(frame)
        else:
            b = g = r = frame

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if channels == 3 else frame

        stats: dict = {
            "width":       w,
            "height":      h,
            "channels":    channels,
            "bit_depth":   frame.dtype.itemsize * 8,
            "r_mean":      float(np.mean(r)),
            "g_mean":      float(np.mean(g)),
            "b_mean":      float(np.mean(b)),
            "r_std":       float(np.std(r)),
            "g_std":       float(np.std(g)),
            "b_std":       float(np.std(b)),
            "min":         int(frame.min()),
            "max":         int(frame.max()),
            "overall_mean":float(np.mean(frame)),
            "overall_std": float(np.std(frame)),
            "entropy":     ImageStats._entropy(gray),
            "snr":         ImageStats._snr(gray),
            "rg_cov":      float(np.cov(r.ravel().astype(float), g.ravel().astype(float))[0, 1]),
            "rb_cov":      float(np.cov(r.ravel().astype(float), b.ravel().astype(float))[0, 1]),
            "regional_var":ImageStats._regional_variance(gray, grid=4),
        }
        return stats

    @staticmethod
    def _entropy(gray: np.ndarray) -> float:
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
        hist /= hist.sum() + 1e-9
        hist = hist[hist > 0]
        return float(-np.sum(hist * np.log2(hist)))

    @staticmethod
    def _snr(gray: np.ndarray) -> float:
        mu = float(np.mean(gray))
        sigma = float(np.std(gray))
        return float(mu / (sigma + 1e-9))

    @staticmethod
    def _regional_variance(gray: np.ndarray, grid: int = 4) -> list[float]:
        h, w = gray.shape
        gh, gw = h // grid, w // grid
        variances = []
        for i in range(grid):
            for j in range(grid):
                region = gray[i * gh:(i + 1) * gh, j * gw:(j + 1) * gw]
                variances.append(float(np.var(region)))
        return variances


class ReportExporter:
    """Export a multi-page PDF analysis report."""

    @staticmethod
    def export_pdf(
        path: str,
        original: Optional[np.ndarray],
        processed: Optional[np.ndarray],
        stats: dict,
        filter_info: dict,
    ) -> bool:
        """
        Generate a PDF report with:
        - Page 1: original vs processed image side by side + active ops
        - Page 2: RGB histograms
        - Page 3: statistics table
        Returns True on success, False on error.
        """
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_pdf import PdfPages

            with PdfPages(path) as pdf:
                # ── Page 1: Images ───────────────────────────────────────────
                fig, axes = plt.subplots(1, 2, figsize=(12, 6), facecolor="#1e1e2e")
                fig.suptitle("Görüntü İşleme Raporu", color="#cdd6f4", fontsize=14, fontweight="bold")
                for ax, img, title in [
                    (axes[0], original, "Orijinal"),
                    (axes[1], processed, "İşlenmiş"),
                ]:
                    if img is not None:
                        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        ax.imshow(rgb)
                    ax.set_title(title, color="#cdd6f4", fontsize=11)
                    ax.axis("off")
                    ax.set_facecolor("#181825")
                fig.text(
                    0.5, 0.02,
                    "Aktif İşlemler: " + ", ".join(filter_info.get("active_ops", [])),
                    ha="center", color="#a6adc8", fontsize=9,
                )
                plt.tight_layout()
                pdf.savefig(fig, facecolor="#1e1e2e")
                plt.close(fig)

                # ── Page 2: Histograms ────────────────────────────────────────
                fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), facecolor="#1e1e2e")
                for ax, img, label in [(ax1, original, "Orijinal"), (ax2, processed, "İşlenmiş")]:
                    if img is not None:
                        b_ch, g_ch, r_ch = cv2.split(img)
                        for ch, col, lbl in [
                            (r_ch, "#f38ba8", "R"),
                            (g_ch, "#a6e3a1", "G"),
                            (b_ch, "#89b4fa", "B"),
                        ]:
                            hist = cv2.calcHist([ch], [0], None, [256], [0, 256]).flatten()
                            ax.plot(hist, color=col, linewidth=0.8, alpha=0.85, label=lbl)
                    ax.set_facecolor("#181825")
                    ax.set_title(f"{label} — RGB Histogram", color="#cdd6f4", fontsize=10)
                    ax.tick_params(colors="#a6adc8", labelsize=7)
                    for sp in ax.spines.values():
                        sp.set_color("#45475a")
                    ax.legend(fontsize=8, facecolor="#313244", labelcolor="#cdd6f4")
                plt.tight_layout()
                pdf.savefig(fig, facecolor="#1e1e2e")
                plt.close(fig)

                # ── Page 3: Statistics table ──────────────────────────────────
                fig, ax = plt.subplots(figsize=(10, 7), facecolor="#1e1e2e")
                ax.axis("off")
                ax.set_facecolor("#1e1e2e")
                rows = [
                    ("Çözünürlük", f"{stats.get('width','?')} × {stats.get('height','?')}"),
                    ("Kanal Sayısı", str(stats.get("channels", "?"))),
                    ("Bit Derinliği", f"{stats.get('bit_depth','?')} bit"),
                    ("R Ortalama / Std", f"{stats.get('r_mean',0):.2f} / {stats.get('r_std',0):.2f}"),
                    ("G Ortalama / Std", f"{stats.get('g_mean',0):.2f} / {stats.get('g_std',0):.2f}"),
                    ("B Ortalama / Std", f"{stats.get('b_mean',0):.2f} / {stats.get('b_std',0):.2f}"),
                    ("Min / Max Piksel", f"{stats.get('min','?')} / {stats.get('max','?')}"),
                    ("Genel Ortalama / Std", f"{stats.get('overall_mean',0):.2f} / {stats.get('overall_std',0):.2f}"),
                    ("Entropi (bit)", f"{stats.get('entropy',0):.4f}"),
                    ("SNR", f"{stats.get('snr',0):.4f}"),
                    ("RG Kovaryans", f"{stats.get('rg_cov',0):.2f}"),
                    ("RB Kovaryans", f"{stats.get('rb_cov',0):.2f}"),
                ]
                table = ax.table(
                    cellText=rows,
                    colLabels=["Özellik", "Değer"],
                    loc="center",
                    cellLoc="left",
                )
                table.auto_set_font_size(False)
                table.set_fontsize(10)
                table.scale(1, 1.8)
                for (r, c), cell in table.get_celld().items():
                    cell.set_facecolor("#313244" if r % 2 == 0 else "#1e1e2e")
                    cell.set_text_props(color="#cdd6f4")
                    cell.set_edgecolor("#45475a")
                ax.set_title("İstatistik Raporu", color="#cdd6f4", fontsize=13, pad=10)
                plt.tight_layout()
                pdf.savefig(fig, facecolor="#1e1e2e")
                plt.close(fig)

            return True
        except Exception as exc:
            print(f"[ReportExporter] PDF error: {exc}")
            return False
