# Görüntü İşleme Laboratuvarı — Proje Raporu

---

## 1. Giriş ve Amaç

Dijital görüntü işleme; tıbbi görüntüleme, nesne tanıma, video analizi ve makine görüsü gibi pek çok alanda kritik rol oynamaktadır. Bu projenin amacı, görüntü işleme algoritmalarını gerçek zamanlı olarak uygulayan, her filtrenin matematiksel modelini görselleştiren ve kapsamlı istatistiksel analiz sunan etkileşimli bir masaüstü uygulaması geliştirmektir.

Uygulama; webcam görüntüsü, fotoğraf ve video dosyası olmak üzere üç farklı giriş kaynağını desteklemekte, onbeş adımlı işleme zinciri aracılığıyla çok sayıda filtre ve dönüşümü sıralı biçimde uygulamakta, sonuçları hem görsel hem de sayısal olarak sunmaktadır.

---

## 2. Kullanılan Teknolojiler

### 2.1 Python

Proje Python 3.10+ ile geliştirilmiştir. Python'ın bilimsel hesaplama ekosistemi (NumPy, SciPy) ve GUI desteği (PyQt5), görüntü işleme uygulamaları için olgun ve hızlı bir geliştirme ortamı sağlamaktadır.

### 2.2 OpenCV (Open Source Computer Vision Library)

OpenCV, 2500'den fazla optimize edilmiş görüntü işleme ve bilgisayar görüsü algoritması barındıran açık kaynaklı bir kütüphanedir. Bu projede şu işlemler için kullanılmıştır:

- Gaussian Blur, Sobel, Laplacian, Canny kenar tespiti
- Morfolojik operatörler (erozyon, genişletme, açma, kapama)
- Adaptif ve Otsu eşikleme
- Haar Cascade ile yüz tespiti
- Hough dönüşümü ile doğru tespiti
- Renk uzayı dönüşümleri (BGR ↔ HSV, LAB, YCrCb)
- Kontur tespiti ve görüntü geometrik dönüşümleri

### 2.3 PyQt5

PyQt5, Qt framework'ünün Python bağlantısıdır. Platform bağımsız masaüstü uygulaması geliştirmeye olanak tanır. Projede şu amaçlarla kullanılmıştır:

- Ana pencere ve panel düzeni (QMainWindow, QWidget, QLayout)
- Etkileşimli kontroller (QSlider, QCheckBox, QComboBox)
- Sekme tabanlı navigasyon (QTabWidget)
- İş parçacığı yönetimi (QThread, pyqtSignal)
- Görüntü gösterimi (QLabel + QPixmap + QImage)

### 2.4 Matplotlib

Matplotlib, Python için kapsamlı grafik çizim kütüphanesidir. PyQt5 ile Qt5Agg backend aracılığıyla entegre edilmiştir. Şu amaçlarla kullanılmıştır:

- RGB histogram ve CDF eğrisi çizimi
- 3-D yoğunluk yüzey haritası (Axes3D)
- FFT frekans spektrumu görselleştirmesi
- LaTeX formül render'ı (mathtext motoru)
- Kernel ısı haritası (imshow + TwoSlopeNorm)
- PDF rapor sayfalarının oluşturulması

### 2.5 NumPy

NumPy, Python'ın temel sayısal hesaplama kütüphanesidir. Görüntüler N-boyutlu diziler olarak temsil edildiğinden tüm piksel düzeyindeki işlemler NumPy üzerinden gerçekleştirilmiştir:

- Kanal ayrıştırma ve birleştirme
- Vektörize piksel dönüşümleri
- Gaussian gürültü üretimi (`np.random.normal`)
- FFT hesabı (`np.fft.fft2`, `np.fft.fftshift`)
- İstatistiksel fonksiyonlar (ortalama, standart sapma, varyans)

---

## 3. Sistem Mimarisi

### 3.1 Katmanlı Yapı (MVC Deseni)

Proje, Model-View-Controller (MVC) mimari deseni esas alınarak tasarlanmıştır. Bu yaklaşım sayesinde iş mantığı, arayüz ve koordinasyon kodları birbirinden bağımsız tutulmuştur.

