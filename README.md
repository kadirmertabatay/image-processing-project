# Görüntü İşleme Laboratuvarı

Gerçek zamanlı görüntü işleme, matematiksel analiz ve görsel istatistik sunan masaüstü uygulaması. PyQt5, OpenCV ve Matplotlib ile geliştirilmiştir.

---

## İçindekiler

- [Özellikler](#özellikler)
- [Kurulum](#kurulum)
- [Çalıştırma](#çalıştırma)
- [Uygulama Yapısı](#uygulama-yapısı)
- [Proje Dosya Yapısı](#proje-dosya-yapısı)
- [Teknik Mimari](#teknik-mimari)
- [Bağımlılıklar](#bağımlılıklar)

---

## Özellikler

### Giriş Kaynakları
| Kaynak | Açıklama |
|--------|----------|
| Webcam | Gerçek zamanlı ~30 FPS canlı akış |
| Fotoğraf | PNG, JPG, JPEG, BMP, TIFF, WEBP |
| Video | MP4, AVI, MOV, MKV, WMV (otomatik döngü) |

### Görüntü İşleme Filtreleri

**Uzamsal Filtreler**
- **Gaussian Blur** — Ayarlanabilir kernel boyutu (1–41 px), otomatik sigma
- **Keskinleştirme (Unsharp Mask)** — Güç kontrolü 0–20
- **Görüntü Döndürme** — −180° ile +180° arasında döndürme
- **Gaussian Gürültü** — Ayarlanabilir standart sapma (σ = 0–50)

**Piksel Dönüşümleri**
- **Parlaklık** — Doğrusal offset (−100 / +100)
- **Kontrast** — Çarpımsal ölçek (0.5× – 2.5×)
- **CLAHE** — Adaptif histogram eşitleme (LAB L kanalı, 8×8 tile)
- **Gri Tonlama** — BT.601 standardı (Y = 0.299R + 0.587G + 0.114B)
- **Renk Ters Çevirme (Negatif)** — `bitwise_not`

**Renk Kanalı Kontrolü**
- R, G, B kanalları bağımsız kazanç kontrolü (0–2.0×)
- **Sepya Tonu** — Klasik 3×3 renk matrisi dönüşümü

**Kenar Tespiti**
| Yöntem | Açıklama |
|--------|----------|
| Canny | Gaussian + gradyan büyüklüğü + histerezis |
| Sobel | Yatay (Gx) ve dikey (Gy) gradyan, birleşik büyüklük |
| Laplacian | İkinci türev operatörü (3×3 kernel) |

**Morfolojik İşlemler**
- Erozyon, Genişletme, Açma, Kapama
- Ayarlanabilir kernel boyutu (3–21 px, tek sayı)

**Eşikleme**
- Binary (sabit eşik)
- Otsu (otomatik optimal eşik)
- Adaptif (yerel Gaussian ortalaması)

**Özellik Tespiti**
- Yüz Tespiti (Haar Cascade)
- Kontur Tespiti (RETR_EXTERNAL)
- Hough Doğruları (ayarlanabilir eşik)

**Geometrik İşlemler**
- Yatay / Dikey Çevirme

### Analiz ve Görselleştirme

- **RGB Histogram** — Canlı R, G, B kanal grafikleri + CDF eğrisi
- **3-D Yüzey** — Yoğunluk yüzey haritası (64×64 örneklem, Plasma renk haritası)
- **FFT Spektrum** — Log ölçekli genlik spektrumu + radyal güç profili
- **Renk Uzayı** — HSV, LAB, YCrCb, GRAY kanal ayrıştırma

### İstatistik Paneli

Çözünürlük, kanal sayısı, bit derinliği, R/G/B ortalaması ve standart sapması, genel ortalama/std, min/max piksel, Shannon entropisi, SNR ve tıklanan pikselin R, G, B, Hex değerleri.

### Matematiksel Model Paneli

Aktif filtrenin LaTeX formülü ve kernel matrisi ısı haritası (matplotlib mathtext, harici LaTeX kurulumu gerektirmez).

### Dışa Aktarma
- İşlenmiş görüntüyü PNG/JPEG olarak kaydetme
- PDF rapor (orijinal + işlenmiş görüntü, histogram, istatistik tablosu)
- Pano kopyalama (Ctrl+V ile yapıştırılabilir)

---

## Kurulum

### Gereksinimler

- Python **3.10** veya üzeri
- `pip`
- macOS, Windows veya Linux

---

### 1. Depoyu Klonlayın

```bash
git clone <repo-url>
cd image-processing-project
```

---

### 2. Sanal Ortam (venv) Oluşturun

Sanal ortam, proje bağımlılıklarını sistem Python'ından izole eder. Bu adımı **mutlaka** yapın.

**macOS / Linux:**
```bash
python3 -m venv venv
```

**Windows:**
```cmd
python -m venv venv
```

> Oluşturma başarılıysa proje dizininde `venv/` klasörü görünür.

---

### 3. Sanal Ortamı Etkinleştirin

**macOS / Linux:**
```bash
source venv/bin/activate
```

**Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

> Etkinleştirme başarılıysa terminal satırının başında `(venv)` ibaresi belirir:
> ```
> (venv) kullanici@makine image-processing-project %
> ```

---

### 4. Bağımlılıkları Yükleyin

```bash
pip install -r requirements.txt
```

Yükleme tamamlandıktan sonra şunlar kurulmuş olur:

| Paket | Versiyon | Kullanım |
|-------|----------|----------|
| `opencv-python` | ≥ 4.5 | Görüntü işleme çekirdeği |
| `PyQt5` | ≥ 5.15 | Masaüstü arayüzü |
| `matplotlib` | ≥ 3.5 | Grafik ve formula görselleştirme |
| `numpy` | ≥ 1.21 | Matris ve sayısal hesaplama |
| `Pillow` | ≥ 9.0 | PDF rapor resim işleme |
| `scipy` | ≥ 1.7 | İstatistik hesaplamaları |

---

## Çalıştırma

Sanal ortamın **aktif** olduğundan emin olun (`(venv)` ibaresini kontrol edin), ardından:

```bash
python app.py
```

Uygulama 1500×940 px boyutunda açılır.

---

### Sanal Ortamı Kapatmak

Çalışma oturumunuz bittiğinde:

```bash
deactivate
```

---

### Hızlı Başvuru

```bash
# Her yeni terminal oturumunda yapmanız gerekenler:
source venv/bin/activate      # (macOS/Linux)
python app.py
```

---

## Uygulama Yapısı

```
┌─────────────────────────────────────────────────────────┐
│                    Başlık Çubuğu                        │
│  ▣ Görüntü İşleme Laboratuvarı          ● Durum         │
├──────────────┬──────────────────────┬───────────────────┤
│  SOL PANEL   │    ORTA PANEL        │    SAĞ PANEL      │
│  (305 px)    │    (Esnek)           │    (285 px)       │
│              │                      │                   │
│ Giriş        │  Orijinal │ İşlenmiş │ Matematiksel      │
│ Kaynağı      │  Görüntü  │ Görüntü  │ Model             │
│              │           │          │ (LaTeX + Kernel)  │
│ ─────────    │ ──────────────────── │                   │
│              │                      │ ─────────────     │
│ Kontrol      │  ┌──────────────┐    │                   │
│ Paneli       │  │ Histogram    │    │ İstatistik        │
│ (Sekmeli)    │  │ 3-D Yüzey   │    │ Paneli            │
│              │  │ FFT          │    │                   │
│ ─────────    │  │ Renk Uzayı  │    │                   │
│              │  └──────────────┘    │                   │
│ İşlem        │                      │                   │
│ Günlüğü      │                      │                   │
└──────────────┴──────────────────────┴───────────────────┘
```

### Kontrol Paneli Sekmeleri

| Sekme | İçerik |
|-------|--------|
| **Temel** | Blur, Keskinlik, Döndürme, Gürültü, Parlaklık, Kontrast, CLAHE, Gri Tonlama, Negatif, Çevirme |
| **Renk** | R/G/B kanal kazancı, Sepya tonu, Renk uzayı seçici |
| **Kenar** | Kenar tespiti yöntemi (Canny/Sobel/Laplacian), Canny eşikleri |
| **Morfoloji** | Morfolojik işlem tipi, kernel boyutu, eşikleme yöntemi |
| **Özellik** | Yüz tespiti, kontur, Hough doğruları |

---

## Proje Dosya Yapısı

```
image-processing-project/
│
├── app.py                        # Giriş noktası, PyQt5 başlatıcı
├── config.py                     # Tema renkleri, varsayılan parametreler,
│                                 # formül meta verisi, tooltip metinleri
├── requirements.txt              # Python bağımlılıkları
│
├── core/                         # İş mantığı (Qt bağımsız)
│   ├── processor.py              # Görüntü işleme pipeline (ImageProcessor)
│   ├── math_models.py            # Kernel üreticiler, FFT, 3D yüzey hesabı
│   └── statistics.py            # İstatistik hesaplama + PDF rapor dışa aktarma
│
├── ui/                           # Kullanıcı arayüzü katmanı
│   ├── main_window.py            # Ana pencere, panel koordinasyonu, olay bağlantıları
│   └── widgets/
│       ├── control_panel.py      # Sekmeli parametre kontrol paneli
│       ├── charts.py             # Histogram, 3D yüzey, FFT, renk uzayı grafikleri
│       └── formula_view.py       # LaTeX formül ve kernel ısı haritası paneli
│
└── utils/                        # Yardımcı araçlar
    ├── stream.py                 # FrameGrabber (kamera/video iş parçacığı),
    │                             # AnalysisWorker (arka plan analiz iş parçacığı)
    └── logger.py                 # Uygulama içi günlük sistemi
```

---

## Teknik Mimari

### MVC Deseni

```
Model (core/)          View (ui/)              Controller (main_window.py)
──────────────         ──────────────          ──────────────────────────
ImageProcessor    ←──  ControlPanel  ──►  params_changed signal
MathModels             MainWindow         _on_params_changed()
ImageStats             HistogramWidget    _on_frame()
                       FormulaView        _on_analysis_done()
```

### İş Parçacığı Modeli

```
Ana İş Parçacığı (Qt GUI)
    │
    ├── FrameGrabber (QThread)
    │       Webcam / video / statik görüntü okur
    │       frame_ready sinyali ile ana iş parçacığına gönderir
    │
    └── AnalysisWorker (QThread)
            FFT, 3D yüzey, istatistik hesaplar
            result_ready sinyali ile sonucu döndürür
```

### İşleme Pipeline Sırası

```
Ham Görüntü
    │
    ▼
0.  Döndürme (warpAffine)
1.  Gri Tonlama
2.  RGB Kanal Kazancı
3.  CLAHE
4.  Parlaklık / Kontrast (convertScaleAbs)
5.  Keskinleştirme (filter2D)
6.  Gaussian Blur
7.  Morfolojik İşlemler
8.  Eşikleme
9.  Kenar Tespiti
10. Özellik Tespiti (Yüz / Kontur / Hough)
11. Renk Uzayı Dönüşümü
12. Renk Ters Çevirme
13. Sepya Tonu
14. Gürültü Ekleme
15. Yatay / Dikey Çevirme
    │
    ▼
ProcessResult (frame, formula_key, kernel, active_ops)
```

---

## Bağımlılıklar

```
opencv-python >= 4.5.0
PyQt5         >= 5.15.0
matplotlib    >= 3.5.0
numpy         >= 1.21.0
Pillow        >= 9.0.0
scipy         >= 1.7.0
```

---

## Sorun Giderme

**Webcam açılmıyor (macOS)**
macOS, kamera iznini ilk kullanımda sorar. İzin verdikten sonra uygulamayı yeniden başlatın.

**`No module named 'PyQt5'` hatası**
Sanal ortamın aktif olmadığını gösterir. `source venv/bin/activate` komutunu çalıştırın.

**`pip install` yavaş**
Pip önbelleğini kullanarak yeniden deneyin:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Uygulama donuyor**
Derin Analiz (3D yüzey + FFT) büyük görüntülerde birkaç saniye sürebilir; bu normaldir. İşlem arka planda çalışır.
