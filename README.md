# Mamikos Scraper - UNUD Housing Analysis

Web scraper untuk Mamikos.com yang mengumpulkan dan menganalisis data kos-kosan di sekitar kampus Universitas Udayana.

## Fitur

- Scraping listing properti dengan geolokasi
- Kalkulasi jarak ke kampus UNUD (Jimbaran & Sudirman)
- Kalkulasi jarak ke Bandara Ngurah Rai
- POI (Point of Interest) enrichment via OpenStreetMap Overpass API
- Progressive saving dengan failure recovery
- Retry mechanism untuk POI yang gagal di-fetch
- **Pipeline preprocessing otomatis** — normalisasi nama kota/kecamatan, parsing harga & fasilitas, binning tier & zona jarak
- **Analisis 35 Insight Mahasiswa** — ekspektasi budget, jarak, fasilitas, simulasi keputusan, dan fairness score
- **Threshold dinamis** — harga tier, budget simulasi, jarak ideal semuanya dihitung via quantile/percentile dari distribusi data aktual, bukan hardcoded

## Setup

### Menggunakan Conda (Recommended)

```bash
conda env create -f environment.yml
conda activate <env-name>
playwright install chromium
```

### Menggunakan pip

```bash
pip install -r requirements.txt
playwright install chromium
```

## Usage

### Menjalankan scraper utama

```bash
python run.py scrape
```

Atau langsung:

```bash
python run.py
```

### Retry POI enrichment yang gagal

```bash
python run.py retry
```

### Menjalankan analisis 40 insight

```bash
python notebooks/insight/analyze_mamikos.py
```

Output tersimpan di `notebooks/insight/output/*.png`

## Struktur Proyek

```
├── src/                          # Source code
│   ├── scraper.py               # Main scraper logic
│   ├── retry_poi.py             # POI retry logic
│   ├── config.py                # Configuration & constants
│   └── utils/                   # Shared utilities
│       ├── distance.py          # Haversine distance calculation
│       ├── poi.py               # POI enrichment logic
│       ├── parsers.py           # JSON/HTML parsing helpers
│       └── file_io.py           # File I/O classes
├── data/
│   ├── preprocess.py            # Preprocessing pipeline (normalisasi, parsing, binning)
│   ├── mamikos_all.csv          # Raw scraped data (137+ kolom)
│   └── processed/
│       ├── mamikos_clean.csv    # Preprocessed data (166 kolom, 358 kos valid)
│       ├── raw/                 # Raw scraped data (JSON)
│       └── failed/              # Failed POI logs
├── analysis_mahasiswa_v2/       # Analisis 35 Insight Mahasiswa
│   ├── analyze_student.py       # Script utama — 35 insight + poster + ringkasan
│   └── output/                  # 35 PNG + poster + ringkasan.txt
├── analysis_mahasiswa/          # Analisis v1 (IQR outlier detection reference)
├── sessions/                    # Browser sessions (gitignored)
├── notebooks/
│   └── insight/                 # Analisis 40 insight (v1, referensi)
│       ├── analyze_mamikos.py
│       └── output/
├── archive/                     # Historical data backups
└── tests/                       # Unit tests (future)
```

## Output Data

Data disimpan dalam format CSV di `data/mamikos_all.csv` dengan 137 kolom:

```csv
nama_kost,harga_real_detail,price,latitude,longitude,size_area,dist_to_nearest_university_km,...
```

## 40 Insight Analisis Kost Jimbaran

Analisis dilakukan terhadap **241 kost** di area Jimbaran, Badung dengan **137 kolom** data.

### Bagian A: Insight Dasar (1-24)

