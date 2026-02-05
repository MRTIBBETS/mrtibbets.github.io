import asyncio
from playwright.async_api import async_playwright

async def verify_index(browser):
    page = await browser.new_page()
    try:
        # Track requests
        requests = []
        page.on("request", lambda request: requests.append(request.url))

        print("Navigating to index.html...")
        await page.goto("http://localhost:8080/")

        found_assets = []
        found_common_js = False

        for url in requests:
            if "?v=assets1" in url:
                found_assets.append(url)
                print(f"Found versioned asset: {url}")
            if "common.js?v=" in url:
                found_common_js = True
                print(f"Found common.js with version: {url}")

        if len(found_assets) == 0:
            print("WARNING: No v=assets1 assets found.")

        if not found_common_js:
            print("WARNING: common.js with version query not found.")
        else:
            print("SUCCESS: common.js found with version.")

        await page.screenshot(path="index_verification.png")
    finally:
        await page.close()

async def verify_links(browser):
    page = await browser.new_page()
    try:
        print("Navigating to links.html...")
        await page.goto("http://localhost:8080/links.html")
        await page.screenshot(path="links_verification.png")
    finally:
        await page.close()

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            await asyncio.gather(
                verify_index(browser),
                verify_links(browser)
            )
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