```
┌─────────────────────────────────────────────────────┐
│                     VIEW (ui/)                      │
│  MainWindow  ControlPanel  Charts  FormulaView      │
└──────────────────────┬──────────────────────────────┘
                       │  pyqtSignal / pyqtSlot
┌──────────────────────▼──────────────────────────────┐
│                CONTROLLER (main_window.py)           │
│   _on_params_changed()  _on_frame()  _on_analysis() │
└──────────────────────┬──────────────────────────────┘
                       │  method calls
┌──────────────────────▼──────────────────────────────┐
│                    MODEL (core/)                    │
│   ImageProcessor   MathModels   ImageStats          │
└─────────────────────────────────────────────────────┘
```

**Model katmanı** (`core/`): Tüm ağır OpenCV işlemleri burada gerçekleşir. Qt bağımlılığı yoktur, dolayısıyla bağımsız test edilebilir.

**View katmanı** (`ui/`): Yalnızca gösterim sorumluluğu taşır. İş mantığı içermez.

**Controller** (`ui/main_window.py`): Model ve View arasında veri akışını yönetir, sinyal-slot bağlantılarını kurar.

### 3.2 İş Parçacığı Modeli

Görüntü işlemenin ana GUI iş parçacığını bloklamaması için iki ayrı QThread kullanılmıştır:

**FrameGrabber:** Webcam, video veya statik görüntüden kare okur. `frame_ready` sinyali ile işlenmiş kareyi ana iş parçacığına iletir. Webcam için ~30 FPS hedeflenir; video dosyaları gerçek FPS'lerinde oynatılır.

**AnalysisWorker:** FFT hesabı, 3-D yüzey oluşturma ve kapsamlı istatistik hesaplamalarını arka planda yürütür. Hesaplama tamamlandığında `result_ready` sinyali ile sonucu iletir.

Bu model sayesinde canlı video akışı sırasında arayüz donmaz, kullanıcı kontrolleri kesintisiz çalışmaya devam eder.

### 3.3 Dosya Yapısı

```
image-processing-project/
│
├── app.py              ← Giriş noktası: PyQt5 uygulaması başlatılır
├── config.py           ← Tema renkleri, varsayılan parametreler, formül verileri
├── requirements.txt    ← Bağımlılık listesi
│
├── core/               ← İş mantığı (Qt bağımsız)
│   ├── processor.py    ← 15 adımlı görüntü işleme pipeline'ı
│   ├── math_models.py  ← Kernel üreticiler, FFT, 3D yüzey hesabı
│   └── statistics.py   ← İstatistik hesaplama + PDF rapor dışa aktarma
│
├── ui/                 ← Kullanıcı arayüzü
│   ├── main_window.py  ← Ana pencere ve olay koordinasyonu
│   └── widgets/
│       ├── control_panel.py  ← Sekmeli parametre kontrolleri
│       ├── charts.py         ← Histogram, 3D, FFT, renk uzayı grafikleri
│       └── formula_view.py   ← LaTeX formül + kernel ısı haritası
│
└── utils/
    ├── stream.py        ← FrameGrabber ve AnalysisWorker iş parçacıkları
    └── logger.py        ← Uygulama içi günlük sistemi
```

---

## 4. Görüntü İşleme Pipeline'ı

Her kare, aşağıdaki sırayla işlenir. Yalnızca aktif filtreler için hesaplama yapılır; bu yaklaşım gereksiz işlem yükünü ortadan kaldırır.

```
Ham Görüntü (BGR, uint8)
    │
    ▼ Adım 0   Döndürme
    ▼ Adım 1   Gri Tonlama
    ▼ Adım 2   RGB Kanal Kazancı
    ▼ Adım 3   CLAHE
    ▼ Adım 4   Parlaklık / Kontrast
    ▼ Adım 5   Keskinleştirme
    ▼ Adım 6   Gaussian Blur
    ▼ Adım 7   Morfolojik İşlemler
    ▼ Adım 8   Eşikleme
    ▼ Adım 9   Kenar Tespiti
    ▼ Adım 10  Özellik Tespiti
    ▼ Adım 11  Renk Uzayı Dönüşümü
    ▼ Adım 12  Renk Ters Çevirme
    ▼ Adım 13  Sepya Tonu
    ▼ Adım 14  Gaussian Gürültü
    ▼ Adım 15  Yatay / Dikey Çevirme
    │
    ▼
ProcessResult (işlenmiş kare, formül anahtarı, kernel matrisi, aktif işlemler)
```

---

## 5. Algoritmaların Matematiksel Temeli

### 5.1 Gaussian Blur

Gaussian bulanıklaştırma, görüntü üzerine iki boyutlu bir Gauss çekirdeğinin konvolüsyonu uygulanarak gerçekleştirilir.

**Gaussian fonksiyonu:**

