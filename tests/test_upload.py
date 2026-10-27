from Cloud_Database import database
from Scraper.validate import ScrapedGameData


def scraped(name, category, created="10/05/2026", extract="2026-10-27", ccu="1,200"):
    return ScrapedGameData(**{
        "Games": name,
        "Category": category,
        "Players (CCU)": ccu,
        "Created": created,
        "Date Extracted": extract,
        "Genre": "Simulation",
    })


class Recorder:
    def __init__(self):
        self.calls = []

    def table(self, name):
        self.calls.append(("table", name))
        return self

    def delete(self):
        self.calls.append(("delete",))
        return self

    def eq(self, column, value):
        self.calls.append(("eq", column, value))
        return self

    def upsert(self, rows):
        self.calls.append(("upsert", len(rows)))
        return self

    def insert(self, rows):
        self.calls.append(("insert", len(rows)))
        return self

    def execute(self):
        return self


def test_same_game_gets_the_same_id_on_every_scrape_and_title_variant():
    first = scraped("Fish It!", "Top 100", extract="2026-10-20")
    later = scraped("[UPD] Fish It! 🐟", "Top by Players", extract="2026-10-27")
    assert first.game_id == later.game_id


def test_different_release_date_gives_a_different_id():
    other = scraped("Obby", "Top 100", created="11/01/2026")
    assert scraped("Obby", "Top 100").game_id != other.game_id


def test_build_rows_merges_lists_into_one_game_and_one_metric_row():
    games = [
        scraped("Fish It!", "Top 100"),
        scraped("[UPD] Fish It!", "Top by Players"),
        scraped("Fish It!", "Top 100"),
        scraped("Other", "Top 100"),
    ]
    dim_rows, metric_rows = database.build_rows(games)
    assert len(dim_rows) == 2
    assert len(metric_rows) == 2
    fish = next(row for row in dim_rows if row["game_name"].endswith("Fish It!"))
    assert fish["category"] == "Top 100, Top by Players"


def test_same_game_on_two_days_keeps_two_metric_rows_and_one_dim_row_per_batch():
    games = [scraped("Fish It!", "Top 100", extract="2026-10-20"),
             scraped("Fish It!", "Top 100", extract="2026-10-27")]
    dim_rows, metric_rows = database.build_rows(games)
    assert len(dim_rows) == 1
    assert len(metric_rows) == 2


def test_upload_replaces_that_days_metrics_before_inserting():
    client = Recorder()
    games = [scraped("Fish It!", "Top 100"), scraped("Other", "Top 100")]
    stored = database.upload_data(games, client)
    assert stored == (2, 2)
    kinds = [call[0] for call in client.calls if call[0] in ("delete", "upsert", "insert")]
    assert kinds == ["delete", "upsert", "insert"]
    assert ("eq", "extract_date", "2026-10-27T00:00:00") in client.calls
