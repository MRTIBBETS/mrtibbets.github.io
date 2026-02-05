import asyncio
from playwright.async_api import async_playwright
import os

# Ensure verification directory exists
os.makedirs("/home/jules/verification", exist_ok=True)

PAGES = ["/", "/links.html", "/profiles.html", "/404.html"]

async def verify_page(browser, path):
    page = await browser.new_page()
    url = f"http://localhost:8080{path}"
    try:
        # Track requests
        requests = []
        page.on("request", lambda request: requests.append(request.url))

        print(f"Navigating to {path}...")
        # waitUntil="domcontentloaded" might be faster, but we need to ensure assets are requested.
        # "load" is safer for asset verification.
        await page.goto(url, wait_until="load")

        # Check for versioned assets
        # We look for either assets1 (images) or common1 (js) as at least one should be present.
        found_assets = []
        for req_url in requests:
            if "?v=assets1" in req_url or "?v=common1" in req_url:
                found_assets.append(req_url)
                # print(f"Found versioned asset on {path}: {req_url}")

        if len(found_assets) == 0:
            print(f"WARNING: No versioned assets found in requests for {path}. Check if browser is requesting them.")
            # Print debug info only on failure
            print(f"DEBUG: All requests for {path} ({len(requests)}):")
            for r in requests:
                print(f" - {r}")
        else:
            print(f"SUCCESS: Found {len(found_assets)} versioned assets on {path}")

        # Generate screenshot name from path
        safe_name = path.replace("/", "").replace(".html", "")
        if not safe_name: safe_name = "index"

        screenshot_path = f"/home/jules/verification/{safe_name}_verification.png"
        await page.screenshot(path=screenshot_path)

    except Exception as e:
        print(f"ERROR verifying {path}: {e}")
    finally:
        await page.close()

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            tasks = [verify_page(browser, page) for page in PAGES]
            await asyncio.gather(*tasks)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
