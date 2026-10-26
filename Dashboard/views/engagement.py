import numpy as np
import plotly.express as px
import streamlit as st

from Analytics.insights import (
    CLUSTER_FEATURES,
    cluster_games,
    cluster_profile,
    list_overlap,
    momentum_mix,
    monetisation_leaders,
    top_movers,
)
from Dashboard import charts
from Dashboard.data import current_games

games = current_games()

st.title("Engagement and momentum")
st.caption("How players behave once they arrive, and which games are gaining or losing them.")

if games.empty:
    st.warning("No games match the current filters.")
    st.stop()

quality_tab, momentum_tab, money_tab, archetype_tab, corr_tab = st.tabs(
    ["Quality and retention", "Momentum", "Monetisation", "Archetypes", "Correlations"]
)

with quality_tab:
    left, right = st.columns(2)
    with left:
        fig = px.box(
            games.dropna(subset=["avg_session"]),
            x="genre",
            y="avg_session",
            color_discrete_sequence=[charts.SERIES[0]],
            points=False,
            title="Average session length by genre",
        )
        fig.update_xaxes(title=None, tickangle=-35)
        fig.update_yaxes(title="Minutes")
        st.plotly_chart(charts.style(fig, 440), width="stretch")
    with right:
        fig = px.box(
            games.dropna(subset=["favorites_per_1k_visits"]),
            x="genre",
            y="favorites_per_1k_visits",
            color_discrete_sequence=[charts.SERIES[2]],
            points=False,
            title="Favourites per 1,000 visits",
        )
        fig.update_xaxes(title=None, tickangle=-35)
        fig.update_yaxes(title="Favourites", type="log")
        st.plotly_chart(charts.style(fig, 440), width="stretch")

    fig = px.scatter(
        games.dropna(subset=["like_ratio"]),
        x="players_ccu",
        y="like_ratio",
        color="genre",
        log_x=True,
        hover_name="game_name",
        hover_data={"total_votes": ":,", "genre": False},
        color_discrete_sequence=charts.SERIES,
        title="Do better-liked games hold more players?",
    )
    fig.update_xaxes(title="Players now")
    fig.update_yaxes(title="Up-votes / all votes", tickformat=".0%")
    st.plotly_chart(charts.style(fig, 480), width="stretch")

    st.markdown("**Which top lists each game appears in**")
    st.dataframe(list_overlap(games), hide_index=True, width="stretch")

with momentum_tab:
    floor = st.slider("Ignore games below this many players", 0, 5000, 500, step=100)
    rising, fading = top_movers(games, min_ccu=floor)
    left, right = st.columns(2)
    for column, title, frame in ((left, "Surging", rising), (right, "Fading", fading)):
        with column:
            st.markdown(f"**{title}** (players now vs 14-day average)")
            st.dataframe(
                frame,
                hide_index=True,
                width="stretch",
                column_config={
                    "ccu_surge": st.column_config.NumberColumn("1d / 14d CCU", format="%.2fx")
                },
            )

    mix = momentum_mix(games)
    if not mix.empty:
        long = mix.reset_index().melt(id_vars="genre", var_name="momentum", value_name="share")
        fig = px.bar(
            long,
            x="share",
            y="genre",
            color="momentum",
            orientation="h",
            color_discrete_sequence=charts.SERIES,
            title="One-month momentum mix by genre",
        )
        fig.update_xaxes(title=None, tickformat=".0%")
        fig.update_yaxes(title=None)
        st.plotly_chart(charts.style(fig, 440), width="stretch")

with money_tab:
    paid = games.dropna(subset=["earning_rank", "avg_ccu_rank_14d"])
    if paid.empty:
        st.info("No earning ranks in the current selection.")
    else:
        fig = px.scatter(
            paid,
            x="avg_ccu_rank_14d",
            y="earning_rank",
            color="genre",
            log_x=True,
            log_y=True,
            hover_name="game_name",
            hover_data={"players_ccu": ":,", "genre": False},
            color_discrete_sequence=charts.SERIES,
            title="Player rank vs earning rank (lower is better)",
        )
        top = float(max(paid["avg_ccu_rank_14d"].max(), paid["earning_rank"].max()))
        fig.add_shape(type="line", x0=1, y0=1, x1=top, y1=top,
                      line=dict(color="rgba(128,128,128,0.6)", dash="dot"))
        fig.update_xaxes(title="14-day average CCU rank")
        fig.update_yaxes(title="Earning rank")
        st.plotly_chart(charts.style(fig, 520), width="stretch")
        st.caption(
            "Below the dotted line a game earns better than its player rank suggests. "
            "Earning ranks only exist for games in the earning list."
        )
        st.markdown("**Best monetisers relative to their audience**")
        st.dataframe(monetisation_leaders(paid), hide_index=True, width="stretch")

with archetype_tab:
    k = st.slider("Number of archetypes", 2, 8, 4)
    try:
        clustered = cluster_games(games, k)
    except ValueError:
        st.info("Not enough complete games to cluster. Loosen the filters.")
    else:
        clustered["archetype"] = "Group " + (clustered["cluster"] + 1).astype(str)
        fig = px.scatter(
            clustered,
            x="avg_session",
            y="players_ccu",
            color="archetype",
            log_y=True,
            hover_name="game_name",
            hover_data={"genre": True, "age_days": True, "archetype": False},
            color_discrete_sequence=charts.SERIES,
            category_orders={"archetype": sorted(clustered["archetype"].unique())},
        )
        fig.update_xaxes(title="Average session (minutes)")
        fig.update_yaxes(title="Players now")
        st.plotly_chart(charts.style(fig, 520), width="stretch")
        st.markdown("**Median profile of each group**")
        st.dataframe(cluster_profile(clustered), hide_index=True, width="stretch")
        st.caption(
            "K-Means on log-scaled players, session length, like ratio, favourites per visit, age."
        )

with corr_tab:
    numeric = games.select_dtypes("number").columns.tolist()
    default = [c for c in CLUSTER_FEATURES + ["global_rank", "visits", "earning_rank"]
               if c in numeric]
    chosen = st.multiselect("Metrics", numeric, default=default)
    method = st.radio("Method", ["spearman", "pearson"], horizontal=True)
    if len(chosen) < 2:
        st.info("Pick at least two metrics.")
    else:
        corr = games[chosen].corr(method=method)
        fig = px.imshow(
            corr,
            zmin=-1,
            zmax=1,
            color_continuous_scale=["#e34948", "#f0efec", "#2a78d6"],
            text_auto=".2f",
            aspect="auto",
        )
        fig.update_xaxes(title=None, tickangle=-35)
        fig.update_yaxes(title=None)
        st.plotly_chart(charts.style(fig, 560), width="stretch")
        st.caption(
            "Spearman compares ranks, which suits CCU and visits because a few giants skew them."
        )
        upper = np.triu(np.ones(corr.shape, dtype=bool), k=1)
        pairs = corr.where(upper).stack().reset_index()
        pairs.columns = ["metric_a", "metric_b", "correlation"]
        pairs = pairs.reindex(pairs["correlation"].abs().sort_values(ascending=False).index)
        st.markdown("**Strongest pairs**")
        st.dataframe(pairs.head(10), hide_index=True, width="stretch")
