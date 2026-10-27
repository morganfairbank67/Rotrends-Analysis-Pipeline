import altair as alt
import streamlit as st

from Analytics.insights import title_feature_impact
from Analytics.text import phrase_games, phrase_table
from Dashboard import charts, ui, viz
from Dashboard.data import current_games

LENGTHS = {
    "Any length": (1, 2, 3),
    "Single words": (1,),
    "Two-word phrases": (2,),
    "Three-word phrases": (3,),
}

games = current_games()

ui.page_header("Title keywords", "Phrase frequency and demand relative to supply")
ui.require_games(games)

controls = st.columns([2, 2, 3])
length = controls[0].selectbox("Phrase type", list(LENGTHS))
min_games = controls[1].slider("Minimum games", 2, 10, 2)

table = phrase_table(games, LENGTHS[length], min_games)
if table.empty:
    st.info("No phrase meets the minimum. Lower it or widen the filters.")
    st.stop()

frequency_tab, opportunity_tab, detail_tab, features_tab = st.tabs(
    ["Frequency", "Opportunities", "Phrase detail", "Title features"]
)

phrase_tooltip = [
    alt.Tooltip("phrase:N", title="Phrase"),
    alt.Tooltip("games:Q", title="Games"),
    alt.Tooltip("total_ccu:Q", title="Players", format=","),
    alt.Tooltip("top_game:N", title="Largest game"),
    alt.Tooltip("verdict:N", title="Verdict"),
]

with frequency_tab:
    ui.section("Most used phrases", "Games using each phrase")
    viz.show(
        viz.hbar(
            table.nlargest(15, "games"),
            "phrase",
            "games",
            color="verdict",
            scale=viz.verdict_scale(),
            label=lambda v: f"{v:.0f}",
            x_title="Games using the phrase",
            tooltip=phrase_tooltip,
        )
    )

with opportunity_tab:
    ui.section("Share of players relative to share of games", "1x is a proportional share.")
    best = table.nlargest(15, "opportunity_score")
    viz.show(
        viz.hbar(
            best,
            "phrase",
            "demand_index",
            color="verdict",
            scale=viz.verdict_scale(),
            label=ui.times,
            x_title="Times its proportional share of players",
            rule=1,
            tooltip=phrase_tooltip
            + [alt.Tooltip("demand_index:Q", title="Share multiple", format=".2f")],
        )
    )
    with st.expander("Supply and demand"):
        viz.show(
            viz.scatter(
                table,
                "games",
                "total_ccu",
                color="verdict",
                scale=viz.verdict_scale(),
                size="median_ccu",
                log_x=True,
                log_y=True,
                x_title="Games using the phrase (log)",
                y_title="Total players (log)",
                y_format="~s",
                label="phrase",
                label_top=8,
                label_by="opportunity_score",
                tooltip=phrase_tooltip,
            ),
            height=460,
        )

with detail_tab:
    choice = st.selectbox("Phrase", table["phrase"])
    matches = phrase_games(games, choice)
    row = table[table["phrase"] == choice].iloc[0]
    stats = st.columns(3)
    stats[0].metric("Games", int(row["games"]))
    stats[1].metric("Players", ui.compact(row["total_ccu"]))
    stats[2].metric("Largest game share", f"{row['top_game_share']:.0%}")
    st.dataframe(
        matches[["display_name", "genre", "sub_genre", "players_ccu", "avg_session", "like_ratio",
                 "age_days"]],
        hide_index=True,
        width="stretch",
        column_config={
            "display_name": "Game", "genre": "Genre", "sub_genre": "Sub-genre",
            "players_ccu": st.column_config.NumberColumn("Players", format="%d"),
            "avg_session": st.column_config.NumberColumn("Avg session (min)", format="%.1f"),
            "like_ratio": st.column_config.ProgressColumn(
                "Liked", min_value=0, max_value=1, format="percent"
            ),
            "age_days": st.column_config.NumberColumn("Age (days)", format="%d"),
        },
    )

with features_tab:
    ui.section("Median players by title feature")
    impact = title_feature_impact(games)
    impact["present"] = impact["present"].map({True: "Has it", False: "Does not"})
    viz.show(
        viz.vbar_grouped(
            impact,
            "feature",
            "median_ccu",
            "present",
            label=ui.compact,
            y_title="Median players",
            y_format="~s",
            scale=alt.Scale(domain=["Has it", "Does not"], range=[charts.SERIES[0], charts.MUTED]),
            tooltip=[
                alt.Tooltip("feature:N", title="Feature"),
                alt.Tooltip("present:N", title=""),
                alt.Tooltip("median_ccu:Q", title="Median players", format=",.0f"),
                alt.Tooltip("games:Q", title="Games"),
            ],
        ),
        height=380,
    )
