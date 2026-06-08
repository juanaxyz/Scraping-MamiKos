import json
import os
from playwright.sync_api import sync_playwright
from mamikos_scraper import inspect_room_detail, open_card_detail, search_by_locations

BASE_URL = "https://mamikos.com/cari/"
SESSION_FILE = "mamikos_session.json"
OUTPUT_FILE = "mamikos_data.json"
OUTPUT_FILE_DETAIL = "mamikos_data_detail.json"


def block_assets(route):
    if route.request.resource_type == "image":
        route.abort()  # Batalkan request jika berupa CSS
    else:
        route.continue_()  # Lanjutkan jika bukan CSS (seperti dokumen HTML, JS, dll)


if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)

        if os.path.exists(SESSION_FILE):
            print("Menggunakan session yang tersimpan...")
            context = browser.new_context(
                storage_state=SESSION_FILE,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )
        else:
            print("Session tidak ditemukan. Membuat session baru...")
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        # --- BLOKIR CSS ---
        # Fungsi interceptor untuk mengecek tipe data request

        context.route("**/*", block_assets)
        # --------------------------

        hasil_scrape, pages = search_by_locations(
            location="ubud-kabupaten-gianyar-bali-indonesia",
            context=context,
            debug=True,
        )
        cards = pages.locator(".kost-rc")
        jumlah_cards = cards.count()
        print(f"Jumlah card yang ditemukan: {jumlah_cards}")

        # untuk setiap card kita ekstrak data menggunakan fungsi inspect_room_detail
        hasil_detail = []
        for index in range(jumlah_cards):
            try:
                card = cards.nth(index)
                detail_url = open_card_detail(pages, card, debug=True)
                if detail_url:
                    print(f"\nMemproses card dengan URL: {detail_url}")
                    detail = inspect_room_detail(detail_url)
                    if detail:
                        hasil_detail.append(detail)
                    pages.go_back(wait_until="networkidle")
                    pages.wait_for_timeout(1000)
                else:
                    print("Gagal menemukan URL pada card ini.")
            except Exception as e:
                print(f"Error saat memproses card: {e}")

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(hasil_scrape, f, ensure_ascii=False, indent=4)
        with open(OUTPUT_FILE_DETAIL, "w", encoding="utf-8") as f:
            json.dump(hasil_detail, f, ensure_ascii=False, indent=4)
        context.storage_state(path=SESSION_FILE)
        context.close()
        browser.close()
        print("Browser ditutup.")
