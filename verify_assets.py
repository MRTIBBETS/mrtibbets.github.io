import asyncio
from playwright.async_api import async_playwright
import os

async def check_preconnects(page, page_name):
    preconnects = await page.query_selector_all('link[rel="preconnect"]')
    hrefs = await asyncio.gather(*[link.get_attribute('href') for link in preconnects])
    for href in hrefs:
        if href and "alexandertibbets.com" in href:
             print(f"FAILURE: Redundant preconnect to origin found in {page_name}: {href}")
             raise Exception(f"Redundant preconnect to origin found in {page_name}")
        elif href:
             print(f"Verified preconnect in {page_name}: {href}")

async def verify_index(browser):
    page = await browser.new_page()
    path = "/"
    url = f"http://localhost:8080{path}"
    try:
        # Track requests
        requests = []
        page.on("request", lambda request: requests.append(request.url))

        print(f"Navigating to {path}...")
        # waitUntil="domcontentloaded" might be faster, but we need to ensure assets are requested.
        # "load" is safer for asset verification.
        await page.goto(url, wait_until="load")

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
