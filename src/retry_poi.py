import json
import os
import time
import requests

from src.config import (
    OUTPUT_FILE,
    FAILED_POI_FILE,
    OVERPASS_ENDPOINTS,
    OVERPASS_QUERY_TIMEOUT,
    RETRY_OVERPASS_HTTP_TIMEOUT,
    RETRY_OVERPASS_MAX_RETRIES,
    RETRY_INTER_REQUEST_DELAY,
    RETRY_INTER_KOS_DELAY,
    POI_CATEGORIES,
    HEADERS,
    _POI_FAILED,
)
from src.utils.distance import hitung_jarak_haversine
from src.utils.parsers import _to_float, _safe_get_nested, _extract_poi_label


def _build_overpass_query(lat: float, lon: float, tags: list, radius: int) -> str:
    filters = "\n    ".join(
        f'nwr(around:{radius},{lat},{lon})["{k}"="{v}"];' for k, v in tags
    )
    return (
        f"[out:json][timeout:{OVERPASS_QUERY_TIMEOUT}];\n"
        f"(\n    {filters}\n);\n"
        f"out center 5;"
    )


def _fetch_overpass_with_retry(query: str, category: str) -> list | None:
    for endpoint in OVERPASS_ENDPOINTS:
        for attempt in range(1, RETRY_OVERPASS_MAX_RETRIES + 1):
            try:
                resp = requests.get(
                    endpoint,
                    params={"data": query},
                    headers={"User-Agent": HEADERS["User-Agent"], "Accept": "application/json"},
                    timeout=RETRY_OVERPASS_HTTP_TIMEOUT,
                )

                if resp.status_code == 200:
                    try:
                        return resp.json().get("elements", [])
                    except ValueError:
                        print(
                            f"  [retry:{category}] Response bukan JSON, skip endpoint."
                        )
                        break

                if resp.status_code in (429, 504):
                    wait = 15 * attempt
                    print(
                        f"  [retry:{category}] HTTP {resp.status_code} → tunggu {wait}s (attempt {attempt}/{RETRY_OVERPASS_MAX_RETRIES})"
                    )
                    time.sleep(wait)
                    continue

                print(f"  [retry:{category}] HTTP {resp.status_code} tidak tertangani.")
                break

            except requests.exceptions.Timeout:
                wait = 12 * attempt
                print(
                    f"  [retry:{category}] Timeout attempt {attempt}/{RETRY_OVERPASS_MAX_RETRIES} → tunggu {wait}s"
                )
                time.sleep(wait)

            except requests.exceptions.ConnectionError as e:
                print(
                    f"  [retry:{category}] ConnectionError: {e} → coba endpoint berikutnya"
                )
                break

            except Exception as e:
                print(f"  [retry:{category}] Error tak terduga: {e}")
                break
        else:
            print(f"  [retry:{category}] Semua retry habis di {endpoint}")

    return None


def retry_poi_for_entry(entry: dict) -> tuple[dict, list]:
    lat = _to_float(entry.get("latitude"))
    lon = _to_float(entry.get("longitude"))
    failed_cats = entry.get("failed_categories", [])

    updates = {}
    still_failed = []

    for category in failed_cats:
        config = POI_CATEGORIES.get(category)
        if not config:
            print(f"  [retry] Kategori tidak dikenal: {category}, dilewati.")
            continue

        print(f"  [retry] Querying {category} (radius {config['radius']}m)...")
        query = _build_overpass_query(lat, lon, config["tags"], config["radius"])
        elements = _fetch_overpass_with_retry(query, category)

        if elements is None:
            print(f"  [retry] {category} masih gagal, tetap di failed list.")
            still_failed.append(category)
        else:
            nearest_km, nearest_name = None, None
            for elem in elements:
                e_lat = _to_float(
                    elem.get("lat") or _safe_get_nested(elem, "center", "lat")
                )
                e_lon = _to_float(
                    elem.get("lon") or _safe_get_nested(elem, "center", "lon")
                )
                if e_lat is None or e_lon is None:
                    continue
                dist = hitung_jarak_haversine(lat, lon, e_lat, e_lon)
                if nearest_km is None or dist < nearest_km:
                    nearest_km = dist
                    nearest_name = _extract_poi_label(elem.get("tags", {}), category)

            updates[f"dist_to_nearest_{category}_km"] = (
                round(nearest_km, 3) if nearest_km else None
            )
            updates[f"nearest_{category}_name"] = nearest_name
            status = (
                f"{nearest_name} ({round(nearest_km, 3)} km)"
                if nearest_km
                else "tidak ada POI"
            )
            print(f"  [retry] {category} OK → {status}")

        time.sleep(RETRY_INTER_REQUEST_DELAY)

    return updates, still_failed


def load_json(filepath: str) -> list:
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError) as e:
        print(f"[load_json] Gagal baca {filepath}: {e}")
        return []


def save_json_atomic(filepath: str, data: list):
    tmp = filepath + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, filepath)
    except OSError as e:
        print(f"[save_json_atomic] Gagal simpan ke {filepath}: {e}")


def run_retry():
    failed_entries = load_json(FAILED_POI_FILE)
    if not failed_entries:
        print(
            f"[retry_poi] Tidak ada entry di {FAILED_POI_FILE}. Tidak ada yang perlu di-retry."
        )
        return

    print(f"[retry_poi] Ditemukan {len(failed_entries)} kos dengan POI gagal.")
    main_data = load_json(OUTPUT_FILE)
    if not main_data:
        print(
            f"[retry_poi] File utama {OUTPUT_FILE} kosong atau tidak ditemukan. Abort."
        )
        return

    main_index = {item.get("url_detail"): i for i, item in enumerate(main_data)}

    still_failed_entries = []
    resolved_count = 0

    for ei, entry in enumerate(failed_entries):
        url = entry.get("url_detail", f"entry_{ei}")
        cats = entry.get("failed_categories", [])
        print(f"\n[{ei + 1}/{len(failed_entries)}] Retry: {url}")
        print(f"  Kategori gagal sebelumnya: {cats}")

        updates, still_failed = retry_poi_for_entry(entry)

        if updates:
            idx = main_index.get(url)
            if idx is not None:
                main_data[idx].update(updates)
                save_json_atomic(OUTPUT_FILE, main_data)
                print(
                    f"  [OK] {len(updates) // 2} kategori berhasil, data utama diupdate."
                )
            else:
                print(
                    f"  [Warn] url_detail tidak ditemukan di {OUTPUT_FILE}, update dilewati."
                )

        if still_failed:
            entry["failed_categories"] = still_failed
            still_failed_entries.append(entry)
            print(f"  {len(still_failed)} kategori masih gagal: {still_failed}")
        else:
            resolved_count += 1
            print(f"  Semua kategori berhasil! Entry dihapus dari failed list.")

        if ei < len(failed_entries) - 1:
            print(f"  Jeda {RETRY_INTER_KOS_DELAY}s sebelum kos berikutnya...")
            time.sleep(RETRY_INTER_KOS_DELAY)

    save_json_atomic(FAILED_POI_FILE, still_failed_entries)

    print(f"\n[retry_poi] Selesai.")
    print(f"  Berhasil penuh  : {resolved_count} kos")
    print(f"  Masih gagal     : {len(still_failed_entries)} kos")
    if still_failed_entries:
        print(f"  → Jalankan lagi nanti: python run.py retry")


if __name__ == "__main__":
    run_retry()
