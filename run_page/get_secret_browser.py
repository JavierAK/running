import re

import garth
from playwright.sync_api import sync_playwright

print("Launching interactive browser...")

with sync_playwright() as p:
    # Launch visible Chromium window
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    # Navigate to sign-in page
    page.goto("https://connect.garmin.com/signin")

    print("\n=======================================================")
    print("PLEASE LOG IN TO GARMIN IN THE CHROMIUM WINDOW.")
    print("Complete any 2FA or CAPTCHA if prompted.")
    print("=======================================================\n")

    # Wait until the URL changes to the main dashboard / modern page
    page.wait_for_url(re.compile(r"connect\.garmin\.com/modern"), timeout=120000)
    print("Login detected! Extracting session tokens...")

    cookies = context.cookies()
    browser.close()

# Convert cookies to garth session format
for cookie in cookies:
    garth.client.sess.cookies.set(
        cookie["name"], cookie["value"], domain=cookie["domain"]
    )

secret_json = garth.client.dumps()

print("\n================ GARMIN SECRET STRING START ================")
print(secret_json)
print("================= GARMIN SECRET STRING END =================\n")
