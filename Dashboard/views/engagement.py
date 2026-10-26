import plotly.express as px
import streamlit as st

from Analytics.insights import (
    cluster_games,
    cluster_profile,
    metric_links,
    momentum_mix,
    monetisation_leaders,
    top_movers,
)
from Dashboard import charts, ui
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

games = current_games()

ui.page_header("Engagement", "Retention, momentum and monetisation")
ui.require_games(games)

stick_tab, momentum_tab, money_tab, types_tab, drivers_tab = st.tabs(
    ["Retention", "Momentum", "Monetisation", "Segments", "Drivers"]
)

with stick_tab:
    ui.section("Average session length by genre", "Minutes, median marked")
    sessions = games.dropna(subset=["avg_session"])
    sessions = sessions[sessions["genre"] != "Unknown"]
    order = sessions.groupby("genre")["avg_session"].median().sort_values().index.tolist()
    fig = px.box(
        sessions,
        x="avg_session",
        y="genre",
        category_orders={"genre": order},
        color_discrete_sequence=[charts.SERIES[0]],
        points=False,
    )
    fig.update_xaxes(title="Average session (minutes)")
    fig.update_yaxes(title=None)
    charts.show(fig, max(380, 34 * len(order) + 100))

    ui.section("Like ratio against concurrent players")
    liked = games.dropna(subset=["like_ratio"])
    fig = px.scatter(
        liked,
        x="players_ccu",
        y="like_ratio",
        color="genre",
        log_x=True,
        hover_name="display_name",
        hover_data={"total_votes": ":,", "genre": False},
        color_discrete_sequence=charts.SERIES,
    )
    fig.update_xaxes(title="Players online (log scale)")
    fig.update_yaxes(title="Share of votes that are up-votes", tickformat=".0%")
    charts.show(fig, 460)

with momentum_tab:
    floor = st.slider("Minimum players", 0, 5000, 500, step=100)
    rising, fading = top_movers(games, min_ccu=floor, n=10)
    ui.section("Players now relative to 14-day average")
    for title, frame, colour in (("Surging", rising, charts.SERIES[0]),
                                  ("Fading", fading, charts.SERIES[1])):
        if frame.empty:
            continue
        frame = frame.merge(games[["game_name", "display_name"]].drop_duplicates("game_name"),
                            on="game_name").sort_values("ccu_surge")
        fig = px.bar(
            frame,
            x="ccu_surge",
            y="display_name",
            orientation="h",
            text=frame["ccu_surge"].map(lambda v: f"{v:.1f}x"),
            color_discrete_sequence=[colour],
            title=title,
        )
        fig.add_vline(x=1, line_dash="dot", line_color="rgba(128,128,128,0.8)")
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig.update_xaxes(title="Players now / 14-day average")
        fig.update_yaxes(title=None)
        charts.show(fig, 400)

    mix = momentum_mix(games[games["genre"] != "Unknown"])
    if not mix.empty:
        ui.section("One-month momentum mix by genre")
        long = mix.reset_index().melt(id_vars="genre", var_name="momentum", value_name="share")
        fig = px.bar(
            long,
            x="share",
            y="genre",
            color="momentum",
            orientation="h",
            color_discrete_sequence=charts.SERIES,
        )
        fig.update_xaxes(title=None, tickformat=".0%")
        fig.update_yaxes(title=None)
        charts.show(fig, max(380, 34 * len(mix) + 120))

with money_tab:
    paid = games.dropna(subset=["earning_rank", "avg_ccu_rank_14d"])
    if paid.empty:
        st.info("No earning ranks in the current selection.")
    else:
        ui.section("Player rank against earning rank", "Below the line: earns above audience rank")
        fig = px.scatter(
            paid,
            x="avg_ccu_rank_14d",
            y="earning_rank",
            color="genre",
            log_x=True,
            log_y=True,
            hover_name="display_name",
            hover_data={"players_ccu": ":,", "genre": False},
            color_discrete_sequence=charts.SERIES,
        )
        top = float(max(paid["avg_ccu_rank_14d"].max(), paid["earning_rank"].max()))
        fig.add_shape(type="line", x0=1, y0=1, x1=top, y1=top,
                      line=dict(color="rgba(128,128,128,0.7)", dash="dot"))
        fig.update_xaxes(title="Player rank (1 is best)")
        fig.update_yaxes(title="Earning rank (1 is best)")
        charts.show(fig, 500)
        leaders = monetisation_leaders(paid, n=10).merge(
            games[["game_name", "display_name"]].drop_duplicates("game_name"), on="game_name"
        )
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
        names = {
            row.cluster: f"{row.cluster + 1}. {row.description}" for row in profile.itertuples()
        }
        clustered["group"] = clustered["cluster"].map(names)
        fig = px.scatter(
            clustered,
            x="avg_session",
            y="players_ccu",
            color="group",
            log_y=True,
            hover_name="display_name",
            hover_data={"genre": True, "age_days": True, "group": False},
            color_discrete_sequence=charts.SERIES,
            category_orders={"group": sorted(names.values())},
        )
        fig.update_xaxes(title="Average session (minutes)")
        fig.update_yaxes(title="Players online (log scale)")
        charts.show(fig, 520)
        profile["group"] = profile["cluster"].map(names)
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
        links["direction"] = links["correlation"].map(lambda v: "More players" if v >= 0
                                                      else "Fewer players")
        fig = px.bar(
            links,
            x="correlation",
            y="label",
            color="direction",
            orientation="h",
            text=links["correlation"].map(lambda v: f"{v:+.2f}"),
            color_discrete_map={"More players": charts.SERIES[0], "Fewer players": charts.MUTED},
        )
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig.update_xaxes(title="Correlation (-1 to +1)", range=[-1, 1])
        fig.update_yaxes(title=None)
        charts.show(fig, max(360, 40 * len(links) + 120))