```
G(x, y) = (1 / 2πσ²) · e^(-(x² + y²) / 2σ²)
```

**Konvolüsyon işlemi:**

```
I'(x, y) = (I * G)(x, y) = Σ Σ I(x+i, y+j) · G(i, j)
```

Burada `σ` (standart sapma), kernel boyutuna bağlı olarak `σ = 0.3 × ((k-1)/2 - 1) + 0.8` formülüyle OpenCV varsayılan değeri kullanılarak otomatik hesaplanır.

Gaussian blur, yüksek frekanslı gürültüyü bastırır; ancak keskin kenarları da yumuşatır. Bu özelliği, kenar tespitinden önce gürültü azaltma adımı olarak sıkça kullanılmasını sağlar.

### 5.2 Keskinleştirme (Unsharp Mask)

Unsharp Mask yöntemi, görüntüden bulanık versiyonunun çıkarılmasıyla elde edilen "kenar maskesini" özgün görüntüye ekler.

```
I' = I + α · (I - G_σ * I)
   = (1 + α) · I - α · G_σ * I
```

Uygulamada bu işlem, aşağıdaki konvolüsyon çekirdeğine karşılık gelir:

```
K = [  0    -α     0  ]
    [ -α   1+4α   -α  ]
    [  0    -α     0  ]
```

`α` (güç katsayısı) kullanıcı tarafından 0–20 arasında ayarlanır; kodda `strength = α / 10` şeklinde normalize edilir.

### 5.3 Parlaklık ve Kontrast

Doğrusal piksel dönüşümü:

```
I'(x, y) = α · I(x, y) + β
```

- `α` (kontrast katsayısı): 0.5 – 2.5 arasında değer alır. `α > 1` kontrastı artırır, `α < 1` azaltır.
- `β` (parlaklık ofseti): −100 ile +100 arasında değer alır.

Sonuç [0, 255] aralığında kırpılır (`cv2.convertScaleAbs`).

### 5.4 CLAHE (Contrast Limited Adaptive Histogram Equalization)

Standart histogram eşitleme, tüm görüntüye tek bir dönüşüm uygular ve aşırı kontrast artışına yol açabilir. CLAHE bu sorunu yerel olarak çözer.

Görüntü küçük bölgelere (tile) ayrılır ve her bölgede histogram eşitlemesi ayrı ayrı yapılır. Kontrast sınırı (clip limit) aşan histogram çubukları komşu bölgelere dağıtılır:

```
p_r(r_k) = n_k / (M · N)         (olasılık yoğunluğu)

s_k = Σ(j=0, k) p_r(r_j)         (kümülatif dağılım fonksiyonu → CDF)
```

Projede bu işlem, BGR görüntünün önce LAB renk uzayına dönüştürülmesi, ardından yalnızca parlaklık kanalına (L) uygulanması şeklinde gerçekleştirilir:

```
BGR → LAB → CLAHE(L) → LAB → BGR
```

Bu yaklaşım, renk bilgisini bozmadan yalnızca parlaklık dengesini iyileştirir.

### 5.5 Gri Tonlama

BT.601 (ITU-R Recommendation 601) standardına göre ağırlıklı dönüşüm:

```
Y = 0.299·R + 0.587·G + 0.114·B
```

İnsan gözünün yeşil ışığa en duyarlı, maviye en az duyarlı olduğu gerçeğini yansıtır. Farklı katsayılar farklı algısal sonuçlar doğurur; projede OpenCV'nin `cv2.COLOR_BGR2GRAY` dönüşümü bu standartı uygular.

### 5.6 Canny Kenar Tespiti

Canny algoritması dört aşamadan oluşur:

1. **Gürültü azaltma:** Gaussian bulanıklaştırma uygulanır.
2. **Gradyan hesabı:** Sobel operatörü ile yatay (G_x) ve dikey (G_y) gradyanlar hesaplanır, büyüklük ve yön bulunur:
   ```
   M = √(G_x² + G_y²)
   θ = arctan(G_y / G_x)
   ```
3. **Non-maximum suppression:** Gradyan yönünde yerel olmayan maksimumlar bastırılır; böylece ince, tek pikselli kenar çizgileri elde edilir.
4. **Histerezis eşikleme:** İki eşik değeri (T_low, T_high) ile kenarlar sınıflandırılır:
   - `M > T_high` → kesin kenar
   - `T_low < M < T_high` → yalnızca kesin kenara bağlıysa kenar
   - `M < T_low` → kenar değil

