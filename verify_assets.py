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
        response = await page.goto(url, wait_until="load", timeout=10000)

        if response.status != 200:
            print(f"  - FAILURE: Received status {response.status} for {path}")
            return False

        await asyncio.sleep(1) # Wait for any late requests

        found_assets = []
        for req_url in requests:
            if "?v=" in req_url:
                found_assets.append(req_url)

        print(f"Summary for {path}: SUCCESS")
        print(f"  - Found {len(found_assets)} versioned assets.")
        return True

    except Exception as e:
        print(f"Error for {path}: {e}")
        return False
    finally:
        await context.close()

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            paths = ["/", "/links.html", "/profiles.html", "/404.html"]
            results = []
            for path in paths:
                success = await verify_page(browser, path)
                results.append(success)

            if all(results):
                print("\nAll pages verified successfully.")
            else:
                print("\nSome pages failed verification.")
                exit(1)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
