import altair as alt
import streamlit as st

from Analytics.insights import age_cohorts
from Analytics.market import segment_table
from Dashboard import charts, ui, viz
from Dashboard.data import current_games

games = current_games()

ui.page_header("Market gaps", "Demand relative to supply by genre and sub-genre")
ui.require_games(games)

controls = st.columns([2, 2, 3])
level = controls[0].radio("Group by", ["Genre", "Sub-genre"], horizontal=True)
column = "genre" if level == "Genre" else "sub_genre"
min_games = controls[1].slider("Minimum games per group", 1, 15, 3)

table = segment_table(games, column, min_games=min_games)
table = table[~table[column].isin(["Unknown", "Unclassified"])]
if table.empty:
    st.info("No group has that many games. Lower the slider or widen the sidebar filters.")
    st.stop()

ranking_tab, supply_tab, newcomer_tab, age_tab = st.tabs(
    ["Ranking", "Supply and demand", "Entry", "Release age"]
)

with ranking_tab:
    ui.section("Share of players relative to share of games", "1x is a proportional share.")
    viz.show(
        viz.hbar(
            table,
            column,
            "demand_index",
            color="verdict",
            scale=viz.verdict_scale(),
            label=ui.times,
            x_title="Times its proportional share of players",
            rule=1,
            tooltip=[
                alt.Tooltip(f"{column}:N", title=level),
                alt.Tooltip("verdict:N", title="Verdict"),
                alt.Tooltip("demand_index:Q", title="Share multiple", format=".2f"),
                alt.Tooltip("games:Q", title="Games"),
                alt.Tooltip("total_ccu:Q", title="Players", format=","),
                alt.Tooltip("top_game:N", title="Largest game"),
            ],
        )
    )

with supply_tab:
    ui.section("Games against players", "Top left: many players, few games. Both axes logarithmic.")
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
            x_title="Games in the top lists",
            y_title="Total players",
            label=column,
            label_top=5,
            label_by="total_ccu",
            tooltip=[
                alt.Tooltip(f"{column}:N", title=level),
                alt.Tooltip("verdict:N", title="Verdict"),
                alt.Tooltip("games:Q", title="Games"),
                alt.Tooltip("total_ccu:Q", title="Players", format=","),
                alt.Tooltip("median_ccu:Q", title="Typical game", format=",.0f"),
            ],
        ),
        height=460,
    )

with newcomer_tab:
    ui.section("Release recency and incumbent concentration")
    viz.show(
        viz.scatter(
            table,
            "recent_share",
            "top_game_share",
            color="verdict",
            scale=viz.verdict_scale(),
            size="games",
            x_title="Share of games under 90 days old",
            y_title="Largest game's share of group players",
            x_format="%",
            y_format="%",
            label=column,
            label_top=6,
            label_by="total_ccu",
            tooltip=[
                alt.Tooltip(f"{column}:N", title=level),
                alt.Tooltip("verdict:N", title="Verdict"),
                alt.Tooltip("games:Q", title="Games"),
                alt.Tooltip("recent_share:Q", title="Under 90 days", format=".0%"),
                alt.Tooltip("top_game_share:Q", title="Largest game share", format=".0%"),
                alt.Tooltip("top_game:N", title="Largest game"),
            ],
        ),
        height=460,
    )

with age_tab:
    ui.section("Share of players and games by release age")
    cohorts = age_cohorts(games).melt(
        id_vars="age_bucket",
        value_vars=["ccu_share", "game_share"],
        var_name="measure",
        value_name="share",
    )
    cohorts["measure"] = cohorts["measure"].map(
        {"ccu_share": "Share of players", "game_share": "Share of games"}
    )
    viz.show(
        viz.vbar_grouped(
            cohorts,
            "age_bucket",
            "share",
            "measure",
            order=["< 1 month", "1-3 months", "3-12 months", "1-3 years", "3+ years"],
            label=lambda v: f"{v:.0%}",
            y_format="%",
            scale=alt.Scale(
                domain=["Share of games", "Share of players"],
                range=[charts.MUTED, charts.SERIES[0]],
            ),
        ),
        height=380,
    )

    fresh = games[games["age_days"] <= 30].nlargest(10, "players_ccu")
    st.markdown("**Largest releases in the last 30 days**")
    st.dataframe(
        fresh[["display_name", "genre", "sub_genre", "players_ccu", "age_days"]],
        hide_index=True,
        width="stretch",
        column_config={
            "display_name": "Game", "genre": "Genre", "sub_genre": "Sub-genre",
            "players_ccu": st.column_config.NumberColumn("Players", format="%d"),
            "age_days": st.column_config.NumberColumn("Age (days)", format="%d"),
        },
    )

with st.expander("Data"):
    st.dataframe(
        table[[column, "verdict", "games", "total_ccu", "median_ccu", "demand_index",
               "opportunity_score", "top_game"]],
        hide_index=True,
        width="stretch",
        column_config={
            column: level, "verdict": "Verdict", "games": "Games",
            "total_ccu": st.column_config.NumberColumn("Total players", format="%d"),
            "median_ccu": st.column_config.NumberColumn("Typical game", format="%d"),
            "demand_index": st.column_config.NumberColumn("Fair-share multiple", format="%.2f"),
            "opportunity_score": st.column_config.NumberColumn("Opportunity", format="%.2f"),
            "top_game": "Largest game",
        },
    )
