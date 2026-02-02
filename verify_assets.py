from playwright.sync_api import sync_playwright

def verify_assets(page):
    # Track requests
    requests = []
    page.on("request", lambda request: requests.append(request.url))

    print("Navigating to index.html...")
    page.goto("http://localhost:8080/")

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

    page.screenshot(path="/home/jules/verification/index_verification.png")

    print("Navigating to links.html...")
    page.goto("http://localhost:8080/links.html")
    page.screenshot(path="/home/jules/verification/links_verification.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            verify_assets(page)
        finally:
            browser.close()
