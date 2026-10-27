import altair as alt
import pandas as pd
import streamlit as st

from Analytics.insights import (
    cluster_games,
    cluster_profile,
    metric_links,
    momentum_mix,
    monetisation_leaders,
    top_movers,
)
from Dashboard import charts, ui, viz
from Dashboard.data import current_games

LINK_LABELS = {
    "avg_session": "Longer sessions",
    "like_ratio": "Higher like ratio",
    "favorites_per_1k_visits": "More favourites per visit",
    "age_days": "Older game",
    "visits": "More total visits",
    "total_votes": "More votes cast",
    "up_votes": "More up-votes",
    "favorites": "More favourites",
    "earning_rank": "Worse earning rank",
    "ccu_surge": "Recent surge in players",
}
MOMENTUM_ORDER = ["Surging", "Rising", "Stable", "Fading", "Dropping"]

games = current_games()
names = games[["game_name", "display_name"]].drop_duplicates("game_name")

ui.page_header("Engagement", "Retention, momentum and monetisation")
ui.require_games(games)

stick_tab, momentum_tab, money_tab, types_tab, drivers_tab = st.tabs(
    ["Retention", "Momentum", "Monetisation", "Segments", "Drivers"]
)

with stick_tab:
    ui.section("Average session length by genre", "Minutes, median marked")
    sessions = games.dropna(subset=["avg_session"])
    sessions = sessions[sessions["genre"] != "Unknown"]
    order = sessions.groupby("genre")["avg_session"].median().sort_values(ascending=False)
    viz.show(
        viz.boxplot(sessions, "genre", "avg_session", order=order.index.tolist(),
                    x_title="Average session (minutes)")
    )

    ui.section("Like ratio against concurrent players")
    liked = games.dropna(subset=["like_ratio"])
    liked = viz.limit_categories(liked, "genre")
    viz.show(
        viz.scatter(
            liked,
            "players_ccu",
            "like_ratio",
            color="genre",
            log_x=True,
            x_title="Players (log)",
            y_title="Share of votes that are up-votes",
            x_format="~s",
            y_format="%",
            tooltip=[
                alt.Tooltip("display_name:N", title="Game"),
                alt.Tooltip("genre:N", title="Genre"),
                alt.Tooltip("players_ccu:Q", title="Players", format=","),
                alt.Tooltip("like_ratio:Q", title="Liked", format=".0%"),
                alt.Tooltip("total_votes:Q", title="Votes", format=","),
            ],
        ),
        height=440,
    )

with momentum_tab:
    floor = st.slider("Minimum players", 0, 5000, 500, step=100)
    rising, fading = top_movers(games, min_ccu=floor, n=10)
    ui.section("Players now relative to 14-day average")
    for title, frame, colour in (("Surging", rising, charts.SERIES[0]),
                                  ("Fading", fading, charts.SERIES[1])):
        if frame.empty:
            continue
        frame = frame.merge(names, on="game_name")
        st.markdown(f"**{title}**")
        viz.show(
            viz.hbar(
                frame.assign(group=title),
                "display_name",
                "ccu_surge",
                color="group",
                scale=alt.Scale(domain=[title], range=[colour]),
                label=ui.times,
                x_title="Players now / 14-day average",
                rule=1,
                ascending=(title == "Fading"),
                show_legend=False,
                tooltip=[
                    alt.Tooltip("display_name:N", title="Game"),
                    alt.Tooltip("genre:N", title="Genre"),
                    alt.Tooltip("players_ccu:Q", title="Players", format=","),
                    alt.Tooltip("avg_ccu_14d:Q", title="14-day average", format=",.0f"),
                    alt.Tooltip("ccu_surge:Q", title="Ratio", format=".2f"),
                ],
            )
        )

    mix = momentum_mix(games[games["genre"] != "Unknown"])
    if not mix.empty:
        ui.section("One-month momentum mix by genre")
        long = mix.reset_index().melt(id_vars="genre", var_name="momentum", value_name="share")
        domain = [m for m in MOMENTUM_ORDER if m in long["momentum"].unique()]
        palette = {
            "Surging": charts.SERIES[0],
            "Rising": charts.SERIES[2],
            "Stable": charts.MUTED,
            "Fading": charts.SERIES[3],
            "Dropping": charts.SERIES[7],
        }
        viz.show(
            viz.stacked_hbar(
                long,
                "genre",
                "share",
                "momentum",
                scale=alt.Scale(domain=domain, range=[palette[m] for m in domain]),
            )
        )

