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
    email_box.press_sequentially(" " + YourEmail, delay=150)
    
    page.keyboard.press("Tab")
    page.wait_for_timeout(500)
    
    page.keyboard.insert_text(YourPassword)
    page.wait_for_timeout(500)
    
    page.keyboard.press("Enter")
    
    time.sleep(3)

    context.storage_state(path="auth_state.json")
    print("Login successful and state saved.")

def set_preferences(page):
        page.get_by_role("button", name="table Metrics (7/34) down").click()
        page.get_by_text("Earning Rank").click()
        page.get_by_text("Genre", exact=True).click()
        page.get_by_text("Sub Genre").click()
        page.get_by_text("Avg CCU (7d)").click()
        page.get_by_role("button", name="table Metrics (11/34) down").click()




def extract_games(page):

    page.wait_for_selector(".ant-table-row")
    games = page.query_selector_all(".ant-table-row")

    for game in games:
        name = game.query_selector(".ant-table-cell:nth-child(1)").inner_text()
        rank_change = game.query_selector(".ant-table-cell:nth-child(2)").inner_text()
        earning_rank = game.query_selector(".ant-table-cell:nth-child(3)").inner_text()
        genre = game.query_selector(".ant-table-cell:nth-child(4)").inner_text()
        sub_genre = game.query_selector(".ant-table-cell:nth-child(5)").inner_text()
        visits = game.query_selector(".ant-table-cell:nth-child(6)").inner_text()
        players = game.query_selector(".ant-table-cell:nth-child(7)").inner_text()
        avg_ccu = game.query_selector(".ant-table-cell:nth-child(8)").inner_text()
        avg_session_length = game.query_selector(".ant-table-cell:nth-child(9)").inner_text()
        favourites = game.query_selector(".ant-table-cell:nth-child(10)").inner_text()
        rating = game.query_selector(".ant-table-cell:nth-child(11)").inner_text()
        dateCreated = game.query_selector(".ant-table-cell:nth-child(12)").inner_text()
        dateExtracted = datetime.datetime.now().strftime("%Y-%m-%d")

        print(f"Name: {name}, Rank Change: {rank_change}, Visits: {visits}, Players: {players}, Avg CCU: {avg_ccu}, Avg Session Length: {avg_session_length}, Favourites: {favourites}, Rating: {rating}, Date Created: {dateCreated}, Date Extracted: {dateExtracted}")
        print("-"*50 + "\n")

def new_and_rising_games(page):
     page.goto("https://rotrends.com/games?page=1&page_size=100&sort=-rank_change_day&created_min=2026-06-04T00%3A00%3A00.000Z")
     set_preferences(page)
     extract_games(page)

def top_moving_games(page):
     page.goto("https://rotrends.com/games?page=1&page_size=100&sort=-rank_change_day&playing_min=500")
     extract_games(page)

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        context = browser.new_context()
        page = context.new_page()

        login_Save_State(page, context)

        new_and_rising_games(page)
        top_moving_games(page)



        browser.close()

if __name__ == "__main__":
    main()