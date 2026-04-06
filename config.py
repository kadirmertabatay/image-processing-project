"""
config.py — Global theme, constants, formula metadata, and tooltip strings.
"""
from __future__ import annotations

# ─── Catppuccin Mocha Palette ─────────────────────────────────────────────────
THEME = {
    "base":    "#1e1e2e",
    "mantle":  "#181825",
    "crust":   "#11111b",
    "surface0":"#313244",
    "surface1":"#45475a",
    "surface2":"#585b70",
    "overlay0":"#6c7086",
    "overlay1":"#7f849c",
    "text":    "#cdd6f4",
    "subtext": "#a6adc8",
    "lavender":"#b4befe",
    "blue":    "#89b4fa",
    "sapphire":"#74c7ec",
    "sky":     "#89dceb",
    "teal":    "#94e2d5",
    "green":   "#a6e3a1",
    "yellow":  "#f9e2af",
    "peach":   "#fab387",
    "maroon":  "#eba0ac",
    "red":     "#f38ba8",
    "mauve":   "#cba6f7",
    "pink":    "#f5c2e7",
    "flamingo":"#f2cdcd",
    "rosewater":"#f5e0dc",
    "accent":  "#7c3aed",
}

# ─── Processing defaults ──────────────────────────────────────────────────────
DEFAULTS = {
    "blur":           0,
    "brightness":     0,
    "contrast":       100,   # /100 → 1.0
    "sharpen":        0,
    "r_gain":         100,   # /100 → 1.0
    "g_gain":         100,
    "b_gain":         100,
    "clahe":          False,
    "grayscale":      False,
    "edge_mode":      "none",   # none|canny|sobel|laplacian
    "canny_low":      50,
    "canny_high":     150,
    "morph_op":       "none",   # none|erode|dilate|open|close
    "morph_kernel":   3,
    "thresh_mode":    "none",   # none|binary|adaptive|otsu
    "thresh_value":   127,
    "face_detect":    False,
    "contour_detect": False,
    "hough_lines":    False,
    "hough_thresh":   80,
    "color_space":    "BGR",    # BGR|HSV|LAB|YCrCb|GRAY
    "flip_h":         False,
    "flip_v":         False,
}

# ─── Tooltip strings ──────────────────────────────────────────────────────────
TOOLTIPS = {
    "blur":      "Gaussian Blur — kernel büyüklüğü (σ buna göre otomatik). Formül: G(x,y)=e^(-(x²+y²)/2σ²)",
    "brightness":"Piksel yoğunluğunu sabit artır/azalt. Formül: I' = I + β",
    "contrast":  "Tüm pikselleri alpha katsayısıyla ölçekle. Formül: I' = α·I + β",
    "sharpen":   "Keskinleştirme — Unsharp Mask tekniği. Formül: I' = I + k·(I - blur(I))",
    "r_gain":    "Kırmızı kanal kazancı. R' = clip(R × gain, 0, 255)",
    "g_gain":    "Yeşil kanal kazancı. G' = clip(G × gain, 0, 255)",
    "b_gain":    "Mavi kanal kazancı. B' = clip(B × gain, 0, 255)",
    "clahe":     "CLAHE (Contrast Limited Adaptive Histogram Equalization) — LAB uzayında L kanalına uygulanır",
    "grayscale": "BGR → Gri: Y = 0.114·B + 0.587·G + 0.299·R",
    "canny_low": "Canny histerezis alt eşiği. Bu değerin altındaki kenarlar elenir.",
    "canny_high":"Canny histerezis üst eşiği. Bu değerin üstündeki kenarlar kesindir.",
    "morph_op":  "Morfolojik işlem tipi: Erozyon (daraltma) / Genişletme / Açma / Kapama",
    "morph_kernel":"Morfolojik yapı elemanı boyutu (piksel)",
    "thresh_value":"Binary eşik değeri. I' = 255 if I > T else 0",
    "hough_thresh":"Hough uzayında bir doğru için minimum oy sayısı",
    "face_detect":"Haar Cascade (Frontal Face) ile yüz tespiti. Dikdörtgenlerle işaretler.",
    "contour":   "cv2.findContours ile kontur tespiti (RETR_EXTERNAL, CHAIN_APPROX_SIMPLE)",
}

