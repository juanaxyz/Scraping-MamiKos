# AGENTS.md – Quick Run‑Book

**Environment**
- Project runs in a Conda environment (already provisioned). No package install steps needed.

**Key files**
- `main.py` – entry point for full scrape.
- `mamikos_scraper.py` – library with all scraping helpers.
- `mamikos_session.json` – Playwright storage state cache.
- `mamikos_data.json` – default output location (only written when `output_file` arg is supplied).

**Running the scraper**
1. Activate your Conda env and launch:
   ```
   python main.py
   ```
2. The script will:
   - Re‑use `mamikos_session.json` if it exists; delete the file to start a fresh session.
   - Open a Chromium headless browser via Playwright.
   - Block image requests (via `block_assets`) to speed up scraping.
   - Call `search_by_locations` (default location slug) and iterate over the resulting cards.
3. **Important:** `main.py` mistakenly references an undefined variable `page` when counting cards (line 40). The intended variable is the `page` returned by `search_by_locations`. Fix by replacing `cards = page.locator(".kost-rc")` with `cards = hasil_scrape` or the proper locator from the returned `page`.
4. To write results to JSON, pass `output_file="mamikos_data.json"` (or another path) to `search_by_locations`:
   ```python
   search_by_locations(context, output_file="mamikos_data.json", session_file="mamikos_session.json", debug=True)
   ```

**Debug / ad‑hoc inspection**
- All helper functions accept `debug=True` for verbose console output.
- For isolated room‑detail inspection, run the standalone script (`testing.py`). **This file is now deprecated and can be ignored**.

**Session handling**
- Session state is saved at the end of `main.py` via `context.storage_state(path=SESSION_FILE)`. Subsequent runs will reuse the saved cookies/headers.
- Deleting `mamikos_session.json` forces a fresh login/initial navigation.

**Known quirks**
- No automated test suite; manual checks are done via the debug script.
- The repository does not include a `requirements.txt` or `environment.yml` readable here; rely on the existing Conda environment.

**Typical one‑off command** (run from repo root):
```python
from mamikos_scraper import search_by_locations
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    ctx = p.chromium.launch(headless=True).new_context()
    search_by_locations(
        ctx,
        location="your-location-slug",
        output_file="mamikos_data.json",
        session_file="mamikos_session.json",
        debug=True,
    )
```

---
*Only repository‑specific actions that an OpenCode agent would otherwise miss are listed above.*