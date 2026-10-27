from Analytics.identity import stable_game_id
from Cloud_Database import migrate_game_ids as migration


def dim(game_id, name="Fish It!", created="2026-10-05", category="Top 100"):
    return {"game_id": game_id, "game_name": name, "created": created, "category": category,
            "genre": "Simulation", "sub_genre": None}


def metric(row_id, game_id, date="2026-10-27", ccu=100):
    return {"id": row_id, "game_id": game_id, "extract_date": date, "players_ccu": ccu}


def fixture():
    dims = [
        dim("old-1", category="Top 100"),
        dim("old-2", name="[UPD] Fish It!", category="Top by Players"),
        dim("old-3", name="Other", created="2026-09-01"),
    ]
    metrics = [
        metric("m1", "old-1"),
        metric("m2", "old-2"),
        metric("m3", "old-1", date="2026-10-20", ccu=90),
        metric("m4", "old-3"),
    ]
    return dims, metrics


def test_duplicate_ids_collapse_to_one_game_with_merged_categories():
    plan = migration.plan_migration(*fixture())
    fish_id = str(stable_game_id("Fish It!", "2026-10-05"))
    fish = next(row for row in plan["new_dim_rows"] if row["game_id"] == fish_id)
    assert fish["category"] == "Top 100, Top by Players"
    assert len(plan["new_dim_rows"]) == 2
    assert sorted(plan["delete_dim_ids"]) == ["old-1", "old-2", "old-3"]


def test_metrics_dedupe_per_game_and_day_but_keep_history():
    plan = migration.plan_migration(*fixture())
    dates = sorted((row["game_id"], row["extract_date"]) for row in plan["new_metric_rows"])
    fish_id = str(stable_game_id("Fish It!", "2026-10-05"))
    assert dates.count((fish_id, "2026-10-27")) == 1
    assert dates.count((fish_id, "2026-10-20")) == 1
    assert len(plan["new_metric_rows"]) == 3
    assert all("id" not in row for row in plan["new_metric_rows"])
    assert sorted(plan["delete_metric_ids"]) == ["m1", "m2", "m3", "m4"]


def test_running_on_migrated_data_changes_nothing():
    dims, metrics = fixture()
    first = migration.plan_migration(dims, metrics)
    migrated_dims = first["new_dim_rows"]
    migrated_metrics = [dict(row, id=f"n{i}") for i, row in enumerate(first["new_metric_rows"])]
    again = migration.plan_migration(migrated_dims, migrated_metrics)
    assert again == {"new_dim_rows": [], "new_metric_rows": [], "delete_metric_ids": [],
                     "delete_dim_ids": []}


def test_chunks_split_evenly():
    assert [len(c) for c in migration.chunks(list(range(10)), 4)] == [4, 4, 2]
