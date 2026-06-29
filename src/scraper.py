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

            # Remove overlays before each card click
            page.evaluate("""() => {
                document.querySelectorAll(
                    '[class*="cookie"], [class*="consent"], [class*="overlay"], [class*="modal"], [class*="popup"], [class*="banner"]'
                ).forEach(el => el.remove());
            }""")

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

            # Skip if this kos name already scraped (resume support)
            if nama and not nama.startswith("Kos Idx") and saver.has_name(nama):
                print(f"    [Skip] '{nama}' sudah ada di JSON, lanjut ke card berikutnya...")
                continue

            current_card.scroll_into_view_if_needed()
            page.wait_for_timeout(300)

            # Click card to open detail page in new tab
            # Use name element specifically - it reliably triggers new tab
            click_target = current_card.locator(".rc-info__name, .rc-info__name span").first
            if click_target.count() == 0:
                click_target = current_card  # fallback to whole card

            try:
                ctx = page.context
                with ctx.expect_page(timeout=15000) as new_page_info:
                    click_target.click()
                detail_page = new_page_info.value
                detail_page.wait_for_load_state("domcontentloaded")
                detail_page.wait_for_timeout(2000)
            except Exception as click_err:
                err_str = str(click_err)
                if "timeout" in err_str.lower():
                    print(f"    [Warning] New tab timeout, trying JS click...")
                    try:
                        ctx = page.context
                        with ctx.expect_page(timeout=15000) as new_page_info:
                            click_target.evaluate("el => el.click()")
                        detail_page = new_page_info.value
                        detail_page.wait_for_load_state("domcontentloaded")
                        detail_page.wait_for_timeout(2000)
                    except Exception:
                        print(f"    [Error] Gagal membuka detail page, skip card ini")
                        continue
                else:
                    print(f"    [Error] Click failed: {click_err}")
                    continue
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
            error_msg = str(e)
            if "intercepts pointer events" in error_msg:
                # Log overlay info for debugging
                try:
                    overlay_info = page.evaluate("""() => {
                        const els = document.elementsFromPoint(window.innerWidth/2, window.innerHeight/2);
                        return els.slice(0, 5).map(el => ({
                            tag: el.tagName,
                            id: el.id,
                            classes: el.className?.toString()?.substring(0, 80)
                        }));
                    }""")
                    print(f"    [Debug] Overlay detected: {overlay_info}")
                    # Try to remove overlay again
                    page.evaluate("""() => {
                        document.querySelectorAll(
                            '[class*="cookie"], [class*="consent"], [class*="overlay"], [class*="modal"], [class*="popup"], [class*="banner"]'
                        ).forEach(el => el.remove());
                    }""")
                    print("    [Overlay] Removed overlay, retrying next card...")
                except Exception:
                    pass
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
        browser = p.chromium.launch(headless=True, slow_mo=50)

        context = browser.new_context(
            storage_state=SESSION_FILE if os.path.exists(SESSION_FILE) else None,
            user_agent=HEADERS["User-Agent"],
        )

        # Do NOT block images during page load - causes route handler deadlock
        # Images will be loaded but we don't care about them

        page = context.new_page()

        target_url = (
            f"{BASE_URL}"
            "universitas-udayana-kampus-sudirman-universitas-udayana-kampus-sudirman-dangin-puri-klod-denpasar-city-bali-indonesia/all/bulanan/0-15000000?keyword=Universitas%20Udayana%20-%20Kampus%20Sudirman&suggestion_type=search&rent=2&sort=price,-&price=0-20000000&singgahsini=0"
        )
        print(f"Membuka: {target_url}")

        # Navigate with retry (network can be flaky)
        for attempt in range(3):
            try:
                page.goto(target_url, timeout=60000, wait_until="domcontentloaded")
                print(f"    [OK] Halaman dimuat (attempt {attempt + 1})")
                break
            except Exception as e:
                print(f"    [Warning] Attempt {attempt + 1} failed: {e}")
                if attempt == 2:
                    print("    [Error] Gagal navigasi setelah 3 percobaan")
                    context.close()
                    browser.close()
                    return
                page.wait_for_timeout(3000)

        # Wait for Vue to render cards (up to 30s)
        print("    [Wait] Menunggu cards muncul...")
        try:
            page.wait_for_selector(".kost-rc", timeout=30000)
            print("    [OK] Cards ditemukan!")
        except Exception:
            print("    [Warning] .kost-rc tidak ditemukan, coba selector lain...")
            try:
                page.wait_for_selector("[data-testid='roomCard']", timeout=10000)
                print("    [OK] Cards ditemukan via data-testid!")
            except Exception:
                print("    [Error] Tidak ada cards yang ditemukan")
                context.close()
                browser.close()
                return

        # Dismiss popup/overlay (cookie consent, promo banner, etc.)
        dismiss_selectors = [
            'button:has-text("Accept")',
            'button:has-text("Setuju")',
            'button:has-text("Terima")',
            'button:has-text("OK")',
            'button:has-text("Got it")',
            'button:has-text("Mengerti")',
            '[data-testid="cookie-consent-accept"]',
            '#onetrust-accept-btn-handler',
            '[aria-label="close"]',
            '[aria-label="Close"]',
        ]
        for sel in dismiss_selectors:
            try:
                btn = page.locator(sel).first
                if btn.is_visible(timeout=500):
                    btn.click(timeout=1000)
                    print(f"    [Overlay] Dismissed: {sel}")
                    page.wait_for_timeout(500)
                    break
            except Exception:
                continue

        # Remove fixed/absolute overlays via JS
        page.evaluate("""() => {
            document.querySelectorAll(
                '[class*="cookie"], [class*="consent"], [class*="overlay"], [class*="modal"], [class*="popup"], [class*="banner"]'
            ).forEach(el => {
                const pos = getComputedStyle(el).position;
                if (pos === 'fixed' || pos === 'absolute') {
                    el.remove();
                }
            });
        }""")
        print("    [Overlay] Cleaned up fixed/absolute overlays via JS")

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
