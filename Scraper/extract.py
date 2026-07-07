import re

from playwright.sync_api import sync_playwright
import pandas as pd
import time
import datetime

def login_Save_State(page, context):
    YourEmail = ""
    YourPassword = ""

    page.goto("https://rotrends.com/login")

    email_box = page.get_by_role("textbox", name="Email Address")
    email_box.wait_for(state="visible")

    email_box.click()
    time.sleep(1)
    email_box.press_sequentially(YourEmail, delay=300)
    
    page.keyboard.press("Tab")
    page.wait_for_timeout(500)
    
    page.keyboard.insert_text(YourPassword)
    page.wait_for_timeout(500)

    
    page.keyboard.press("Enter")
    
    time.sleep(5)

    context.storage_state(path="auth_state.json")
    print("Login successful and state saved.")

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

    df = pd.DataFrame(all_games)

    return df


def new_and_rising_games(page, columns):
     page.goto("https://rotrends.com/games?page=1&page_size=100&sort=-rank_change_day&created_min=2026-06-04T00%3A00%3A00.000Z")
     set_preferences(page, columns)
     return extract_games(page, "New and Rising")

def top_moving_games(page, columns):
     page.goto("https://rotrends.com/games?page=1&page_size=100&sort=-rank_change_day&playing_min=500")
     set_preferences(page, columns)
     return extract_games(page, "Top Moving")

def new_and_stable_games(page, columns):
     page.goto("https://rotrends.com/games?page=1&page_size=100&sort=-rap_14d&created_min=2026-06-05T00%3A00%3A00.000Z")
     set_preferences(page, columns)
     return extract_games(page, "New and Stable")

def top_100_games(page, columns):
        page.goto("https://rotrends.com/games?page=1&page_size=100&sort=-rank_change_day&rank_max=100")
        set_preferences(page, columns)
        return extract_games(page, "Top 100")

def top_by_earning(page, columns):
     page.goto("https://rotrends.com/games?page=1&page_size=100&sort=-earning_rank")
     set_preferences(page, columns)
     return extract_games(page, "Top by Earning")

def top_by_players(page, columns):
     page.goto("https://rotrends.com/games?page=1&page_size=100&sort=-players")
     set_preferences(page, columns)
     return extract_games(page, "Top by Players")

def top_by_session(page, columns):
     page.goto("https://rotrends.com/games?page=1&page_size=100&sort=-est_avg_session_duration_naive&playing_min=100")
     set_preferences(page, columns)
     return extract_games(page, "Top by Session")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        context = browser.new_context()
        page = context.new_page()

        columns = ["Game Name", "Global Rank", "Global Rank Shift (1d)", "Global Rank Shift (1w)", "Global Rank Shift (1m)", "Avg CCU Rank (1d)", "Avg CCU Rank (7d)", "Avg CCU Rank (14d)", "Avg CCU Rank Shift (1d)", "Earning Rank", "Genre", "Sub Genre", "Visits", "Players (CCU)", "Platform Share", "Avg CCU (1d)", "Avg CCU (7d)", "Avg CCU (14d)", "Momentum (1d)", "Momentum (1w)", "Momentum (1m)", "Avg Session", "Favorites", "Rating", "Up Votes", "Down Votes", "Created", "Extract Date"]

        login_Save_State(page, context)

        all_dataframes = []

        all_dataframes.append(new_and_rising_games(page, columns))
        all_dataframes.append(top_moving_games(page, columns))
        all_dataframes.append(new_and_stable_games(page, columns))
        all_dataframes.append(top_100_games(page, columns))
        all_dataframes.append(top_by_earning(page, columns))
        all_dataframes.append(top_by_players(page, columns))
        all_dataframes.append(top_by_session(page, columns))

        browser.close()

        final_df = pd.concat(all_dataframes, ignore_index=True)

if __name__ == "__main__":
    main()