import os
from playwright.sync_api import sync_playwright

from src.config import (
    BASE_URL,
    SESSION_FILE,
    OUTPUT_FILE,
    FAILED_POI_FILE,
    REKTORAT_UNUD,
    UNUD_SUDIRMAN,
    BANDARA_IGUSTI_NGURAH_RAI,
    HEADERS,
    ENABLE_POI_ENRICHMENT,
)
from src.utils.distance import hitung_jarak_haversine
from src.utils.parsers import ambil_kolom_analisis_dari_json, _safe_get_nested
from src.utils.poi import enrich_nearest_poi_distances
from src.utils.file_io import ProgressiveSaver, FailedPoiLogger


def scrape_pencarian_hybrid(
    page, saver: ProgressiveSaver, failed_logger: FailedPoiLogger
):
    print("\n[TAHAP 1] Memulai ekstraksi card & mengambil data objek...")

    cards_locator = page.locator(".kost-rc")
    if cards_locator.count() == 0:
        cards_locator = page.locator('[data-testid="nominatimRoomCard"]')

    total_cards = cards_locator.count()
    print(f"Jumlah card yang akan diproses: {total_cards}")

    scraped_data = []

    for index in range(total_cards):
        try:
            print(f"\n--> Memproses Card [{index + 1}/{total_cards}]")

            current_card = cards_locator.nth(index)

            nama_loc = current_card.locator(".rc-info__name, .kost-rc__info span").first
            nama = (
                nama_loc.text_content().strip()
                if nama_loc.count() > 0
                else f"Kos Idx {index}"
            )
            harga_loc = current_card.locator(
                ".rc-overview__label, .bg-c-label, .rc-price__text"
            ).first
            harga_card = (
                harga_loc.text_content().strip() if harga_loc.count() > 0 else None
            )

            ctx = page.context
            with ctx.expect_page() as new_page_info:
                current_card.click()

            detail_page = new_page_info.value
            detail_page.wait_for_load_state("domcontentloaded")
            url_detail = detail_page.url
            print(f"    URL Detail: {url_detail}")

            print("    [Engine] Mengekstrak window.detail dari browser memory...")
            obj_kos = detail_page.evaluate("() => window.detail")
            obj_harga = detail_page.evaluate("() => window.price_card_info")

            data_backend: dict = {
                "latitude": None,
                "longitude": None,
                "jarak_unud_jimbaran_km": None,
                "jarak_unud_sudirman_km": None,
                "jarak_bandara_ngurah_rai_km": None,
                "harga_real_detail": None,
            }

            if obj_kos:
                kos_lat = obj_kos.get("latitude")
                kos_lon = obj_kos.get("longitude")

                analysis = ambil_kolom_analisis_dari_json(obj_kos)
                data_backend.update(analysis)

                if kos_lat is not None and kos_lon is not None:
                    data_backend["jarak_unud_jimbaran_km"] = round(
                        hitung_jarak_haversine(kos_lat, kos_lon, *REKTORAT_UNUD), 2
                    )
                    data_backend["jarak_unud_sudirman_km"] = round(
                        hitung_jarak_haversine(kos_lat, kos_lon, *UNUD_SUDIRMAN), 2
                    )
                    data_backend["jarak_bandara_ngurah_rai_km"] = round(
                        hitung_jarak_haversine(
                            kos_lat, kos_lon, *BANDARA_IGUSTI_NGURAH_RAI
                        ),
                        2,
                    )
                    print(
                        f"    [Lokasi] Jimbaran: {data_backend['jarak_unud_jimbaran_km']} km | Sudirman: {data_backend['jarak_unud_sudirman_km']} km"
                    )

                    if ENABLE_POI_ENRICHMENT:
                        poi, failed_cats = enrich_nearest_poi_distances(
                            kos_lat,
                            kos_lon,
                            url_detail=url_detail,
                            debug=True,
                        )
                        data_backend.update(poi)

                        if failed_cats:
                            print(
                                f"    [POI] {len(failed_cats)} kategori gagal, dicatat ke {FAILED_POI_FILE}: {failed_cats}"
                            )
                            failed_logger.log(url_detail, kos_lat, kos_lon, failed_cats)

            if obj_harga:
                h_bulan = _safe_get_nested(obj_harga, "price", "price_monthly") or {}
                if h_bulan:
                    data_backend["harga_real_detail"] = (
                        f"{h_bulan.get('currency_symbol')}"
                        f"{h_bulan.get('price')}/"
                        f"{h_bulan.get('rent_type_unit')}"
                    )

            detail_page.close()

            item_kos = {
                "nama_kost": nama,
                "harga_card": harga_card,
                "url_detail": url_detail,
            }
            item_kos.update(data_backend)

            scraped_data.append(item_kos)
            saver.append_and_save(item_kos)
            print(f"    [Saved] Total tersimpan: {saver.count} item(s)")

            page.wait_for_timeout(300)

        except Exception as e:
            print(f"    [Error] Gagal memproses card {index}: {e}")
            try:
                pages = page.context.pages
                if len(pages) > 1:
                    pages[-1].close()
            except Exception:
                pass
            continue

    return scraped_data


def run_main():
    saver = ProgressiveSaver(OUTPUT_FILE)
    failed_logger = FailedPoiLogger(FAILED_POI_FILE)
    print(f"[Init] Data existing : {saver.count} item(s) di {OUTPUT_FILE}")
    print(f"[Init] Failed POI log: {failed_logger.count} entry di {FAILED_POI_FILE}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)

        context = browser.new_context(
            storage_state=SESSION_FILE if os.path.exists(SESSION_FILE) else None,
            user_agent=HEADERS["User-Agent"],
        )
        context.route(
            "**/*",
            lambda route: route.abort()
            if route.request.resource_type == "image"
            else route.continue_(),
        )

        page = context.new_page()

        target_url = (
            f"{BASE_URL}"
            "universitas-udayana-kampus-sudirman-universitas-udayana-kampus-sudirman-dangin-puri-klod-denpasar-city-bali-indonesia/all/bulanan/0-15000000?keyword=Universitas%20Udayana%20-%20Kampus%20Sudirman&suggestion_type=search&rent=2&sort=price,-&price=0-20000000&singgahsini=0"
        )
        print(f"Membuka: {target_url}")
        page.goto(target_url)
        page.wait_for_timeout(3000)

        print("Memperluas daftar kost...")
        show_more = page.get_by_text("Lihat lebih banyak lagi", exact=True)
        while True:
            if show_more.is_visible():
                try:
                    show_more.click()
                    page.wait_for_timeout(1500)
                except Exception:
                    break
            else:
                break

        hasil = scrape_pencarian_hybrid(page, saver, failed_logger)

        print(
            f"\n[Selesai] Scrape {len(hasil)} kost baru. Total di file: {saver.count}"
        )
        if failed_logger.count:
            print(
                f"[Info] {failed_logger.count} kost perlu retry POI → jalankan: python run.py retry"
            )

        context.storage_state(path=SESSION_FILE)
        context.close()
        browser.close()


if __name__ == "__main__":
    run_main()
