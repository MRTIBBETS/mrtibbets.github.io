import asyncio
from playwright.async_api import async_playwright
import os

async def verify_page(browser, path):
    context = await browser.new_context()
    # Abort external requests
    await context.route("**/*", lambda route:
        route.abort() if not (route.request.url.startswith("http://localhost:8080") or "favicon.ico" in route.request.url)
        else route.continue_()
    )

    page = await context.new_page()
    url = f"http://localhost:8080{path}"
    try:
        # Track requests
        requests = []
        page.on("request", lambda request: requests.append(request.url))

        print(f"Navigating to {url}...")
        await page.goto(url, wait_until="load", timeout=10000)
        await asyncio.sleep(1) # Wait for any late requests

        found_assets = []
        found_common_js = False

        for req_url in requests:
            if "?v=assets1" in req_url:
                found_assets.append(req_url)
            if "common.js?v=" in req_url:
                found_common_js = True

        print(f"Summary for {path}:")
        print(f"  - Found {len(found_assets)} versioned assets.")

        favicons = [u for u in requests if "favicon.ico" in u]
        if favicons:
            print(f"  - Favicon requests: {favicons}")
            if len(set(favicons)) > 1:
                print(f"  - FAILURE: Multiple DIFFERENT favicon.ico requests found: {set(favicons)}")
            else:
                print(f"  - SUCCESS: Consistent favicon request: {favicons[0]}")
        else:
             print(f"  - No favicon requests detected for {path} (common in headless)")

    except Exception as e:
        print(f"Error for {path}: {e}")
    finally:
        await context.close()

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            # Run sequentially to avoid log mixing
            await verify_page(browser, "/")
            await verify_page(browser, "/links.html")
            await verify_page(browser, "/profiles.html")
            await verify_page(browser, "/404.html")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
