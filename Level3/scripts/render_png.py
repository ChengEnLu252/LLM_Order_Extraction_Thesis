from pathlib import Path
from playwright.sync_api import sync_playwright


BASE_DIR = Path(__file__).resolve().parent.parent
HTML_DIR = BASE_DIR / "dataset" / "order_level3_html"
OUTPUT_DIR = BASE_DIR / "dataset" / "order_level3_images_clean"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def render_html_to_png(html_path: Path) -> None:
    """
    將單一 HTML 檔渲染成 clean PNG。
    """
    html_uri = html_path.resolve().as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 1200, "height": 1700},
            device_scale_factor=2
        )

        page.goto(html_uri)
        page.screenshot(
            path=str(OUTPUT_DIR / f"{html_path.stem}.png"),
            full_page=True
        )
        browser.close()

    print(f"[OK] PNG rendered: {html_path.stem}.png")


def main() -> None:
    html_files = sorted(HTML_DIR.glob("*.html"))

    if not html_files:
        print("[WARN] No HTML files found.")
        return

    print(f"[INFO] Found {len(html_files)} HTML files.")

    for html_file in html_files:
        render_html_to_png(html_file)

    print(f"\nDone. Rendered {len(html_files)} clean PNG files.")


if __name__ == "__main__":
    main()