| No | Insight | Deskripsi | Statistik Deskriptif |
|----|---------|-----------|---------------------|
| 1 | **Distribusi Harga Bulanan** | Histogram & boxplot harga kost | Mean Rp 2.8jt, median Rp 2.5jt, skewness 2.81 (right-skewed) |
| 2 | **Harga per Subdistrict** | Perbandingan harga 5 subdistrict | Kuta Selatan (n=220, mean Rp 2.86jt) dominan |
| 3 | **Harga per Gender** | Perbandingan Campur vs Putri | Campur (Rp 2.88jt) > Putri (Rp 2.01jt), selisih Rp 866rb |
| 4-10 | **Harga vs Jarak POI** | Korelasi harga dengan 7 POI terdekat | Universitas (r=-0.13, p=0.048) & terminal (r=0.14, p=0.031) signifikan |
| 11 | **Harga vs Ukuran Kamar** | Regresi linear harga ~ ukuran | R²=0.248, setiap +1m² = +Rp 47,866 |
| 12 | **Harga vs Tahun Bangunan** | Korelasi harga dengan usia bangunan | R=0.178, p=0.007 (signifikan tapi lemah) |
| 13 | **Top Fasilitas Kamar** | 10 fasilitas kamar paling umum | Kasur (95%), AC (91.3%), Lemari (82.2%) |
| 14 | **Top Fasilitas Berbagi** | 10 fasilitas berbagi paling umum | WiFi (85.9%), Dapur (64.7%), CCTV (62.2%) |
| 15 | **Top Fasilitas Kamar Mandi** | Fasilitas kamar mandi paling umum | K. Mandi Dalam (91.7%), Shower (90.5%) |
| 16 | **Jumlah Fasilitas vs Harga** | Korelasi jumlah fasilitas dengan harga | Fasilitas kamar paling berkorelasi (r=0.38) |
| 17 | **Distribusi DP Percentage** | Distribusi uang muka | Mean 33%, median 30%, range 10-50% |
| 18 | **Analisis Rating** | Distribusi dan korelasi rating | Mean 0.94, sebagian besar belum dirating |
| 19 | **View & Love Count** | Popularitas vs harga | Korelasi negatif (r=-0.31) - harga tinggi = view rendah |
| 20 | **Harga per m²** | Harga normalisasi per luas | Mean Rp 168,862/m², median Rp 157,576/m² |
| 21 | **Distribusi Ukuran Kamar** | Frekuensi per kategori ukuran | S (<12m²): 85, M: 51, L: 49, XL: 36, XXL: 20 |
| 22 | **Heatmap Korelasi** | Korelasi 19 variabel numerik | Visualisasi hubungan antar variabel |
| 23 | **Kamar Tersedia vs Harga** | Analisis ketersediaan kamar | Tidak ada pola signifikan |
| 24 | **Top Termahal & Termurah** | 10 kost termahal dan termurah | Termahal: Rp 12jt (Humayana), Termurah: Rp 700rb (Pak Komang) |

### Bagian B: Inferensial & Forecasting (25-39)

| No | Insight | Metode | Hasil Utama |
|----|---------|--------|-------------|
| 25 | **CI 95% Mean Harga** | t-interval | Rp 2.63jt - Rp 2.98jt |
| 26 | **Uji Normalitas** | Shapiro-Wilk | Tidak normal (p=4.22e-18) |
| 27 | **Distribusi Log-Normal** | Log transform + Shapiro | Lebih baik dari normal (p=1.22e-5) |
| 28 | **T-test Campur vs Putri** | Welch's t-test | Signifikan (t=5.62, p=8.92e-7) |
| 29 | **Regresi: Harga ~ Ukuran** | Simple linear regression | Price = 47,866×Size + 1,877,167 (R²=0.248) |
| 30 | **Expected Price per m²** | Descriptive + groupby | Per subdistrict: Kuta Selatan Rp 169,653/m² |
| 31 | **Regresi: Harga ~ Jarak Univ** | Simple linear regression | R²=0.016 (lemah), p=0.048 |
| 32 | **Multiple Regression** | OLS (9 fitur) | R²=0.42, MAPE=20.7%, RMSE=Rp 842rb |
| 33 | **ANOVA: Harga per Subdistrict** | One-way ANOVA | F=5.13, p=0.024 (signifikan) |
| 34 | **Rumus Prediksi Harga** | Multiple regression equation | 9 variabel, contoh prediksi akurat |
| 35 | **What-if Analysis** | Regression coefficients | Jarak RS paling berpengaruh (-Rp 358rb/km) |
| 36 | **Prediksi per Kategori Ukuran** | Groupby + boxplot | S: Rp 2.29jt, XXL: Rp 4.61jt |
| 37 | **Klasifikasi Harga** | Regression-based classifier | Accuracy 74.4% |
| 38 | **Monte Carlo Simulation** | 10,000 simulasi normal | 95% CI: Rp 469rb - Rp 5.5jt |
| 39 | **Residual Analysis** | Residual diagnostics | Model good fit, residual ~0 |

