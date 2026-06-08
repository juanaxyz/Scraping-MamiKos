import ast
import json
import math
import re

import requests

BASE_URL = "https://mamikos.com/cari/"
ROOM_DETAIL_BASE_URL = "https://mamikos.com"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
DEFAULT_HEADERS = {
    "User-Agent": DEFAULT_USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

# Titik Koordinat Kampus UNUD [Latitude, Longitude]
REKTORAT_UNUD = [-8.798256245751867, 115.17249471428231]
UNUD_SUDIRMAN = [-8.673060417640015, 115.21901203994138]


def build_search_url(
    location="universitas-udayana-jimbaran-kabupaten-badung-bali-indonesia",
    type="all",
    waktu="bulanan",
    price="0-15000000",
):
    return f"{BASE_URL}{location}/{type}/{waktu}/{price}/"


def normalize_room_url(url_detail):
    if url_detail and not url_detail.startswith("http"):
        return f"{ROOM_DETAIL_BASE_URL}{url_detail}"
    return url_detail


def get_text_or_none(locator):
    return locator.text_content().strip() if locator.count() > 0 else None


def get_card_detail_url(page, card, debug=False):
    url_candidates = [
        ("a[href]", "href"),
        ("[href]", "href"),
        ("[data-href]", "data-href"),
        ("[data-url]", "data-url"),
        ("[data-link]", "data-link"),
    ]

    for selector, attribute_name in url_candidates:
        locator = card.locator(selector)
        if locator.count() > 0:
            raw_url = locator.first.get_attribute(attribute_name)
            if raw_url:
                return normalize_room_url(raw_url)

    onclick_value = card.get_attribute("onclick")
    if onclick_value:
        match_url = re.search(r"['\"](\/[^'\"]+)['\"]", onclick_value)
        if match_url:
            return normalize_room_url(match_url.group(1))

    if debug:
        print("URL detail tidak ditemukan di atribut card. Mencoba klik card...")

    detail_url = open_card_detail(page, card, debug=debug)
    if detail_url:
        page.go_back(wait_until="networkidle")
        page.wait_for_timeout(1000)

    return detail_url


def scrape_card_data(page, debug=False):
    if debug:
        print("Mulai mengekstrak data dari card...")

    cards = page.locator("div.room-list__card").all()
    if debug:
        print(f"Jumlah card yang ditemukan: {len(cards)}")

    scraped_data = []
    for index, card in enumerate(cards, start=1):
        try:
            if debug:
                print(f"\n[Card {index}] Memulai ekstraksi")

            nama = get_text_or_none(card.locator(".rc-info__name"))
            tipe = get_text_or_none(card.locator(".rc-overview__label"))
            lokasi = get_text_or_none(card.locator(".rc-info__location"))
            harga = get_text_or_none(card.locator(".rc-price__text"))
            tipe_sewa = get_text_or_none(card.locator(".rc-price__type"))

            rating_text = get_text_or_none(card.locator(".rc-overview__rating-text"))
            rating = float(rating_text) if rating_text else None

            sisa_kamar = get_text_or_none(card.locator(".bg-u-text-red-600"))
            total_view = get_text_or_none(card.locator(".rc-photo__fomo-badge p"))

            fasilitas_elements = card.locator(
                '[data-testid="roomCardFacilities-facility"] span:not(.rc-facilities_divider)'
            ).all()
            fasilitas = [
                fasilitas.text_content().strip()
                for fasilitas in fasilitas_elements
                if fasilitas.text_content().strip() != ""
            ]

            url_detail = get_card_detail_url(page, card, debug=debug)

            item = {
                "nama_kost": nama,
                "tipe_kost": tipe,
                "lokasi": lokasi,
                "harga": harga,
                "tipe_sewa": tipe_sewa,
                "rating": rating,
                "sisa_kamar": sisa_kamar,
                "total_view": total_view,
                "fasilitas": fasilitas,
                "url_detail": url_detail,
            }

            if debug:
                print(
                    "[Card {0}] nama={1!r}, harga={2!r}, lokasi={3!r}, url={4!r}".format(
                        index, nama, harga, lokasi, url_detail
                    )
                )

            scraped_data.append(item)
        except Exception as exc:
            if debug:
                print(f"[Card {index}] Gagal ekstrak card: {exc}")
            continue

    return scraped_data


def block_assets(route):
    if route.request.resource_type == "image":
        route.abort()
    else:
        route.continue_()


def wait_for_room_cards(page, timeout_ms=10000):
    page.wait_for_selector("div.room-list__card", timeout=timeout_ms)


def open_search_page(
    context, location, type="all", waktu="bulanan", price="0-15000000"
):
    url = build_search_url(location=location, type=type, waktu=waktu, price=price)
    page = context.new_page()
    page.goto(url)
    return page, url


def expand_show_more(page, debug=False):
    show_more = page.get_by_text("Lihat lebih banyak lagi", exact=True)
    while True:
        if show_more.is_visible():
            if debug:
                print("Tombol ditemukan. Mengklik tombol 'Lihat lebih banyak lagi'...")
            show_more.click()
            try:
                page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                pass
            page.wait_for_timeout(1500)
            if debug:
                print("Data baru selesai dimuat. Memeriksa tombol kembali...")
        else:
            if debug:
                print("Semua data sudah berhasil dimuat.")
            break


def open_card_detail(page, card, timeout_ms=10000, debug=False):
    current_url = page.url
    card.scroll_into_view_if_needed()
    card.click(force=True)

    try:
        page.wait_for_load_state("networkidle", timeout=timeout_ms)
    except Exception:
        page.wait_for_timeout(1500)

    detail_url = page.url
    if detail_url == current_url:
        if debug:
            print("Klik card tidak mengubah URL halaman.")
        return None

    if debug:
        print(f"Detail page terbuka: {detail_url}")

    return detail_url


def search_by_locations(
    context,
    location="universitas-udayana-jimbaran-kabupaten-badung-bali-indonesia",
    type="all",
    waktu="bulanan",
    price="0-15000000",
    output_file=None,
    session_file=None,
    debug=False,
):
    page, url = open_search_page(
        context=context,
        location=location,
        type=type,
        waktu=waktu,
        price=price,
    )

    if debug:
        print(f"Searching URL: {url}")
        print("Page berhasil di load.")

    page.wait_for_timeout(2000)
    expand_show_more(page, debug=debug)

    if session_file:
        context.storage_state(path=session_file)
        if debug:
            print(f"Session berhasil diperbarui di {session_file}")

    hasil_scrape = scrape_card_data(page, debug=debug)

    if output_file:
        with open(output_file, "w", encoding="utf-8") as file_handle:
            json.dump(hasil_scrape, file_handle, ensure_ascii=False, indent=4)

    return hasil_scrape, page


def hitung_jarak_haversine(lat1, lon1, lat2, lon2):
    """Menghitung jarak lurus antara dua titik koordinat dalam satuan kilometer (km)."""
    radius_bumi = 6371.0

    rad_lat1 = math.radians(lat1)
    rad_lon1 = math.radians(lon1)
    rad_lat2 = math.radians(lat2)
    rad_lon2 = math.radians(lon2)

    dlat = rad_lat2 - rad_lat1
    dlon = rad_lon2 - rad_lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(rad_lat1) * math.cos(rad_lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return radius_bumi * c


def extract_detail_from_html(html_content):
    match_detail = re.search(r"var\s+detail\s*=\s*(\{.*?\});", html_content, re.DOTALL)
    match_price = re.search(
        r"var\s+price_card_info\s*=\s*(\{.*?\});", html_content, re.DOTALL
    )

    detail_data = (
        _parse_js_object_literal(match_detail.group(1)) if match_detail else None
    )
    price_data = _parse_js_object_literal(match_price.group(1)) if match_price else None

    return detail_data, price_data


def _parse_js_object_literal(raw_object):
    try:
        return json.loads(raw_object)
    except json.JSONDecodeError:
        normalized = raw_object
        normalized = re.sub(
            r"(?<![\w\"'])((?:[A-Za-z_][$\w]*))\s*:", r'"\1":', normalized
        )
        normalized = normalized.replace("null", "None")
        normalized = normalized.replace("true", "True")
        normalized = normalized.replace("false", "False")
        normalized = normalized.replace("undefined", "None")
        normalized = normalized.replace("\\/", "/")
        return ast.literal_eval(normalized)


def fetch_room_detail(url, timeout=10, headers=None):
    request_headers = headers or DEFAULT_HEADERS
    response = requests.get(url, headers=request_headers, timeout=timeout)
    response.raise_for_status()
    return response.text


def parse_room_detail(url, headers=None, timeout=10):
    html_content = fetch_room_detail(url, headers=headers, timeout=timeout)
    return extract_detail_from_html(html_content)


def inspect_room_detail(url):
    """Fetch and print room details, then return a dict with the extracted data.
    Returns:
        dict | None: payload JSON-serializable yang berisi detail kos dan harga, atau None on error.
    """
    print(f"Mengirim HTTP Request ke: {url} ...")

    try:
        data_kos, data_harga = parse_room_detail(url, headers=DEFAULT_HEADERS)

        print("\n" + "=" * 55)
        print("HASIL EKSTRAK VIA HTTP REQUEST (TANPA BROWSER)")
        print("=" * 55)

        if data_kos:
            kos_lat = data_kos.get("latitude")
            kos_lon = data_kos.get("longitude")

            print(f"Nama Kos        : {data_kos.get('room_title')}")
            print(f"Latitude        : {kos_lat}")
            print(f"Longitude       : {kos_lon}")

            if kos_lat and kos_lon:
                jarak_rektorat = hitung_jarak_haversine(
                    kos_lat, kos_lon, REKTORAT_UNUD[0], REKTORAT_UNUD[1]
                )
                jarak_sudirman = hitung_jarak_haversine(
                    kos_lat, kos_lon, UNUD_SUDIRMAN[0], UNUD_SUDIRMAN[1]
                )

                print("\n--- Analisis Jarak ke Kampus UNUD ---")
                print(f"Jarak ke UNUD Bukit Jimbaran : {jarak_rektorat:.2f} km")
                print(f"Jarak ke UNUD Sudirman       : {jarak_sudirman:.2f} km")
        else:
            print("Gagal menemukan pola 'var detail' di dalam HTML.")

        harga_bulanan = None
        if data_harga and "price" in data_harga:
            harga_bulanan = data_harga["price"].get("price_monthly", {})
            print(
                f"\nHarga per Bulan : {harga_bulanan.get('currency_symbol')}{harga_bulanan.get('price')}/{harga_bulanan.get('rent_type_unit')}"
            )

        print("=" * 55)

        hasil_detail = {
            "url": url,
            "nama_kost": data_kos.get("room_title") if data_kos else None,
            "latitude": data_kos.get("latitude") if data_kos else None,
            "longitude": data_kos.get("longitude") if data_kos else None,
            "jarak_ke_unud_bukit_jimbaran_km": None,
            "jarak_ke_unud_sudirman_km": None,
            "harga_per_bulan": harga_bulanan,
            "data_kos": data_kos,
            "data_harga": data_harga,
        }

        if data_kos:
            kos_lat = data_kos.get("latitude")
            kos_lon = data_kos.get("longitude")
            if kos_lat and kos_lon:
                hasil_detail["jarak_ke_unud_bukit_jimbaran_km"] = (
                    hitung_jarak_haversine(
                        kos_lat, kos_lon, REKTORAT_UNUD[0], REKTORAT_UNUD[1]
                    )
                )
                hasil_detail["jarak_ke_unud_sudirman_km"] = hitung_jarak_haversine(
                    kos_lat, kos_lon, UNUD_SUDIRMAN[0], UNUD_SUDIRMAN[1]
                )

        return hasil_detail
    except Exception as e:
        print(f"Terjadi error saat request: {e}")
        return None