### 5.7 Sobel Kenar Tespiti

Sobel operatörü, yatay ve dikey gradyanları ayrı çekirdeklerle hesaplar:

```
G_x = [-1  0  +1]     G_y = [-1  -2  -1]
      [-2  0  +2]            [ 0   0   0]
      [-1  0  +1]            [+1  +2  +1]
```

Birleşik gradyan büyüklüğü:

```
M = √(G_x² + G_y²)
```

### 5.8 Laplacian Kenar Tespiti

Laplacian operatörü, görüntünün ikinci türevini hesaplar. Renk geçişlerindeki ani değişimleri yakalar:

```
∇²I = ∂²I/∂x² + ∂²I/∂y²
```

Ayrık kernel matrisi:

```
K = [ 0   1   0]
    [ 1  -4   1]
    [ 0   1   0]
```

### 5.9 Morfolojik İşlemler

Morfolojik işlemler, yapı elemanı (structuring element) B ile görüntü I'yi karşılaştırarak çeşitli geometrik dönüşümler uygular.

**Erozyon** (küçültme):
```
(I ⊖ B)(x, y) = min_{(i,j) ∈ B} I(x+i, y+j)
```

**Genişletme** (büyütme):
```
(I ⊕ B)(x, y) = max_{(i,j) ∈ B} I(x+i, y+j)
```

**Açma** (küçük nesneleri giderir):
```
I ∘ B = (I ⊖ B) ⊕ B
```

**Kapama** (küçük delikleri doldurur):
```
I • B = (I ⊕ B) ⊖ B
```

### 5.10 Eşikleme

**Binary eşikleme:**
```
I'(x, y) = 255   eğer I(x, y) > T
I'(x, y) = 0     aksi halde
```

**Otsu yöntemi:** Histogram analizi ile iki sınıf arasındaki sınıflar arası varyansı (between-class variance) en büyükleyen optimal eşik değeri T* otomatik hesaplanır:

```
σ_B²(T) = ω₀(T) · ω₁(T) · [μ₀(T) - μ₁(T)]²

T* = argmax_T σ_B²(T)
```

**Adaptif eşikleme:** Her piksel için yerel komşuluğun Gaussian ağırlıklı ortalaması kullanılır:

```
T(x, y) = μ_komşu(x, y) - C
```

### 5.11 Görüntü Döndürme

Affine dönüşüm matrisi kullanılarak görüntü merkez etrafında döndürülür:

```
M = [cos(θ)  -sin(θ)  (1-cos(θ))·cx + sin(θ)·cy]
    [sin(θ)   cos(θ)  -sin(θ)·cx + (1-cos(θ))·cy]
```

Ardından `cv2.warpAffine(I, M, (w, h))` ile her pikselin yeni konumu bilineer interpolasyon ile hesaplanır.

### 5.12 Sepya Dönüşümü

Görüntü; piksel başına 3×3 renk matrisi çarpımıyla dönüştürülür:

```
[R']   [0.393  0.769  0.189] [R]
[G'] = [0.349  0.686  0.168]·[G]
[B']   [0.272  0.534  0.131] [B]
```

Sonuç [0, 255] aralığında kırpılır.

### 5.13 Gaussian Gürültü

Her piksel konumuna bağımsız Gaussian dağılımlı rastgele değer eklenir:

```
I'(x, y) = clip(I(x, y) + N(0, σ²), 0, 255)
```

`σ` kullanıcı tarafından 0–50 arasında ayarlanır. Gürültü, filtre algoritmalarının gürültü bastırma etkinliğini test etmek için kullanışlıdır.

---

## 6. İstatistiksel Analiz Modülü

`ImageStats.compute()` metodu her kare için aşağıdaki ölçümleri hesaplar:

### 6.1 Temel İstatistikler

Her renk kanalı (R, G, B) için ortalama ve standart sapma ayrı ayrı hesaplanır:

```
μ_k = (1/MN) · Σ I_k(x, y)         k ∈ {R, G, B}

σ_k = √[(1/MN) · Σ (I_k(x, y) - μ_k)²]
```

### 6.2 Shannon Entropisi

Histogram olasılık yoğunluğu üzerinden hesaplanan entropi, görüntünün bilgi içeriğini ölçer:

```
H = -Σ p(r_k) · log₂(p(r_k))         [bit]
```

Yüksek entropi → görüntüde çok sayıda farklı yoğunluk seviyesi var → daha fazla detay.
Düşük entropi → görüntü tek düze ya da büyük ölçüde sıkıştırılabilir.

