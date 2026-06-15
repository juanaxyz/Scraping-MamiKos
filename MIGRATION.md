# Migration Guide - Project Reorganization

## Changes Made (2026-06-14)

### Directory Structure
**Old structure:**
```
UAS PROJECT/
├── main.py
├── retry_poi.py
├── mamikos_scraper.py (deprecated)
├── testing.py (deprecated)
├── mamikos_data_unud_sudirman.json
├── failed_poi_unud_sudirman.json
├── mamikos_session.json
└── archive/
```

**New structure:**
```
UAS PROJECT/
├── run.py (NEW - entry point)
├── src/
│   ├── scraper.py (refactored from main.py)
│   ├── retry_poi.py (refactored)
│   ├── config.py (NEW - all constants)
│   └── utils/
│       ├── distance.py
│       ├── poi.py
│       ├── parsers.py
│       └── file_io.py
├── data/
│   ├── raw/
│   ├── processed/
│   └── failed/
├── sessions/
├── notebooks/
│   └── insight/
└── tests/
```

### What Changed

#### 1. Code Organization
- **Extracted utilities**: Shared helper functions moved to `src/utils/`
  - `distance.py`: Haversine calculation
  - `poi.py`: POI enrichment & Overpass API logic
  - `parsers.py`: JSON parsing helpers
  - `file_io.py`: ProgressiveSaver & FailedPoiLogger classes

- **Centralized config**: All constants moved to `src/config.py`
  - Coordinates, URLs, headers
  - Overpass API settings
  - POI categories
  - File paths

#### 2. Entry Point
- **Old**: `python main.py`
- **New**: `python run.py scrape` or `python run.py retry`

#### 3. File Locations
- Data files: `*.json` → `data/raw/` and `data/failed/`
- Sessions: `mamikos_session.json` → `sessions/`
- Analysis: `notebooks/insight/` (ready for future work)

#### 4. Deleted Files
- `mamikos_scraper.py` (deprecated/unused)
- `testing.py` (deprecated)
- `mamikos_session copy.json` (duplicate)

#### 5. New Files
- `run.py` - CLI entry point
- `README.md` - Project documentation
- `requirements.txt` - Python dependencies
- `.gitignore` - Enhanced git exclusions

### Breaking Changes

⚠️ **Import paths changed** - If you have custom scripts importing from the old files:

**Old:**
```python
from main import scrape_pencarian_hybrid
from retry_poi import run_retry
```

**New:**
```python
from src.scraper import scrape_pencarian_hybrid
from src.retry_poi import run_retry
from src.config import POI_CATEGORIES, REKTORAT_UNUD
from src.utils.distance import hitung_jarak_haversine
```

### No Breaking Changes

✅ **Data format unchanged** - All JSON output structures remain the same
✅ **Functionality preserved** - All scraping & POI logic works exactly as before
✅ **Session compatibility** - Existing session files work with new structure

### Migration Steps

If you have existing scripts that depend on the old structure:

1. Update import statements (see above)
2. Update file paths if hardcoded:
   - `mamikos_data_*.json` → `data/raw/mamikos_data_*.json`
   - `failed_poi_*.json` → `data/failed/failed_poi_*.json`
   - `mamikos_session.json` → `sessions/mamikos_session.json`

### Benefits

- ✅ Cleaner separation of concerns (code vs data vs config)
- ✅ Easier to maintain and extend
- ✅ Standard Python project structure
- ✅ Better git hygiene (data files excluded)
- ✅ Reusable utility modules
- ✅ Professional documentation

### Rollback

If you need to rollback, the old files are preserved in git history:
```bash
git log --all --full-history -- main.py
git checkout <commit-hash> -- main.py retry_poi.py
```
