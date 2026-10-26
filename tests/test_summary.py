import numpy as np
import pandas as pd

from Analytics import prepare, summary
from tests.conftest import make_row


def build_market():
    rng = np.random.default_rng(1)
    rows = []
    for i in range(6):
        rows.append(make_row(game_name=f"Hot Pet Quest {i}", genre="Simulation",
                             sub_genre="Pets", created=f"2026-07-{10 + i}",
                             players_ccu=20000 + i * 100, avg_ccu_1d=40000,
                             avg_ccu_14d=20000))
    for i in range(30):
        rows.append(make_row(game_name=f"Crowd Tower {i}", genre="Strategy",
                             sub_genre="Tycoon", created=f"2024-01-{1 + i % 28:02d}",
                             players_ccu=int(rng.integers(50, 300)), avg_ccu_1d=100,
                             avg_ccu_14d=100))
    return prepare.prepare(pd.DataFrame(rows))


def test_findings_name_the_underserved_niche_and_crowded_niche():
    found = {f.label: f for f in summary.headline_findings(build_market())}
    assert found["Biggest gap"].headline == "Pets games"
    assert found["Most crowded"].headline == "Tycoon games"
    assert found["Fastest riser"].detail.startswith("Players are at 2.0x")
    assert found["Easiest to break into"].headline == "Simulation"


def test_findings_skip_what_cannot_be_computed():
    tiny = build_market().head(2)
    labels = [f.label for f in summary.headline_findings(tiny)]
    assert "Biggest gap" not in labels
    assert "Most crowded" not in labels


def test_share_formats_tiny_values():
    assert summary.share(0.004) == "<1%"
    assert summary.share(0.256) == "26%"
