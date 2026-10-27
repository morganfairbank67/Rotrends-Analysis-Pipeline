import argparse
import json
from datetime import datetime
from pathlib import Path

from Analytics.identity import stable_game_id
from Cloud_Database.client import get_client
from Cloud_Database.recieveData import fetch_table

CHUNK = 400
BACKUP_DIR = Path("backups")


def records(frame):
    return json.loads(frame.to_json(orient="records"))


def merge_categories(values) -> str:
    names = {part.strip() for value in values for part in str(value or "").split(",")}
    names.discard("")
    return ", ".join(sorted(names))


def plan_migration(dim_rows: list[dict], metric_rows: list[dict]) -> dict:
    old_to_new = {}
    groups: dict[str, list[dict]] = {}
    for row in dim_rows:
        new_id = str(stable_game_id(row["game_name"], row.get("created")))
        old_to_new[row["game_id"]] = new_id
        groups.setdefault(new_id, []).append(row)

    existing_ids = {row["game_id"] for row in dim_rows}
    new_dim_rows = []
    for new_id, rows in groups.items():
        if new_id in existing_ids and len(rows) == 1:
            continue
        template = dict(rows[0])
        template["game_id"] = new_id
        template["category"] = merge_categories(row.get("category") for row in rows)
        new_dim_rows.append(template)
    delete_dim_ids = [
        row["game_id"] for row in dim_rows if row["game_id"] != old_to_new[row["game_id"]]
    ]

    ordered = sorted(metric_rows, key=lambda r: r["game_id"] != old_to_new.get(r["game_id"]))
    seen = set()
    new_metric_rows = []
    delete_metric_ids = []
    for row in ordered:
        new_id = old_to_new.get(row["game_id"])
        if new_id is None:
            continue
        key = (new_id, row["extract_date"])
        already_migrated = row["game_id"] == new_id
        if key in seen:
            delete_metric_ids.append(row["id"])
            continue
        seen.add(key)
        if already_migrated:
            continue
        moved = {k: v for k, v in row.items() if k != "id"}
        moved["game_id"] = new_id
        new_metric_rows.append(moved)
        delete_metric_ids.append(row["id"])

    return {
        "new_dim_rows": new_dim_rows,
        "new_metric_rows": new_metric_rows,
        "delete_metric_ids": delete_metric_ids,
        "delete_dim_ids": delete_dim_ids,
    }


def chunks(items: list, size: int = CHUNK):
    for start in range(0, len(items), size):
        yield items[start:start + size]


def apply_plan(client, plan: dict) -> None:
    for part in chunks(plan["new_dim_rows"]):
        client.table("dim_games").upsert(part).execute()
    for part in chunks(plan["new_metric_rows"]):
        client.table("game_metrics").insert(part).execute()
    for part in chunks(plan["delete_metric_ids"]):
        client.table("game_metrics").delete().in_("id", part).execute()
    for part in chunks(plan["delete_dim_ids"]):
        client.table("dim_games").delete().in_("game_id", part).execute()


def write_backup(dim_rows: list[dict], metric_rows: list[dict]) -> Path:
    BACKUP_DIR.mkdir(exist_ok=True)
    path = BACKUP_DIR / f"before_id_migration_{datetime.now():%Y%m%d_%H%M%S}.json"
    path.write_text(json.dumps({"dim_games": dim_rows, "game_metrics": metric_rows}))
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    client = get_client()
    dim_rows = records(fetch_table(client, "dim_games"))
    metric_rows = records(fetch_table(client, "game_metrics"))
    plan = plan_migration(dim_rows, metric_rows)

    dims_after = len(dim_rows) - len(plan["delete_dim_ids"]) + len(plan["new_dim_rows"])
    metrics_after = (
        len(metric_rows) - len(plan["delete_metric_ids"]) + len(plan["new_metric_rows"])
    )
    print(f"dim_games:    {len(dim_rows)} rows -> {dims_after}")
    print(f"game_metrics: {len(metric_rows)} rows -> {metrics_after}")
    if not plan["new_dim_rows"] and not plan["delete_metric_ids"] and not plan["delete_dim_ids"]:
        print("Nothing to migrate.")
        return
    if not args.apply:
        print("Dry run. Re-run with --apply to write these changes.")
        return

    print(f"Backup written to {write_backup(dim_rows, metric_rows)}")
    apply_plan(client, plan)
    print("Migration complete.")


if __name__ == "__main__":
    main()
