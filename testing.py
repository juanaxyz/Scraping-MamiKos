import json
import math
import os
import re
import requests
from playwright.sync_api import sync_playwright

BASE_URL = "https://mamikos.com/cari/"
SESSION_FILE = "mamikos_session.json"
OUTPUT_FILE = "mamikos_hybrid_data.json"

# Koordinat Titik Acuan Analisis (Kampus UNUD)
REKTORAT_UNUD = [-8.798256245751867, 115.17249471428231]  # Kampus Bukit Jimbaran
UNUD_SUDIRMAN = [-8.673060417640015, 115.21901203994138]  # Kampus Denpasar

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_RADIUS_METERS = 3000
OVERPASS_TIMEOUT_SECONDS = 25
ENABLE_POI_ENRICHMENT = True

# Pemetaan kategori POI ke tag OSM yang relevan untuk demand/livability score.
POI_CATEGORIES = {
    "university": [("amenity", "university")],
    "hospital": [("amenity", "hospital")],
    "marketplace": [("amenity", "marketplace")],
    "supermarket": [("shop", "supermarket")],
    "station": [("public_transport", "station"), ("railway", "station")],
    "mall": [("shop", "mall")],
    "government": [("office", "government")],
    "clinic": [("amenity", "clinic")],
    "school": [("amenity", "school")],
    "restaurant": [("amenity", "restaurant")],
}

POI_DISTANCE_CACHE = {}


