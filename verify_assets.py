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

        # Check for versioned assets
        # Note: browser might not request og:image, but it requests favicon.
        # index.html has: <link rel="icon" ... href="/assets/images/favicon.svg?v=assets1">

        found_assets = []
        for url in requests:
            if "?v=assets1" in url:
                found_assets.append(url)
                print(f"Found versioned asset: {url}")

        if len(found_assets) == 0:
            print("WARNING: No versioned assets found in requests. Check if browser is requesting them.")

        await page.screenshot(path="/home/jules/verification/index_verification.png")
    finally:
        await page.close()

async def verify_links(browser):
    page = await browser.new_page()
    try:
        print("Navigating to links.html...")
        await page.goto("http://localhost:8080/links.html")
        await page.screenshot(path="/home/jules/verification/links_verification.png")
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
