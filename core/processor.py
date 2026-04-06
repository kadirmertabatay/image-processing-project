"""
core/processor.py — Image processing pipeline (MVC Model layer).

All heavy OpenCV operations live here; no Qt imports allowed.
"""
from __future__ import annotations

import cv2
import numpy as np
from dataclasses import dataclass, field
from typing import Optional
import os

from config import FORMULA_DATA, DEFAULTS


@dataclass
class ProcessResult:
    """Returned by ImageProcessor.process()."""
    frame: np.ndarray                      # processed BGR image
    formula_key: str = "identity"          # key into FORMULA_DATA
    kernel: Optional[np.ndarray] = None    # active kernel matrix (if any)
    active_ops: list[str] = field(default_factory=list)  # human-readable op list


class ImageProcessor:
    """
    Stateless-ish processor: hold parameters as attributes, call process().
    """

    # Haar cascade — loaded lazily per process call
    _face_cascade: Optional[cv2.CascadeClassifier] = None

    def __init__(self):
        self.reset_params()

    def reset_params(self):
        d = DEFAULTS
        self.blur_amount   = d["blur"]
        self.brightness    = d["brightness"]
        self.contrast      = d["contrast"] / 100.0
        self.sharpen       = d["sharpen"]
        self.r_gain        = d["r_gain"]   / 100.0
        self.g_gain        = d["g_gain"]   / 100.0
        self.b_gain        = d["b_gain"]   / 100.0
        self.clahe         = d["clahe"]
        self.grayscale     = d["grayscale"]
        self.edge_mode     = d["edge_mode"]
        self.canny_low     = d["canny_low"]
        self.canny_high    = d["canny_high"]
        self.morph_op      = d["morph_op"]
        self.morph_kernel  = d["morph_kernel"]
        self.thresh_mode   = d["thresh_mode"]
        self.thresh_value  = d["thresh_value"]
        self.face_detect   = d["face_detect"]
        self.contour_detect= d["contour_detect"]
        self.hough_lines   = d["hough_lines"]
        self.hough_thresh  = d["hough_thresh"]
        self.color_space   = d["color_space"]
        self.flip_h        = d["flip_h"]
        self.flip_v        = d["flip_v"]

    def update_params(self, params: dict):
        """Apply a partial params dict (from UI signal)."""
        for k, v in params.items():
            if hasattr(self, k):
                setattr(self, k, v)

    # ─── Main pipeline ───────────────────────────────────────────────────────

    def process(self, frame: np.ndarray) -> ProcessResult:
        if frame is None or frame.size == 0:
            return ProcessResult(frame=frame)

        img = frame.copy()
        active_ops: list[str] = []
        formula_key = "identity"
        kernel_arr: Optional[np.ndarray] = None

        # 1. Grayscale
        if self.grayscale:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            img = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            formula_key = "grayscale"
            active_ops.append("Gri Tonlama")

        # 2. Channel gain
        if self.r_gain != 1.0 or self.g_gain != 1.0 or self.b_gain != 1.0:
            b, g, r = cv2.split(img.astype(np.float32))
            b = np.clip(b * self.b_gain, 0, 255)
            g = np.clip(g * self.g_gain, 0, 255)
            r = np.clip(r * self.r_gain, 0, 255)
            img = cv2.merge([b, g, r]).astype(np.uint8)
            active_ops.append("RGB Kanal Ayarı")

        # 3. CLAHE
        if self.clahe:
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l, a, b_ch = cv2.split(lab)
            clahe_obj = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe_obj.apply(l)
            lab = cv2.merge([l, a, b_ch])
            img = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            formula_key = "clahe"
            active_ops.append("CLAHE")

        # 4. Brightness / Contrast
        if self.brightness != 0 or abs(self.contrast - 1.0) > 0.01:
            img = cv2.convertScaleAbs(img, alpha=self.contrast, beta=self.brightness)
            active_ops.append(f"Parlaklık/Kontrast (α={self.contrast:.2f}, β={self.brightness})")

        # 5. Sharpen
        if self.sharpen > 0:
            strength = self.sharpen / 10.0
            k = np.array([
                [0, -strength, 0],
                [-strength, 1 + 4 * strength, -strength],
                [0, -strength, 0]
            ], dtype=np.float32)
            img = cv2.filter2D(img, -1, k)
            img = np.clip(img, 0, 255).astype(np.uint8)
            kernel_arr = k
            formula_key = "sharpen"
            active_ops.append("Keskinleştirme")

        # 6. Gaussian Blur
        if self.blur_amount > 0:
            k_size = self.blur_amount * 2 + 1
            img = cv2.GaussianBlur(img, (k_size, k_size), 0)
            from core.math_models import MathModels
            kernel_arr = MathModels.gaussian_kernel(k_size)
            formula_key = "blur"
            active_ops.append(f"Gaussian Blur (k={k_size})")

        # 7. Morphological operations
        if self.morph_op != "none":
            ks = max(3, self.morph_kernel | 1)  # ensure odd
            struct = cv2.getStructuringElement(cv2.MORPH_RECT, (ks, ks))
            kernel_arr = struct.astype(np.float32)
            op_map = {
                "erode":  (cv2.MORPH_ERODE,  "erode"),
                "dilate": (cv2.MORPH_DILATE, "dilate"),
                "open":   (cv2.MORPH_OPEN,   "open"),
                "close":  (cv2.MORPH_CLOSE,  "close"),
            }
            cv_op, fkey = op_map.get(self.morph_op, (cv2.MORPH_ERODE, "erode"))
            img = cv2.morphologyEx(img, cv_op, struct)
            formula_key = fkey
            active_ops.append(f"Morfoloji: {self.morph_op}")

        # 8. Thresholding
        if self.thresh_mode != "none":
            gray_t = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            if self.thresh_mode == "binary":
                _, thresh = cv2.threshold(gray_t, self.thresh_value, 255, cv2.THRESH_BINARY)
                formula_key = "thresh_binary"
            elif self.thresh_mode == "otsu":
                _, thresh = cv2.threshold(gray_t, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                formula_key = "thresh_otsu"
            elif self.thresh_mode == "adaptive":
                thresh = cv2.adaptiveThreshold(
                    gray_t, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY, 11, 2
                )
                formula_key = "thresh_adaptive"
            else:
                thresh = gray_t
            img = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
            active_ops.append(f"Eşikleme: {self.thresh_mode}")

        # 9. Edge detection
        if self.edge_mode != "none":
            img, formula_key, kernel_arr = self._apply_edge(img, kernel_arr)
            active_ops.append(f"Kenar: {self.edge_mode}")

        # 10. Feature detection overlays (on top of processed img)
        if self.face_detect:
            img = self._detect_faces(img)
            active_ops.append("Yüz Tespiti")

        if self.contour_detect:
            img = self._detect_contours(img)
            active_ops.append("Kontur Tespiti")

        if self.hough_lines:
            img = self._detect_hough_lines(img)
            active_ops.append("Hough Doğruları")

        # 11. Color space conversion (visualization; convert back to BGR for display)
        if self.color_space != "BGR":
            img = self._convert_color_space(img, self.color_space)
            active_ops.append(f"Renk Uzayı: {self.color_space}")

        # 12. Flip
        if self.flip_h:
            img = cv2.flip(img, 1)
        if self.flip_v:
            img = cv2.flip(img, 0)

        return ProcessResult(
            frame=img,
            formula_key=formula_key,
            kernel=kernel_arr,
            active_ops=active_ops,
        )

    # ─── Edge detection helpers ──────────────────────────────────────────────

    def _apply_edge(self, img, prev_kernel):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        kernel_arr = prev_kernel

        if self.edge_mode == "canny":
            edges = cv2.Canny(gray, self.canny_low, self.canny_high)
            img = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            return img, "canny", None

        elif self.edge_mode == "sobel":
            from core.math_models import MathModels
            sx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            mag = np.sqrt(sx**2 + sy**2)
            mag = np.clip(mag / (mag.max() + 1e-6) * 255, 0, 255).astype(np.uint8)
            img = cv2.cvtColor(mag, cv2.COLOR_GRAY2BGR)
            kx, _ = MathModels.sobel_kernels()
            return img, "sobel", kx.astype(np.float32)

        elif self.edge_mode == "laplacian":
            from core.math_models import MathModels
            lap = cv2.Laplacian(gray, cv2.CV_64F)
            lap = np.clip(np.abs(lap) / (np.abs(lap).max() + 1e-6) * 255, 0, 255).astype(np.uint8)
            img = cv2.cvtColor(lap, cv2.COLOR_GRAY2BGR)
            return img, "laplacian", MathModels.laplacian_kernel().astype(np.float32)

        return img, "identity", kernel_arr

    # ─── Feature detection helpers ───────────────────────────────────────────

    @classmethod
    def _get_face_cascade(cls) -> Optional[cv2.CascadeClassifier]:
        if cls._face_cascade is None:
            xml_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            if os.path.exists(xml_path):
                cls._face_cascade = cv2.CascadeClassifier(xml_path)
        return cls._face_cascade

    def _detect_faces(self, img: np.ndarray) -> np.ndarray:
        cascade = self._get_face_cascade()
        if cascade is None:
            return img
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        out = img.copy()
        for (x, y, w, h) in faces:
            cv2.rectangle(out, (x, y), (x + w, y + h), (0, 255, 100), 2)
            cv2.putText(out, "Yuz", (x, y - 8), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (0, 255, 100), 1, cv2.LINE_AA)
        return out

    def _detect_contours(self, img: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        out = img.copy()
        cv2.drawContours(out, contours, -1, (180, 100, 255), 1)
        return out

    def _detect_hough_lines(self, img: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLines(edges, 1, np.pi / 180, self.hough_thresh)
        out = img.copy()
        if lines is not None:
            for rho, theta in lines[:, 0]:
                a, b = np.cos(theta), np.sin(theta)
                x0, y0 = a * rho, b * rho
                pt1 = (int(x0 + 1000 * (-b)), int(y0 + 1000 * a))
                pt2 = (int(x0 - 1000 * (-b)), int(y0 - 1000 * a))
                cv2.line(out, pt1, pt2, (250, 200, 50), 1, cv2.LINE_AA)
        return out

    def _convert_color_space(self, img: np.ndarray, space: str) -> np.ndarray:
        """Convert to requested color space and reconstruct pseudo-BGR for display."""
        cs_map = {
            "HSV":   (cv2.COLOR_BGR2HSV,   cv2.COLOR_HSV2BGR),
            "LAB":   (cv2.COLOR_BGR2LAB,   cv2.COLOR_LAB2BGR),
            "YCrCb": (cv2.COLOR_BGR2YCrCb, cv2.COLOR_YCrCb2BGR),
            "GRAY":  (cv2.COLOR_BGR2GRAY,  None),
        }
        if space not in cs_map:
            return img
        fwd, _ = cs_map[space]
        converted = cv2.cvtColor(img, fwd)
        # show the raw converted channels as BGR (visual inspection)
        if len(converted.shape) == 2:
            return cv2.cvtColor(converted, cv2.COLOR_GRAY2BGR)
        return converted  # already 3-ch, treat channels as BGR for display