### 6.3 Sinyal-Gürültü Oranı (SNR)

```
SNR = μ_gri / σ_gri
```

Yüksek SNR → sinyal baskın, görüntü temiz.
Düşük SNR → gürültü baskın.

### 6.4 Kovaryans

İki renk kanalı arasındaki doğrusal ilişki:

```
Cov(R, G) = (1/N) · Σ (R_i - μ_R)(G_i - μ_G)
```

Pozitif kovaryans → kanallar benzer biçimde değişiyor (doğal fotoğraflarda yaygın).
Sıfıra yakın kovaryans → kanallar birbirinden bağımsız.

### 6.5 Bölgesel Varyans

Görüntü 4×4 = 16 eşit bölgeye ayrılır; her bölgede gri yoğunluk varyansı hesaplanır. Bu ölçüm, görüntüdeki yerel doku farklılıklarını ve yapısal düzensizlikleri gösterir.

---

## 7. Spektral Analiz (FFT)

Hızlı Fourier Dönüşümü (Fast Fourier Transform), görüntüyü uzaysal alandan frekans alanına taşır. Bu sayede görüntünün hangi frekans bileşenlerini ne yoğunlukta içerdiği görülebilir.

**İki boyutlu FFT:**
```
F(u, v) = Σ_x Σ_y I(x, y) · e^(-j2π(ux/M + vy/N))
```

**Log ölçekli genlik spektrumu (görselleştirme için):**
```
magnitude(u, v) = log(1 + |F(u, v)|)
```

Frekans merkezlemesi (`fftshift`) sonrasında düşük frekanslar merkeze taşınır. Merkezdeki parlak bölge → düşük frekans bileşenleri (genel parlaklık, büyük yapılar). Merkez dışı bölgeler → yüksek frekans bileşenleri (kenarlar, gürültü).

**Enerji ayrıştırması:**
Güç spektrumu üzerinde dairesel maske uygulanarak düşük ve yüksek frekans enerji oranları ayrı ayrı hesaplanır:

```
E_düşük  = Σ_{||(u,v)||≤R} |F(u,v)|²  /  E_toplam

E_yüksek = Σ_{||(u,v)||>R} |F(u,v)|²  /  E_toplam
```

---

## 8. Renk Uzayı Dönüşümleri

Farklı renk uzayları farklı görüntü özelliklerini ayrıştırır:

| Renk Uzayı | Kanallar | Kullanım Amacı |
|-----------|----------|----------------|
| BGR | Mavi, Yeşil, Kırmızı | Standart görüntü temsili |
| HSV | Ton, Doygunluk, Değer | Renk bazlı segmentasyon |
| LAB | Parlaklık, a* (kırmızı-yeşil), b* (sarı-mavi) | Algısal renk uzaklığı hesabı |
| YCrCb | Parlaklık, Kırmızı renk farkı, Mavi renk farkı | Yüz tespiti, video sıkıştırma |
| GRAY | Gri yoğunluk | Kenar tespiti ön adımı |

---

## 9. Kullanıcı Arayüzü Tasarımı

### 9.1 Genel Düzen

Uygulama 1500×940 piksel boyutunda üç dikey panele ayrılmıştır:

- **Sol panel (305 px):** Giriş kaynağı seçimi, sekmeli parametre kontrolleri, işlem günlüğü
- **Orta panel (esnek):** Orijinal ve işlenmiş görüntü yan yana, dört sekmeli analiz grafikleri
- **Sağ panel (285 px):** LaTeX formül ve kernel ısı haritası, istatistik tablosu

### 9.2 Kontrol Paneli Sekmeleri

Parametre kontrolleri beş tematik sekmeye ayrılmıştır:

| Sekme | İçerik |
|-------|--------|
| Temel | Blur, Keskinlik, Döndürme, Gürültü, Parlaklık, Kontrast, CLAHE, Gri Tonlama, Negatif, Çevirme |
| Renk | R/G/B kanal kazancı, Sepya tonu, Renk uzayı seçici |
| Kenar | Yöntem seçimi (Canny/Sobel/Laplacian), Canny eşikleri |
| Morfoloji | İşlem tipi, kernel boyutu, eşikleme yöntemi ve değeri |
| Özellik | Yüz tespiti, kontur tespiti, Hough doğruları |

### 9.3 Matematiksel Model Paneli

