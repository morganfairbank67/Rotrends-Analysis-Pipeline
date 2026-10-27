import altair as alt
import pandas as pd

from Dashboard import viz


def spec(chart):
    return chart.to_dict()


def test_hbar_orders_largest_first_and_labels_values():
    df = pd.DataFrame({"genre": ["A", "B", "C"], "gap": [1.0, 5.0, -2.0]})
    chart = viz.hbar(df, "genre", "gap", label=lambda v: f"{v:+.1f}")
    body = spec(chart)
    first = body["layer"][0]
    assert first["encoding"]["y"]["sort"] == ["B", "A", "C"]
    texts = [layer for layer in body["layer"] if layer["mark"]["type"] == "text"]
    assert {t["mark"]["align"] for t in texts} == {"left", "right"}


def test_hbar_adds_reference_rule_when_asked():
    df = pd.DataFrame({"genre": ["A", "B"], "share": [0.5, 2.0]})
    layers = spec(viz.hbar(df, "genre", "share", rule=1))["layer"]
    assert "rule" in [layer["mark"]["type"] for layer in layers]


def test_scatter_uses_log_scales_and_labels_top_points():
    df = pd.DataFrame({"games": [1, 2, 3], "ccu": [10, 100, 1000], "name": list("abc")})
    chart = viz.scatter(df, "games", "ccu", log_x=True, log_y=True, label="name", label_top=2)
    body = spec(chart)
    assert body["layer"][0]["encoding"]["x"]["scale"]["type"] == "log"
    assert body["layer"][1]["mark"]["type"] == "text"
    assert len(body["datasets"]) >= 2


def test_line_has_hover_selection():
    df = pd.DataFrame({
        "extract_date": pd.to_datetime(["2026-10-20", "2026-10-27"] * 2),
        "players": [1, 2, 3, 4],
        "genre": ["A", "A", "B", "B"],
    })
    body = spec(viz.line(df, "extract_date", "players", color="genre"))
    assert any(param.get("select", {}).get("nearest") for param in body["params"])


def test_remaining_helpers_produce_valid_specs():
    df = pd.DataFrame({"bucket": ["new", "old"] * 2, "measure": ["a", "a", "b", "b"],
                       "share": [0.2, 0.8, 0.3, 0.7]})
    assert spec(viz.vbar_grouped(df, "bucket", "share", "measure", y_format="%"))
    assert spec(viz.stacked_hbar(df, "bucket", "share", "measure"))
    grid = pd.DataFrame({"genre": ["A", "A", "B"], "sub": ["x", "y", "x"], "ccu": [1, 2, 3]})
    assert spec(viz.heatmap(grid, "sub", "genre", "ccu", value_title="Players"))
    box = pd.DataFrame({"genre": ["A"] * 5 + ["B"] * 5, "mins": list(range(10))})
    assert spec(viz.boxplot(box, "genre", "mins", order=["A", "B"]))


def test_themed_charts_validate_in_both_palettes(monkeypatch):
    df = pd.DataFrame({"genre": ["A", "B"], "gap": [1.0, 2.0]})
    chart = viz.hbar(df, "genre", "gap")
    for dark in (False, True):
        chosen = viz.charts.DARK if dark else viz.charts.LIGHT
        monkeypatch.setattr(viz.charts, "palette", lambda chosen=chosen: chosen)
        assert isinstance(viz.themed(chart), alt.TopLevelMixin)