# ─── Formula metadata ─────────────────────────────────────────────────────────
# Each entry: { "label": str, "latex": list[str], "kernel": str|None }
FORMULA_DATA: dict[str, dict] = {
    "identity": {
        "label": "Orijinal (Filtre Yok)",
        "latex": [
            r"$I' = I$",
            r"Herhangi bir dönüşüm uygulanmıyor.",
        ],
        "kernel": None,
    },
    "blur": {
        "label": "Gaussian Blur",
        "latex": [
            r"$G_{\sigma}(x,y) = \frac{1}{2\pi\sigma^2} e^{-\frac{x^2+y^2}{2\sigma^2}}$",
            r"$I' = I * G_{\sigma}$",
            r"Konvolüsyon: $(f*g)[n] = \sum_{k} f[k]\,g[n-k]$",
        ],
        "kernel": "gaussian",
    },
    "sharpen": {
        "label": "Unsharp Mask (Keskinleştirme)",
        "latex": [
            r"$I' = I + \alpha \cdot (I - G_{\sigma} * I)$",
            r"$I' = (1+\alpha)\,I - \alpha\,G_{\sigma}*I$",
        ],
        "kernel": "sharpen",
    },
    "canny": {
        "label": "Canny Kenar Tespiti",
        "latex": [
            r"$1.\ G = G_{\sigma} * I$  (Gaussian gürültü azaltma)",
            r"$2.\ M = \sqrt{G_x^2 + G_y^2}$  (gradyan büyüklüğü)",
            r"$3.\ \theta = \arctan\!\left(\frac{G_y}{G_x}\right)$",
            r"$4.\ \text{Histerezis}:\; T_{low} < M < T_{high}$",
        ],
        "kernel": None,
    },
    "sobel": {
        "label": "Sobel Kenar Tespiti",
        "latex": [
            r"$G_x = K_x * I$  (Yatay gradyan)",
            r"$G_y = K_y * I$  (Dikey gradyan)",
            r"$M = \sqrt{G_x^2 + G_y^2}$",
        ],
        "kernel": "sobel_x",
    },
    "laplacian": {
        "label": "Laplacian Kenar Tespiti",
        "latex": [
            r"$\nabla^2 I = \frac{\partial^2 I}{\partial x^2} + \frac{\partial^2 I}{\partial y^2}$",
            r"Kernel matrisi sağ panelde gösterilir.",
            r"$I' = K * I$",
        ],
        "kernel": "laplacian",
    },
    "erode": {
        "label": "Morfolojik Erozyon",
        "latex": [
            r"$(I \ominus B)(x,y) = \min_{(i,j)\in B} I(x+i, y+j)$",
            r"$B$: Yapı elemanı (structuring element)",
        ],
        "kernel": "morph",
    },
    "dilate": {
        "label": "Morfolojik Genişletme",
        "latex": [
            r"$(I \oplus B)(x,y) = \max_{(i,j)\in B} I(x+i, y+j)$",
            r"$B$: Yapı elemanı",
        ],
        "kernel": "morph",
    },
    "open": {
        "label": "Morfolojik Açma",
        "latex": [
            r"$I \circ B = (I \ominus B) \oplus B$",
            r"Erozyon ardından genişletme.",
        ],
        "kernel": "morph",
    },
    "close": {
        "label": "Morfolojik Kapama",
        "latex": [
            r"$I \bullet B = (I \oplus B) \ominus B$",
            r"Genişletme ardından erozyon.",
        ],
        "kernel": "morph",
    },
    "thresh_binary": {
        "label": "Binary Eşikleme",
        "latex": [
            r"$I'(x,y) = 255$  eğer  $I(x,y) > T$",
            r"$I'(x,y) = 0$    aksi halde",
        ],
        "kernel": None,
    },
    "thresh_otsu": {
        "label": "Otsu Eşikleme",
        "latex": [
            r"$\sigma_B^2(T) = \omega_0(T)\,\omega_1(T)\,[\mu_0(T)-\mu_1(T)]^2$",
            r"$T^* = \arg\max_T \sigma_B^2(T)$",
        ],
        "kernel": None,
    },
    "thresh_adaptive": {
        "label": "Adaptif Eşikleme",
        "latex": [
            r"$T(x,y) = \mu_{\text{nbhd}}(x,y) - C$",
            r"Yerel ortalamaya göre piksel bazlı eşik.",
        ],
        "kernel": None,
    },
    "grayscale": {
        "label": "Gri Tonlama (BT.601)",
        "latex": [
            r"$Y = 0.299\,R + 0.587\,G + 0.114\,B$",
        ],
        "kernel": None,
    },
    "clahe": {
        "label": "CLAHE (Adaptif Histogram Eşitleme)",
        "latex": [
            r"$p_r(r_k) = \frac{n_k}{MN}$  (olasılık yoğunluğu)",
            r"$s_k = \sum_{j=0}^{k} p_r(r_j)$  (CDF → dönüşüm)",
            r"Kontrast sınırı aşan piksel sayısı eşit dağıtılır.",
        ],
        "kernel": None,
    },
}
