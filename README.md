# Mamikos Scraper - UNUD Housing Analysis

Web scraper untuk Mamikos.com yang mengumpulkan dan menganalisis data kos-kosan di sekitar kampus Universitas Udayana.

## Fitur

- Scraping listing properti dengan geolokasi
- Kalkulasi jarak ke kampus UNUD (Jimbaran & Sudirman)
- Kalkulasi jarak ke Bandara Ngurah Rai
- POI (Point of Interest) enrichment via OpenStreetMap Overpass API
- Progressive saving dengan failure recovery
- Retry mechanism untuk POI yang gagal di-fetch

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
├── data/                         # Data files (gitignored)
│   ├── raw/                     # Raw scraped data
│   ├── processed/               # Processed/analyzed data
│   └── failed/                  # Failed POI logs
├── sessions/                     # Browser sessions (gitignored)
├── notebooks/                    # Analysis scripts
│   └── insight/                 # Future insight.py development
├── archive/                      # Historical data backups
└── tests/                        # Unit tests (future)
```

## Output Data

Data disimpan dalam format JSON di `data/raw/mamikos_data_unud_sudirman.json` dengan struktur:

```json
{
  "nama_kost": "string",
  "harga_card": "string",
  "url_detail": "string",
  "latitude": float,
  "longitude": float,
  "jarak_unud_jimbaran_km": float,
  "jarak_unud_sudirman_km": float,
  "jarak_bandara_ngurah_rai_km": float,
  "dist_to_nearest_university_km": float,
  "nearest_university_name": "string",
  "dist_to_nearest_hospital_km": float,
  "nearest_hospital_name": "string",
  ...
}
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
