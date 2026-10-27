"""Download the official EBU Loudness Test Set v05 directly via Playwright."""
from pathlib import Path
from playwright.sync_api import sync_playwright


def download_ebu():
    out_dir = Path("datasets")
    out_dir.mkdir(parents=True, exist_ok=True)
    target_zip = out_dir / "ebu-loudness-test-setv05.zip"

    print("Connessione al portale EBU...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        page.goto("https://tech.ebu.ch/publications/ebu_loudness_test_set", timeout=60000)
        page.wait_for_timeout(2000)

        # Accept cookie banner if present
        try:
            cookie_btn = page.locator("#onetrust-accept-btn-handler, button:has-text('Accept'), button:has-text('I agree')")
            if cookie_btn.count() > 0 and cookie_btn.first.is_visible():
                print("Chiusura cookie banner OneTrust...")
                cookie_btn.first.click(timeout=5000)
                page.wait_for_timeout(1000)
        except Exception as e:
            print("Nessun cookie banner bloccante:", e)

        print("Avvio download di ebu-loudness-test-setv05.zip...")
        with page.expect_download(timeout=300000) as download_info:
            page.locator("a:has-text('OPEN FILE')").first.click(force=True)

        download = download_info.value
        download.save_as(str(target_zip))
        print(f"[OK] Download completato con successo: {target_zip} ({target_zip.stat().st_size / (1024*1024):.2f} MB)")
        browser.close()


if __name__ == "__main__":
    download_ebu()