Her aktif filtrenin LaTeX formülü ve kernel matrisi ısı haritası gerçek zamanlı olarak güncellenir. Formüller matplotlib'in mathtext motoru ile render edilir; harici LaTeX kurulumu gerekmez. Kernel matrisi, kırmızı-mavi renk ölçeğiyle hücre hücre sayısal değerleriyle birlikte gösterilir.

### 9.4 Piksel Renk Bilgisi

İşlenmiş görüntüye tıklandığında tıklanan pikselin R, G, B ve Hex değerleri istatistik panelinde güncellenir. Bu özellik, belirli bir renk bölgesinin kanal dağılımını anlık incelemeye olanak tanır.

### 9.5 Tema

Arayüz, Catppuccin Mocha karanlık renk paleti üzerine inşa edilmiştir. 24 renk değişkeni merkezi `config.py` dosyasında tutulur; bu sayede tema değişikliği tek noktadan uygulanabilir. Karanlık tema; uzun süreli görüntü inceleme çalışmalarında göz yorgunluğunu azaltır ve kontrast değerlendirmesi için daha uygun bir zemin sağlar.

---

## 10. Dışa Aktarma ve Raporlama

### 10.1 Görüntü Kaydetme

İşlenmiş kare PNG veya JPEG formatında diske yazılır. PNG kayıpsız sıkıştırma sağlar; piksel değerlerini koruyan bilimsel analizler için tercih edilir.

### 10.2 PDF Rapor

`ReportExporter.export_pdf()` metodu üç sayfalık bir PDF belgesi oluşturur:

- **Sayfa 1:** Orijinal ve işlenmiş görüntü yan yana, aktif işlemler listesi
- **Sayfa 2:** RGB histogram karşılaştırması (orijinal ve işlenmiş, üst üste)
- **Sayfa 3:** Tüm istatistiksel ölçümler tablo halinde

### 10.3 Pano Kopyalama

İşlenmiş kare, PyQt5'in `QApplication.clipboard()` arayüzü aracılığıyla sistem panosuna kopyalanır. Bu sayede görüntü herhangi bir uygulamaya Ctrl+V ile doğrudan yapıştırılabilir.

---

## 11. Performans Optimizasyonları

### 11.1 Hesaplama Kısıtlama (Throttling)

Canlı webcam akışında histogram, FFT ve istatistik güncellemeleri her 5 karede bir yapılır. Statik görüntü veya duraklatılmış video durumunda her parametre değişikliğinde güncelleme tetiklenir.

### 11.2 Tembel Render

Formula paneli yalnızca aktif formül anahtarı değiştiğinde yeniden çizilir. Bu, parametre değişikliklerinde (örneğin yalnızca Canny eşiği ayarlanırken) gereksiz Matplotlib render çağrısını engeller.

### 11.3 Seçici Pipeline

Pipeline'da her adım yalnızca ilgili parametre varsayılan değerinden farklıysa çalışır. Örneğin `blur_amount == 0` ise Gaussian Blur adımı tamamen atlanır. Bu yaklaşım, özellikle canlı akışta işlem yükünü önemli ölçüde azaltır.

---

## 12. Sonuç

Bu proje; gerçek zamanlı görüntü işleme, matematiksel görselleştirme ve istatistiksel analizi tek bir platformda birleştiren bütünleşik bir laboratuvar ortamı sunmaktadır.

Geliştirme sürecinde öne çıkan teknik tercihler şöyle sıralanabilir:

- **MVC mimarisi**, iş mantığı ile arayüzü birbirinden ayırarak kodun test edilebilirliğini ve sürdürülebilirliğini artırmıştır.
- **İş parçacığı ayrımı**, ağır hesaplamaların arayüzü dondurmadan arka planda yürütülmesini sağlamıştır.
- **Modüler pipeline tasarımı**, yeni filtre eklemeyi minimal değişiklikle mümkün kılmaktadır; yeni bir adım için yalnızca `processor.py`'ye işlem kodu ve `control_panel.py`'ye bir kontrol elemanı eklenmesi yeterlidir.
- **Konfigürasyon merkezi** (`config.py`), tema renkleri, varsayılan değerler, formül meta verisi ve tooltip metinlerini tek noktada tutarak bakım maliyetini düşürmektedir.

Uygulama; görüntü işleme algoritmalarının matematiksel temellerini anlamak, farklı filtrelerin etkilerini karşılaştırmak ve işlenmiş görüntülerin kantitatif analizini yapmak amacıyla kullanılabilecek kapsamlı bir eğitim ve araştırma aracı niteliği taşımaktadır.