### Bagian C: Proyeksi Masa Depan (40)

| No | Insight | Metode | Hasil |
|----|---------|--------|-------|
| 40 | **Proyeksi Harga 2-15 Tahun** | Gabungan Building Year Trend (40%) + Inflasi (60%) | Tabel proyeksi + grafik 3 skenario |

#### Tabel Proyeksi Harga

| Tahun | +Tahun | Pesimis (3%) | Sentral (4%) | Optimis (5%) | Kenaikan |
|-------|--------|-------------|-------------|-------------|----------|
| 2026 | 0 | Rp 2.80jt | Rp 2.80jt | Rp 2.80jt | baseline |
| 2028 | +2 | Rp 3.07jt | Rp 3.11jt | Rp 3.14jt | +11% |
| 2031 | +5 | Rp 3.31jt | Rp 3.41jt | Rp 3.51jt | +22% |
| 2036 | +10 | Rp 3.75jt | Rp 3.97jt | Rp 4.22jt | +42% |
| 2041 | +15 | Rp 4.23jt | Rp 4.64jt | Rp 5.10jt | +65% |

**Metode**: Gabungan Building Year Trend (40%) + Inflasi Historis Indonesia (60%) dengan 3 skenario inflasi.

---

## Analisis 35 Insight Mahasiswa v2

Analisis lanjutan yang berfokus pada **kebutuhan mahasiswa** mencari kos di sekitar UNUD Jimbaran. Data: **358 kos** (setelah preprocessing) dengan **166 kolom**.

### Preprocessing (`data/preprocess.py`)

Sebelum analisis, data mentah melalui pipeline berikut:

| Langkah | Detail |
|---------|--------|
| Parsing harga | `harga_real_detail` → `price` (float) |
| Normalisasi kota | `Denpasar`/`Kota Denpasar` → `Denpasar`, `Badung`/`Kabupaten Badung` → `Badung` |
| Normalisasi kecamatan | 13 varian → 7 kecamatan unik |
| Tier harga | Quantile-based: **Q0/Q20/Q40/Q60/Q80/Q100** |
| Zona jarak | Hardcoded: `<1km` / `1-2km` / `2-3km` / `3-5km` / `>5km` |
| Filter valid | Drop baris tanpa harga/jarak |
| Output | `data/processed/mamikos_clean.csv` (358 baris × 166 kolom) |

### 35 Insight

**Tema 1 — Dasar Budget**
| No | Insight | Metode |
|----|---------|--------|
| 1 | Gambaran Harga | Histogram + boxplot, mean/median/skewness |
| 2 | Budget Kumulatif | Ecdf — budget X dapet berapa pilihan? |
| 3 | Estimasi Biaya Bulan Pertama | Price + DP (P50/P90) |
| 4 | Distribusi DP | Histogram DP% |
| 5 | Termurah vs Termahal | 10 lowest & highest |

