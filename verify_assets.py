import asyncio
from playwright.async_api import async_playwright

async def check_preconnects(page, page_name):
    preconnects = await page.query_selector_all('link[rel="preconnect"]')
    for link in preconnects:
        href = await link.get_attribute('href')
        if href and "alexandertibbets.com" in href:
             print(f"FAILURE: Redundant preconnect to origin found in {page_name}: {href}")
             raise Exception(f"Redundant preconnect to origin found in {page_name}")
        elif href:
             print(f"Verified preconnect in {page_name}: {href}")

async def verify_index(browser):
    page = await browser.new_page()
    try:
        # Track requests
        requests = []
        page.on("request", lambda request: requests.append(request.url))

        print("Navigating to index.html...")
        await page.goto("http://localhost:8080/")

        await check_preconnects(page, "index.html")

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
        await check_preconnects(page, "links.html")
        await page.screenshot(path="/home/jules/verification/links_verification.png")
    finally:
        await page.close()

async def verify_profiles(browser):
    page = await browser.new_page()
    try:
        print("Navigating to profiles.html...")
        await page.goto("http://localhost:8080/profiles.html")
        await check_preconnects(page, "profiles.html")
        await page.screenshot(path="/home/jules/verification/profiles_verification.png")
    finally:
        await page.close()

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            await asyncio.gather(
                verify_index(browser),
                verify_links(browser),
                verify_profiles(browser)
            )
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
