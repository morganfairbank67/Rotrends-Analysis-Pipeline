from playwright.sync_api import sync_playwright
import pandas as pd
import time

def scrape_rotrends(playwright):
    browser = playwright.chromium.launch_persistent_context(
        user_data_dir="C:/playwright",
        channel="chrome",
        headless=False
        no_viewport=True
    )

    page = browser.new_page()
    page_count = 0

    games = []

    while page_count < 1:
        print('Scraping page')

        