**Tema 2 — Jarak & Lokasi**
| No | Insight | Metode |
|----|---------|--------|
| 6 | Harga per Zona Jarak | Groupby zone, mean/median |
| 7 | Estimasi Hemat Jalan Jauh | Rata-rata price <1km vs >5km |
| 8 | Ekspektasi Jarak per Tier | Groupby tier → mean distance |
| 9 | Rekomendasi Kos Dekat Kampus | Filter jarak ≤1km + AC + WiFi + KM Dalam, sort by price |
| 10 | Harga per Kecamatan | Boxplot per subdistrict |

**Tema 3 — Ekspektasi Fasilitas**
| No | Insight | Metode |
|----|---------|--------|
| 11 | Fasilitas Paling Umum | Bar chart frekuensi fasilitas |
| 12 | Ekspektasi Fasilitas per Tier | Groupby tier → % fasilitas |
| 13 | Ekspektasi Luas Kamar per Tier | Groupby tier → mean size |
| 14 | AC Worth It? | Harga AC vs non-AC (barplot) |
| 15 | KM Dalam vs Luar | Harga batch-in vs batch-out |
| 16 | Heatmap Fasilitas per Tier | Heatmap % fasilitas per tier |
| 17 | Jumlah Fasilitas vs Harga | Scatter + regresi linear |

**Tema 4 — Prediksi & Estimasi**
| No | Insight | Metode |
|----|---------|--------|
| 18 | Prediksi Harga dari Luas | Regresi linear: price ~ size |
| 19 | Prediksi Multi-Faktor | Multi-regresi: size + distance + year + total_facilities |
| 20 | Harga per m² Wajar | Groupby tier → PPS distribution |
| 21 | Simulasi Naik Budget | Tambah Rp 500rb → tier upgrade comparison |
| 22 | Kategori Mahal/Premium | Pie chart: Murah/Terjangkau/Standar/Mahal/Premium |
| 23 | Tahun Bangunan vs Harga | Scatter + regresi |
| 24 | Available Room | Histogram distribusi kamar kosong |
| 25 | Popularitas per Tier | Mean view_count & love_count per tier |

**Tema 5 — Simulasi & Keputusan**
| No | Insight | Metode |
|----|---------|--------|
| 26 | Simulasi Cari Kos Ideal | Filter median price + Q3 distance + AC + WiFi + KM Dalam |
| 27 | Waktu Terbaik Cari Kos | Love count by time-based grouping |
| 28 | Prediksi Kenaikan 1 Tahun | Regresi price ~ building_year |
| 29 | Kamu Tier Mana? | Feature classification based on size/distance/facilities |
| 30 | Fairness Score | Composite score: PPS vs tier median |
| 31 | Rating vs Harga | Scatter + korelasi |
| 32 | Campur vs Putri | Boxplot per gender |
| 33 | Overpriced & Underpriced | **IQR outlier detection** (Q1-1.5×IQR, Q3+1.5×IQR) dari residual regresi |
| 34 | Love/View Ratio | Scatter love_ratio vs price |
| 35 | What-if Dashboard | Simulasi berbagai budget → rekomendasi terbaik |

### Threshold Dinamis

Semua angka ambang batas dihitung otomatis dari distribusi data:

| Parameter | Sumber |
|-----------|--------|
| Tier harga | Quantile: Q0, Q20, Q40, Q60, Q80, Q100 |
| Budget simulasi | P10 / P25 / P50 / P75 / P90 price |
| Harga per m² wajar | P33 & P66 PPS per tier |
| Jarak ideal | Q3 distance |
| Love/View ratio tinggi | P75 love_ratio |
| Overpriced / Underpriced | IQR 1.5× dari residual regresi |

Data mentah hanya **241 kos**; setelah preprocessing tersaring **358 kos** karena pipeline berhasil mengekstrak data dari lebih banyak record yang sebelumnya gagal diparse.

### Menjalankan

