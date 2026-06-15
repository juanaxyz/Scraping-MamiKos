import time
import requests

from src.config import (
    POI_CATEGORIES,
    POI_DISTANCE_CACHE,
    OVERPASS_ENDPOINTS,
    OVERPASS_QUERY_TIMEOUT,
    OVERPASS_HTTP_TIMEOUT,
    OVERPASS_INTER_REQUEST_DELAY,
    OVERPASS_MAX_RETRIES,
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


def _fetch_overpass(query: str, category: str, debug: bool) -> list | None:
    for endpoint in OVERPASS_ENDPOINTS:
        for attempt in range(1, OVERPASS_MAX_RETRIES + 1):
            try:
                resp = requests.get(
                    endpoint,
                    params={"data": query},
                    headers={
                        "User-Agent": HEADERS["User-Agent"],
                        "Accept": "application/json",
                    },
                    timeout=OVERPASS_HTTP_TIMEOUT,
                )

                if resp.status_code == 200:
                    try:
                        return resp.json().get("elements", [])
                    except ValueError:
                        if debug:
                            print(
                                f"      [POI:{category}] Response bukan JSON valid dari {endpoint}"
                            )
                        break

                if resp.status_code in (429, 504):
                    wait = 10 * attempt
                    if debug:
                        print(
                            f"      [POI:{category}] HTTP {resp.status_code} → tunggu {wait}s (attempt {attempt}/{OVERPASS_MAX_RETRIES})"
                        )
                    time.sleep(wait)
                    continue

                if debug:
                    print(
                        f"      [POI:{category}] HTTP {resp.status_code} tidak tertangani, skip endpoint."
                    )
                break

            except requests.exceptions.Timeout:
                wait = 8 * attempt
                if debug:
                    print(
                        f"      [POI:{category}] Timeout attempt {attempt}/{OVERPASS_MAX_RETRIES} → tunggu {wait}s"
                    )
                time.sleep(wait)

            except requests.exceptions.ConnectionError as e:
                if debug:
                    print(
                        f"      [POI:{category}] ConnectionError: {e} → coba endpoint berikutnya"
                    )
                break

            except Exception as e:
                if debug:
                    print(f"      [POI:{category}] Error tak terduga: {e}")
                break
        else:
            if debug:
                print(f"      [POI:{category}] Semua retry habis di {endpoint}")

    if debug:
        print(
            f"      [POI:{category}] Semua endpoint gagal → akan di-log ke failed_poi"
        )
    return None


def enrich_nearest_poi_distances(
    kos_lat,
    kos_lon,
    url_detail: str = "",
    categories_to_run: list | None = None,
    debug: bool = False,
) -> tuple[dict, list]:
    result = {}
    for cat in POI_CATEGORIES:
        result[f"dist_to_nearest_{cat}_km"] = None
        result[f"nearest_{cat}_name"] = None

    lat = _to_float(kos_lat)
    lon = _to_float(kos_lon)
    if lat is None or lon is None:
        return result, []

    cache_key = (round(lat, 4), round(lon, 4))
    if cache_key in POI_DISTANCE_CACHE and categories_to_run is None:
        if debug:
            print(f"      [POI] Cache hit untuk {cache_key}")
        return POI_DISTANCE_CACHE[cache_key].copy(), []

    target_cats = categories_to_run or list(POI_CATEGORIES.keys())
    failed_cats = []

    for category in target_cats:
        config = POI_CATEGORIES[category]
        if debug:
            print(f"      [POI] Querying: {category} (radius {config['radius']}m)...")

        query = _build_overpass_query(lat, lon, config["tags"], config["radius"])
        elements = _fetch_overpass(query, category, debug)

        if elements is None:
            result[f"dist_to_nearest_{category}_km"] = _POI_FAILED
            result[f"nearest_{category}_name"] = _POI_FAILED
            failed_cats.append(category)
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

            if nearest_km is not None:
                result[f"dist_to_nearest_{category}_km"] = round(nearest_km, 3)
                result[f"nearest_{category}_name"] = nearest_name
                if debug:
                    print(
                        f"      [POI] {category}: {nearest_name} ({round(nearest_km, 3)} km)"
                    )
            else:
                if debug:
                    print(f"      [POI] {category}: tidak ada POI dalam radius")

        time.sleep(OVERPASS_INTER_REQUEST_DELAY)

    if not failed_cats:
        POI_DISTANCE_CACHE[cache_key] = result.copy()

    return result, failed_cats


def poi_has_failed_categories(item: dict) -> bool:
    return any(
        str(item.get(f"dist_to_nearest_{cat}_km")) == _POI_FAILED
        for cat in POI_CATEGORIES
    )


def get_failed_categories(item: dict) -> list[str]:
    return [
        cat
        for cat in POI_CATEGORIES
        if str(item.get(f"dist_to_nearest_{cat}_km")) == _POI_FAILED
    ]