with money_tab:
    paid = games.dropna(subset=["earning_rank", "avg_ccu_rank_14d"])
    if paid.empty:
        st.info("No earning ranks in the current selection.")
    else:
        ui.section("Player rank against earning rank", "Below the line: earns above audience rank")
        top = float(max(paid["avg_ccu_rank_14d"].max(), paid["earning_rank"].max()))
        diagonal = pd.DataFrame({"rank": [1.0, top]})
        both = pd.concat([paid["avg_ccu_rank_14d"], paid["earning_rank"]])
        log_scale, log_axis = viz.log_scale_and_axis(both, None)
        line = (
            alt.Chart(diagonal)
            .mark_line(strokeDash=[4, 4], color=charts.MUTED)
            .encode(
                x=alt.X("rank:Q", scale=log_scale, axis=log_axis),
                y=alt.Y("rank:Q", scale=log_scale, axis=log_axis),
            )
        )
        points = viz.scatter(
            viz.limit_categories(paid, "genre"),
            "avg_ccu_rank_14d",
            "earning_rank",
            color="genre",
            log_x=True,
            log_y=True,
            shared_log_range=both,
            x_title="Player rank (1 is best)",
            y_title="Earning rank (1 is best)",
            tooltip=[
                alt.Tooltip("display_name:N", title="Game"),
                alt.Tooltip("genre:N", title="Genre"),
                alt.Tooltip("players_ccu:Q", title="Players", format=","),
                alt.Tooltip("avg_ccu_rank_14d:Q", title="Player rank", format=",.0f"),
                alt.Tooltip("earning_rank:Q", title="Earning rank", format=",.0f"),
            ],
        )
        viz.show(alt.layer(points, line), height=480)
        leaders = monetisation_leaders(paid, n=10).merge(names, on="game_name")
        st.markdown("**Strongest earners relative to player rank**")
        st.dataframe(
            leaders[["display_name", "genre", "players_ccu", "avg_ccu_rank_14d", "earning_rank"]],
            hide_index=True,
            width="stretch",
            column_config={
                "display_name": "Game", "genre": "Genre",
                "players_ccu": st.column_config.NumberColumn("Players", format="%d"),
                "avg_ccu_rank_14d": st.column_config.NumberColumn("Player rank", format="%d"),
                "earning_rank": st.column_config.NumberColumn("Earning rank", format="%d"),
            },
        )

with types_tab:
    k = st.slider("Segments", 2, 8, 4)
    try:
        clustered = cluster_games(games, k)
    except ValueError:
        st.info("Not enough complete games to group. Widen the sidebar filters.")
    else:
        profile = cluster_profile(clustered)
        labels = {
            row.cluster: f"{row.cluster + 1}. {row.description}" for row in profile.itertuples()
        }
        clustered["group"] = clustered["cluster"].map(labels)
        viz.show(
            viz.scatter(
                clustered,
                "avg_session",
                "players_ccu",
                color="group",
                scale=viz.categorical_scale(sorted(labels.values())),
                log_y=True,
                x_title="Average session (minutes)",
                y_title="Players (log)",
                y_format="~s",
                tooltip=[
                    alt.Tooltip("display_name:N", title="Game"),
                    alt.Tooltip("genre:N", title="Genre"),
                    alt.Tooltip("group:N", title="Segment"),
                    alt.Tooltip("players_ccu:Q", title="Players", format=","),
                    alt.Tooltip("avg_session:Q", title="Session (min)", format=".1f"),
                    alt.Tooltip("age_days:Q", title="Age (days)", format=","),
                ],
            ),
            height=480,
        )
        profile["group"] = profile["cluster"].map(labels)
        st.dataframe(
            profile[["group", "games", "top_genre", "players_ccu", "avg_session", "age_days"]],
            hide_index=True,
            width="stretch",
            column_config={
                "group": "Group", "games": "Games", "top_genre": "Most common genre",
                "players_ccu": st.column_config.NumberColumn("Typical players", format="%d"),
                "avg_session": st.column_config.NumberColumn("Typical session (min)",
                                                             format="%.1f"),
                "age_days": st.column_config.NumberColumn("Typical age (days)", format="%d"),
            },
        )

with drivers_tab:
    ui.section("Rank correlation with concurrent players")
    links = metric_links(games, "players_ccu", list(LINK_LABELS))
    if links.empty:
        st.info("Not enough data to compare. Widen the sidebar filters.")
    else:
        links["label"] = links["metric"].map(LINK_LABELS)
        links["direction"] = links["correlation"].map(
            lambda v: "More players" if v >= 0 else "Fewer players"
        )
        viz.show(
            viz.hbar(
                links,
                "label",
                "correlation",
                color="direction",
                scale=alt.Scale(domain=["More players", "Fewer players"],
                                range=[charts.SERIES[0], charts.MUTED]),
                label=lambda v: f"{v:+.2f}",
                x_title="Correlation (-1 to +1)",
                x_domain=(-1, 1),
                rule=0,
                tooltip=[
                    alt.Tooltip("label:N", title="Metric"),
                    alt.Tooltip("correlation:Q", title="Correlation", format="+.2f"),
                ],
            )
        )
