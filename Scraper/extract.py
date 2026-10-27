import os

from playwright.sync_api import BrowserContext, Page, sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
import datetime
from datetime import date
from dotenv import load_dotenv

load_dotenv()

MENU_ATTEMPTS = 3

def login(page: Page):
    email = os.getenv("ROTRENDS_EMAIL")
    password = os.getenv("ROTRENDS_PASSWORD")

    if not email or not password:
        raise ValueError("ROTRENDS_EMAIL and ROTRENDS_PASSWORD environment variables must be set.")
    
    page.goto("https://rotrends.com/login")

    email_box = page.get_by_role("textbox", name="Email Address")
    email_box.wait_for(state="visible")
    email_box.click()

    page.wait_for_timeout(500)
    email_box.press_sequentially(email, delay=100)
    
    page.keyboard.press("Tab")
    page.wait_for_timeout(500)
    
    page.keyboard.insert_text(password)
    page.wait_for_timeout(500)

    page.keyboard.press("Enter")

    page.wait_for_url("https://rotrends.com/**", timeout=15000)
    page.wait_for_timeout(1000)
    
    print("Login successful.")

def open_metrics_menu(page, first_metric):
    button = page.get_by_role("button").filter(has_text="Metrics")
    first_option = page.locator(f'li[title="{first_metric}"]')
    for attempt in range(MENU_ATTEMPTS):
        if first_option.count() == 0:
            button.click()
        try:
            first_option.wait_for(state="attached", timeout=10000)
            return
        except PlaywrightTimeoutError:
            print(f"Metrics menu did not open (attempt {attempt + 1})")
    raise PlaywrightTimeoutError("Metrics menu never opened")

def set_preferences(page, columns):
    page.wait_for_selector(".ant-table-row")
    open_metrics_menu(page, columns[1])

    for metric in columns[1:-1]:
        option = page.locator(f'li[title="{metric}"]')

        option.wait_for(state="attached")

        class_list = option.get_attribute("class")

        if class_list and "ant-dropdown-menu-item-selected" not in class_list:
            option.click()
            page.wait_for_timeout(100) 

    print("All preferences set successfully!")

def extract_games(page, category):
    all_games = []

    page.wait_for_selector(".ant-table-row")

    header_elements = page.query_selector_all(".ant-table-thead th")
    
    headers = [th.inner_text().strip() for th in header_elements]

    games = page.query_selector_all(".ant-table-row")

    for game in games:
        try:
            cells = game.query_selector_all(".ant-table-cell")
            game_data = {}
            game_data["Category"] = category
            for i in range(len(cells)):
                if i < len(headers):
                    column_name = headers[i]

                    if column_name == "":
                        continue
                        
                    cell_value = cells[i].inner_text().strip()
                    game_data[column_name] = cell_value
            game_data["Date Extracted"] = datetime.datetime.now().strftime("%Y-%m-%d")
            all_games.append(game_data)
        except Exception as e:
            print(f"Error scraping game: {e}")
            continue

    return all_games

def save_diagnostics(page: Page, label: str):
    folder = os.getenv("DIAGNOSTICS_DIR")
    if not folder:
        return
    os.makedirs(folder, exist_ok=True)
    name = label.replace(" ", "_")
    page.screenshot(path=f"{folder}/{name}.png", full_page=True)
    with open(f"{folder}/{name}.txt", "w") as report:
        report.write(f"url: {page.url}\ntitle: {page.title()}\n\n")
        report.write(page.inner_text("body")[:3000])

def scrape_category(page: Page, category: str, url: str, columns: list[str]) -> list[dict]:
    """Navigates to a category URL, sets preferences, and extracts game data."""
    print(f"Scraping category: {category}...")
    try:
        page.goto(url)
        set_preferences(page, columns)
        return extract_games(page, category)
    except Exception:
        save_diagnostics(page, category)
        raise

MAX_ATTEMPTS = 4
PAUSE_BETWEEN_CATEGORIES_MS = 5000

def scrape_with_retries(page: Page, category: str, url: str, columns: list[str]):
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return scrape_category(page, category, url, columns)
        except Exception as e:
            print(f"{category}: attempt {attempt} of {MAX_ATTEMPTS} failed ({type(e).__name__})")
            page.wait_for_timeout(5000 * attempt)
    return None

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=os.getenv("HEADLESS", "").lower() == "true")
        
        context = browser.new_context()
        context.set_default_timeout(60000)
        page = context.new_page()
        # login(page)

        columns = ["Game Name", "Global Rank", "Global Rank Shift (1d)", "Global Rank Shift (1w)", "Global Rank Shift (1m)", "Avg CCU Rank (1d)", "Avg CCU Rank (7d)", "Avg CCU Rank (14d)", "Avg CCU Rank Shift (1d)", "Earning Rank", "Genre", "Sub Genre", "Visits", "Players (CCU)", "Platform Share", "Avg CCU (1d)", "Avg CCU (7d)", "Avg CCU (14d)", "Momentum (1d)", "Momentum (1w)", "Momentum (1m)", "Avg Session", "Favorites", "Rating", "Up Votes", "Down Votes", "Created", "Extract Date"]

        from dateutil.relativedelta import relativedelta

        dateToday = date.today().strftime("%Y-%m-%d")
        dateOneMonthAgo = (date.today() - relativedelta(months=1)).strftime("%Y-%m-%d")

        categories_to_scrape = {
            "Top Moving": "https://rotrends.com/games?page=1&page_size=100&sort=-rank_change_day&playing_min=500",
            "New and Rising": f"https://rotrends.com/games?page=1&page_size=100&sort=-rank_change_day&created_min={dateOneMonthAgo}T00%3A00%3A00.000Z",
            "New and Stable": f"https://rotrends.com/games?page=1&page_size=100&sort=-rap_14d&created_min={dateOneMonthAgo}T00%3A00%3A00.000Z",
            "Top 100": "https://rotrends.com/games?page=1&page_size=100&sort=-rank_change_day&rank_max=100",
            "Top by Earning": "https://rotrends.com/games?page=1&page_size=100&sort=-earning_rank",
            "Top by Players": "https://rotrends.com/games?page=1&page_size=100&sort=-players",
            "Top by Session": "https://rotrends.com/games?page=1&page_size=100&sort=-est_avg_session_duration_naive&playing_min=100"
        }

        all_games_data = []
        failed = []
        for category, url in categories_to_scrape.items():
            games = scrape_with_retries(page, category, url, columns)
            if games is None:
                failed.append(category)
                continue
            all_games_data.extend(games) # Flatten the list
            page.wait_for_timeout(PAUSE_BETWEEN_CATEGORIES_MS)

        if failed:
            print(f"Skipped categories after {MAX_ATTEMPTS} attempts: {', '.join(failed)}")
        if len(failed) > len(categories_to_scrape) // 2:
            browser.close()
            raise RuntimeError("Too many categories failed to scrape")

        browser.close()
        print(f"Scraping complete. Extracted data for {len(all_games_data)} games.")
        print(all_games_data[1])
        return all_games_data

if __name__ == "__main__":
    main()