```bash
# Preprocessing
python data/preprocess.py

# Analisis 35 Insight + poster + ringkasan
python analysis_mahasiswa_v2/analyze_student.py
```

Output tersimpan di `analysis_mahasiswa_v2/output/`.

### Perbandingan v1 vs v2

| Aspek | v1 (`analysis_mahasiswa/`) | v2 (`analysis_mahasiswa_v2/`) |
|-------|---------------------------|-------------------------------|
| Jumlah insight | 40 | 35 |
| Preprocessing | Inline, manual | Pipeline terpisah (`data/preprocess.py`) |
| Threshold | Hardcoded (Rp 1,5jt/2,5jt/3,5jt/5jt) | Quantile-based (dinamis) |
| Outlier | Top-5 residual | IQR 1.5× (statistical) |
| Fokus | Real estate umum | Mahasiswa UNUD |
| Data | 241 kos, price-only | 358 kos, price + DP + view + love |

## Visualisasi

Semua visualisasi tersimpan di `notebooks/insight/output/`:

```
output/
├── 01_price_distribution.png          # Distribusi harga
├── 02_price_by_subdistrict.png        # Harga per subdistrict
├── 03_price_by_gender.png             # Harga per gender
├── 04_10_price_vs_distance.png        # Harga vs jarak 7 POI
├── 11_price_vs_size.png               # Harga vs ukuran kamar
├── 12_price_vs_building_year.png      # Harga vs tahun bangunan
├── 13_top_room_facilities.png         # Top fasilitas kamar
├── 14_top_share_facilities.png        # Top fasilitas berbagi
├── 15_top_bath_facilities.png         # Top fasilitas kamar mandi
├── 16_facility_count_vs_price.png     # Jumlah fasilitas vs harga
├── 17_dp_percentage.png               # Distribusi DP
├── 18_rating_analysis.png             # Analisis rating
├── 19_view_love_analysis.png          # View & love count
├── 20_price_per_sqm.png               # Harga per m²
├── 21_size_distribution.png           # Distribusi ukuran
├── 22_correlation_heatmap.png         # Heatmap korelasi
├── 23_available_room_vs_price.png     # Kamar tersedia vs harga
├── 24_top_cheapest_expensive.png      # Termahal & termurah
├── 26_normality_test.png              # Uji normalitas
├── 27_log_normal_test.png             # Uji log-normal
├── 28_ttest_gender.png                # T-test gender
├── 29_regression_price_size.png       # Regresi harga~ukuran
├── 30_expected_price_per_sqm.png      # Expected price/m²
├── 31_regression_price_university.png # Regresi harga~universitas
├── 32_multiple_regression.png         # Multiple regression
├── 33_anova_subdistrict.png           # ANOVA subdistrict
├── 34_prediction_formula.png          # Rumus prediksi
├── 35_whatif_analysis.png             # What-if analysis
├── 36_price_by_size_category.png      # Harga per kategori ukuran
├── 37_price_classification.png        # Klasifikasi harga
├── 38_monte_carlo_simulation.png      # Monte Carlo simulation
├── 39_residual_analysis.png           # Residual analysis
└── 40_future_price_projection.png     # Proyeksi harga masa depan
```

## Koordinat Acuan

- **UNUD Jimbaran (Rektorat)**: -8.798256, 115.172495
- **UNUD Sudirman**: -8.673060, 115.219012
- **Bandara Ngurah Rai**: -8.745771, 115.167836

## Catatan

- Session browser disimpan otomatis untuk menghindari rate limiting
- Gambar di-block untuk mempercepat scraping
- POI enrichment menggunakan Overpass API dengan retry mechanism
- Failed POI dicatat untuk di-retry nanti
- Hapus `sessions/mamikos_session.json` untuk memaksa session baru

## Development

Untuk pengembangan lebih lanjut, tempatkan script analisis di `notebooks/insight/`.

## License

Educational project for UNUD Statistics Department.
