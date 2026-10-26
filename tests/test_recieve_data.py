import pandas as pd

from Cloud_Database import recieveData


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows
        self.window = (0, len(rows))

    def select(self, _):
        return self

    def range(self, start, end):
        self.window = (start, end + 1)
        return self

    def execute(self):
        return FakeResponse(self.rows[self.window[0]:self.window[1]])


class FakeClient:
    def __init__(self, tables):
        self.tables = tables

    def table(self, name):
        return FakeQuery(self.tables[name])


def test_fetch_table_reads_past_the_page_limit(monkeypatch):
    monkeypatch.setattr(recieveData, "PAGE_SIZE", 3)
    rows = [{"game_id": str(i)} for i in range(8)]
    df = recieveData.fetch_table(FakeClient({"t": rows}), "t")
    assert len(df) == 8


def test_fetch_table_handles_exact_page_multiple(monkeypatch):
    monkeypatch.setattr(recieveData, "PAGE_SIZE", 4)
    rows = [{"game_id": str(i)} for i in range(8)]
    df = recieveData.fetch_table(FakeClient({"t": rows}), "t")
    assert len(df) == 8


def test_get_data_joins_dimension_and_metrics():
    client = FakeClient({
        "dim_games": [
            {"game_id": "a", "game_name": "Alpha"},
            {"game_id": "b", "game_name": "Beta"},
        ],
        "game_metrics": [{"game_id": "a", "players_ccu": 10}],
    })
    df = recieveData.get_data(client)
    assert isinstance(df, pd.DataFrame)
    assert df.to_dict("records") == [{"game_id": "a", "game_name": "Alpha", "players_ccu": 10}]
