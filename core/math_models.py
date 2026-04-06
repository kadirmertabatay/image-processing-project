"""
core/math_models.py — Mathematical tools: kernel generators, FFT, 3D surface data.
No Qt imports allowed here.
"""
from __future__ import annotations

import numpy as np
import cv2


class MathModels:
    """Static collection of mathematical analysis functions."""

    # ─── Kernel generators ───────────────────────────────────────────────────

    @staticmethod
    def gaussian_kernel(k_size: int, sigma: float = 0.0) -> np.ndarray:
        """Return a normalised k_size × k_size Gaussian kernel."""
        if sigma <= 0:
            sigma = 0.3 * ((k_size - 1) * 0.5 - 1) + 0.8  # OpenCV default
        ax = np.linspace(-(k_size // 2), k_size // 2, k_size)
        xx, yy = np.meshgrid(ax, ax)
        kernel = np.exp(-(xx**2 + yy**2) / (2 * sigma**2))
        return kernel / kernel.sum()

    @staticmethod
    def sobel_kernels() -> tuple[np.ndarray, np.ndarray]:
        """Return Sobel Gx and Gy kernels."""
        Gx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
        Gy = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32)
        return Gx, Gy

    @staticmethod
    def laplacian_kernel() -> np.ndarray:
        return np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32)

    @staticmethod
    def sharpen_kernel(strength: float = 1.0) -> np.ndarray:
        s = strength
        return np.array([
            [0, -s, 0],
            [-s, 1 + 4 * s, -s],
            [0, -s, 0]
        ], dtype=np.float32)

    @staticmethod
    def morph_kernel(size: int = 3) -> np.ndarray:
        return np.ones((size, size), dtype=np.float32)

    # ─── FFT analysis ────────────────────────────────────────────────────────

    @staticmethod
    def compute_fft(frame: np.ndarray) -> dict:
        """
        Compute FFT of the grayscale frame.
        Returns dict with:
          magnitude   — log-scaled magnitude spectrum (np.ndarray, uint8)
          power       — power spectrum (np.ndarray, float64)
          low_energy  — fraction of energy in low-freq half
          high_energy — fraction of energy in high-freq half
          radial_profile — 1-D radial power profile (np.ndarray)
        """
        if frame is None:
            return {}
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
        h, w = gray.shape

        f = np.fft.fft2(gray.astype(np.float64))
        fshift = np.fft.fftshift(f)
        power = np.abs(fshift) ** 2

        # log magnitude spectrum for display
        mag = np.log1p(np.abs(fshift))
        mag = (mag / mag.max() * 255).astype(np.uint8)

        # Low / high energy split
        cy, cx = h // 2, w // 2
        r = min(cy, cx) // 2
        mask = np.zeros((h, w), bool)
        Y, X = np.ogrid[:h, :w]
        mask[(X - cx)**2 + (Y - cy)**2 <= r**2] = True
        total = power.sum() + 1e-9
        low_energy  = float(power[mask].sum() / total)
        high_energy = float(power[~mask].sum() / total)

        # Radial power profile
        max_r = min(cy, cx)
        radial = np.zeros(max_r)
        for ri in range(max_r):
            ring = (mask_at := (X - cx)**2 + (Y - cy)**2)
            ring_mask = (ring >= ri**2) & (ring < (ri + 1)**2)
            count = ring_mask.sum()
            radial[ri] = float(power[ring_mask].sum() / (count + 1e-9))

        return {
            "magnitude":    mag,
            "power":        power,
            "low_energy":   low_energy,
            "high_energy":  high_energy,
            "radial_profile": radial,
        }

    # ─── 3-D surface data ────────────────────────────────────────────────────

    @staticmethod
    def compute_surface3d(frame: np.ndarray, target_size: int = 64) -> np.ndarray:
        """
        Downsample frame to target_size × target_size and return
        grey-level intensity as a 2-D float array.
        """
        if frame is None:
            return np.zeros((target_size, target_size))
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
        small = cv2.resize(gray, (target_size, target_size), interpolation=cv2.INTER_AREA)
        return small.astype(np.float64)
