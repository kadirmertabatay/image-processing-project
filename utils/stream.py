"""
utils/stream.py — QThread-based frame capture and background analysis worker.
"""
from __future__ import annotations

import time
import cv2
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal


class FrameGrabber(QThread):
    """
    Continuously reads frames from webcam or video file.
    For a static image, emits exactly once then stops.

    Signals:
        frame_ready(np.ndarray)  — emitted on each new frame
        error(str)               — emitted on capture failure
        finished()               — emitted when thread stops cleanly
    """

    frame_ready = pyqtSignal(object)   # np.ndarray
    error       = pyqtSignal(str)
    finished    = pyqtSignal()

    def __init__(self, source, target_fps: float = 30.0, parent=None):
        """
        source: int (webcam index), str (video/image path), or np.ndarray (single frame)
        """
        super().__init__(parent)
        self._source    = source
        self._target_fps= target_fps
        self._running   = False

    def run(self):
        self._running = True

        # ── Static numpy frame (image already loaded) ──
        if isinstance(self._source, np.ndarray):
            self.frame_ready.emit(self._source)
            self._running = False
            self.finished.emit()
            return

        # ── Webcam / video ──
        cap = cv2.VideoCapture(self._source)
        if not cap.isOpened():
            self.error.emit(f"Kaynak açılamadı: {self._source}")
            self.finished.emit()
            return

        is_webcam = isinstance(self._source, int)
        fps        = cap.get(cv2.CAP_PROP_FPS) or self._target_fps
        delay      = 1.0 / max(fps, 1.0)

        while self._running:
            t0 = time.perf_counter()
            ret, frame = cap.read()
            if not ret or frame is None:
                if is_webcam:
                    self.error.emit("Webcam bağlantısı kesildi.")
                    break
                else:
                    # Loop video
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue

            if frame.size > 0:
                self.frame_ready.emit(frame)

            elapsed = time.perf_counter() - t0
            remaining = delay - elapsed
            if remaining > 0:
                self.msleep(int(remaining * 1000))

        cap.release()
        self._running = False
        self.finished.emit()

    def stop(self):
        self._running = False
        self.wait(2000)


class AnalysisWorker(QThread):
    """
    Off-thread worker for expensive analysis (FFT, 3D surface, stats).

    Signals:
        result_ready(dict)  — dict may contain: 'fft', 'surface3d', 'stats'
    """

    result_ready = pyqtSignal(dict)

    def __init__(self, frame: np.ndarray, tasks: set[str], parent=None):
        """
        tasks: subset of {'fft', 'surface3d', 'stats'}
        """
        super().__init__(parent)
        self._frame = frame.copy() if frame is not None else None
        self._tasks = tasks

    def run(self):
        if self._frame is None:
            return

        result: dict = {}

        if "fft" in self._tasks:
            from core.math_models import MathModels
            result["fft"] = MathModels.compute_fft(self._frame)

        if "surface3d" in self._tasks:
            from core.math_models import MathModels
            result["surface3d"] = MathModels.compute_surface3d(self._frame)

        if "stats" in self._tasks:
            from core.statistics import ImageStats
            result["stats"] = ImageStats.compute(self._frame)

        self.result_ready.emit(result)