def hitung_jarak_haversine(lat1, lon1, lat2, lon2):
    """Menghitung jarak geografis lingkaran besar antara dua koordinat (km)."""
    R = 6371.0
    rad_lat1, rad_lon1 = math.radians(lat1), math.radians(lon1)
    rad_lat2, rad_lon2 = math.radians(lat2), math.radians(lon2)

    dlat = rad_lat2 - rad_lat1
    dlon = rad_lon2 - rad_lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(rad_lat1) * math.cos(rad_lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def build_overpass_query(lat, lon, radius=OVERPASS_RADIUS_METERS):
    query_lines = []
    for tags in POI_CATEGORIES.values():
        for key, value in tags:
            query_lines.append(
                f'nwr(around:{radius},{lat},{lon})["{key}"="{value}"];'
            )

    query_block = "\n    ".join(query_lines)
    return (
        "[out:json][timeout:25];\n"
        "(\n"
        f"    {query_block}\n"
        ");\n"
        "out center tags;"
    )


def _to_float(value):
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def enrich_nearest_poi_distances(kos_lat, kos_lon, debug=False):
    result = {
        f"dist_to_nearest_{category}_km": None
        for category in POI_CATEGORIES.keys()
    }

    lat = _to_float(kos_lat)
    lon = _to_float(kos_lon)
    if lat is None or lon is None:
        return result

    cache_key = (round(lat, 4), round(lon, 4))
    if cache_key in POI_DISTANCE_CACHE:
        return POI_DISTANCE_CACHE[cache_key].copy()

    query = build_overpass_query(lat, lon)
    try:
        response = requests.post(
            OVERPASS_URL,
            data={"data": query},
            headers={
                "User-Agent": HEADERS["User-Agent"],
                "Accept": "application/json",
            },
            timeout=OVERPASS_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
    except Exception as e:
        if debug:
            print(f"    [POI] Gagal query Overpass: {e}")
        POI_DISTANCE_CACHE[cache_key] = result.copy()
        return result

    nearest = {category: None for category in POI_CATEGORIES.keys()}
    elements = payload.get("elements", [])

    for elem in elements:
        tags = elem.get("tags", {})
        elem_lat = _to_float(elem.get("lat", elem.get("center", {}).get("lat")))
        elem_lon = _to_float(elem.get("lon", elem.get("center", {}).get("lon")))
        if elem_lat is None or elem_lon is None:
            continue

        distance_km = hitung_jarak_haversine(lat, lon, elem_lat, elem_lon)

        for category, tag_pairs in POI_CATEGORIES.items():
            matched = any(tags.get(key) == value for key, value in tag_pairs)
            if not matched:
                continue

            previous = nearest[category]
            if previous is None or distance_km < previous:
                nearest[category] = distance_km

    for category, distance_km in nearest.items():
        if distance_km is not None:
            result[f"dist_to_nearest_{category}_km"] = round(distance_km, 3)

    POI_DISTANCE_CACHE[cache_key] = result.copy()
    return result


def ekstrak_detail_via_hybrid(url_detail):
    """
    Pendekatan Hybrid: Mengunduh HTML secara instan via requests
    dan membongkar objek JavaScript (window.detail) via Regex.
    """
    try:
        response = requests.get(url_detail, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            html_content = response.text

            # Regex untuk menangkap var detail dan var price_card_info
            match_detail = re.search(
                r"var\s+detail\s*=\s*(\{.*?\});", html_content, re.DOTALL
            )
            match_price = re.search(
                r"var\s+price_card_info\s*=\s*(\{.*?\});",
                html_content,
                re.DOTALL,
            )

            detail_data = {}

            if match_detail:
                obj_kos = json.loads(match_detail.group(1))
                kos_lat = obj_kos.get("latitude")
                kos_lon = obj_kos.get("longitude")

                detail_data["latitude"] = kos_lat
                detail_data["longitude"] = kos_lon

                # Lakukan kalkulasi jarak jika koordinat valid
                if kos_lat and kos_lon:
                    j_jimbaran = hitung_jarak_haversine(
                        kos_lat, kos_lon, REKTORAT_UNUD[0], REKTORAT_UNUD[1]
                    )
                    j_sudirman = hitung_jarak_haversine(
                        kos_lat, kos_lon, UNUD_SUDIRMAN[0], UNUD_SUDIRMAN[1]
                    )
                    detail_data["jarak_unud_jimbaran_km"] = round(j_jimbaran, 2)
                    detail_data["jarak_unud_sudirman_km"] = round(j_sudirman, 2)

            if match_price:
                obj_harga = json.loads(match_price.group(1))
                if "price" in obj_harga:
                    h_bulan = obj_harga["price"].get("price_monthly", {})
                    detail_data["harga_real_detail"] = (
                        f"{h_bulan.get('currency_symbol')}{h_bulan.get('price')}/{h_bulan.get('rent_type_unit')}"
                    )

            return detail_data

    except Exception as e:
        print(f"      Gagal HTTP Request detail: {e}")

    return {}

def scrape_pencarian_hybrid(page):
    print("\n[TAHAP 1] Memulai ekstraksi card & mengambil data objek...")

    cards_locator = page.locator(".kost-rc")
    if cards_locator.count() == 0:
        cards_locator = page.locator('[data-testid="nominatimRoomCard"]')

    total_cards = cards_locator.count()
    print(f"Jumlah card yang ditemukan di browser UI: {total_cards}")

    scraped_data = []

    for index in range(total_cards):
        try:
            print(f"\n--> Memproses Card [{index + 1}/{total_cards}]")

            # Ambil locator segar berdasarkan urutan indeks
            current_card = cards_locator.nth(index)

            # Ekstrak data teks dari UI Card
            nama_loc = current_card.locator(".rc-info__name, .kost-rc__info span").first
            nama = nama_loc.text_content().strip() if nama_loc.count() > 0 else f"Kos Idx {index}"

            harga_loc = current_card.locator(".rc-overview__label, .bg-c-label, .rc-price__text").first
            harga_card = harga_loc.text_content().strip() if harga_loc.count() > 0 else None

            # Tangkap pembukaan tab baru
            context = page.context
            with context.expect_page() as new_page_info:
                current_card.click()
            
            detail_page = new_page_info.value
            
            # Tunggu JavaScript di tab baru selesai memuat objek globalnya
            detail_page.wait_for_load_state("domcontentloaded")
            url_detail = detail_page.url
            print(f"    Berhasil mendapatkan URL Detail: {url_detail}")

            # --- AMBIL DATA LANGSUNG DARI MEMORI TAB BARU (PENGGANTI REQUESTS) ---
            print("    [Engine] Mengekstrak window.detail langsung dari browser memory...")
            
            # evaluate() memanggil variabel javascript di tab tersebut dan mengembalikannya ke Python
            obj_kos = detail_page.evaluate("() => window.detail")
            obj_harga = detail_page.evaluate("() => window.price_card_info")

            # Siapkan penampung data detail
            data_backend = {
                "latitude": None,
                "longitude": None,
                "jarak_unud_jimbaran_km": None,
                "jarak_unud_sudirman_km": None,
                "harga_real_detail": None
            }

            if obj_kos:
                kos_lat = obj_kos.get("latitude")
                kos_lon = obj_kos.get("longitude")
                
                data_backend["latitude"] = kos_lat
                data_backend["longitude"] = kos_lon

                # Hitung jarak Haversine ke UNUD jika koordinatnya ada
                if kos_lat is not None and kos_lon is not None:
                    j_jimbaran = hitung_jarak_haversine(kos_lat, kos_lon, REKTORAT_UNUD[0], REKTORAT_UNUD[1])
                    j_sudirman = hitung_jarak_haversine(kos_lat, kos_lon, UNUD_SUDIRMAN[0], UNUD_SUDIRMAN[1])
                    data_backend["jarak_unud_jimbaran_km"] = round(j_jimbaran, 2)
                    data_backend["jarak_unud_sudirman_km"] = round(j_sudirman, 2)
                    print(f"    [Sukses] Koordinat didapat. Jarak ke Jimbaran: {data_backend['jarak_unud_jimbaran_km']} km")

                if ENABLE_POI_ENRICHMENT:
                    poi_distances = enrich_nearest_poi_distances(kos_lat, kos_lon, debug=True)
                    data_backend.update(poi_distances)

            if obj_harga and "price" in obj_harga:
                h_bulan = obj_harga["price"].get("price_monthly", {})
                if h_bulan:
                    data_backend["harga_real_detail"] = f"{h_bulan.get('currency_symbol')}{h_bulan.get('price')}/{h_bulan.get('rent_type_unit')}"

            # Tutup tab detail karena datanya sudah aman di variabel Python
            detail_page.close()

            # Gabungkan data dasar dari card dengan data objek dari tab dalam
            item_kos = {
                "nama_kost": nama,
                "harga_card": harga_card,
                "url_detail": url_detail,
            }
            item_kos.update(data_backend)

            scraped_data.append(item_kos)
            
            # Jeda pendek demi kestabilan browser sebelum lanjut card berikutnya
            page.wait_for_timeout(300)

        except Exception as e:
            print(f"    Gagal memproses card pada indeks {index} karena: {e}")
            try:
                # Amankan jika ada tab detail yang bocor/lupa tertutup saat terjadi error
                if len(page.context.pages) > 1:
                    page.context.pages[-1].close()
            except:
                pass
            continue

    return scraped_data


def run_main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)

        # Kelola cookies state agar tidak memicu deteksi bot berlebih
        if os.path.exists(SESSION_FILE):
            context = browser.new_context(
                storage_state=SESSION_FILE, user_agent=HEADERS["User-Agent"]
            )
        else:
            context = browser.new_context(user_agent=HEADERS["User-Agent"])

        # Blokir aset gambar pada browser utama agar performa klik cepat & hemat bandwidth
        context.route(
            "**/*",
            lambda route: (
                route.abort()
                if route.request.resource_type == "image"
                else route.continue_()
            ),
        )

        page = context.new_page()

        # Target Pencarian (Bisa kamu ganti parameter lokasinya)
        target_url = f"{BASE_URL}ubud-kabupaten-gianyar-bali-indonesia/all/bulanan/0-15000000/"
        print(f"Membuka link pencarian utama: {target_url}")

        page.goto(target_url)
        page.wait_for_timeout(3000)

        # Proses melumat tombol 'Lihat lebih banyak lagi' sampai habis di layar browser
        show_more = page.get_by_text("Lihat lebih banyak lagi", exact=True)
        print("Membuka seluruh daftar halaman kost...")
        while True:
            if show_more.is_visible():
                try:
                    show_more.click()
                    page.wait_for_timeout(1500)
                except:
                    break
            else:
                break

        # Eksekusi fungsi pencarian hybrid
        hasil_akhir = scrape_pencarian_hybrid(page)

        # [TAHAPAkhir] Simpan data gabungan ke file JSON
        print(f"\n[TAHAP KELUARAN] Menyimpan semua data ke {OUTPUT_FILE}...")
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(hasil_akhir, f, ensure_ascii=False, indent=4)

        print(
            f"\n Process Hybrid Selesai! Berhasil mengamankan {len(hasil_akhir)} data kos ber-geolocation."
        )

        context.storage_state(path=SESSION_FILE)
        context.close()
        browser.close()


if __name__ == "__main__":
    run_main()