import re
import os

from playwright.sync_api import sync_playwright, Page, BrowserContext
import datetime
from datetime import date
from dotenv import load_dotenv

load_dotenv()

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

def set_preferences(page, columns):
    page.get_by_role("button").filter(has_text="Metrics").click()

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

def scrape_category(page: Page, category: str, url: str, columns: list[str]) -> list[dict]:
    """Navigates to a category URL, sets preferences, and extracts game data."""
    print(f"Scraping category: {category}...")
    page.goto(url)
    set_preferences(page, columns)
    return extract_games(page, category)

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        
        # Force a fresh login every time
        context = browser.new_context()
        page = context.new_page()
        login(page)

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
        for category, url in categories_to_scrape.items():
            games = scrape_category(page, category, url, columns)
            all_games_data.extend(games) # Flatten the list

        browser.close()
        print(f"Scraping complete. Extracted data for {len(all_games_data)} games.")
        print(all_games_data[1])
        return all_games_data

if __name__ == "__main__":
    main()