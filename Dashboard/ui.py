import streamlit as st


def compact(value: float) -> str:
    value = float(value)
    for limit, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(value) >= limit:
            return f"{value / limit:.1f}{suffix}"
    return f"{value:,.0f}"


def times(value: float) -> str:
    return "<0.1x" if value < 0.05 else f"{value:.1f}x"


def page_header(title: str, subtitle: str | None = None) -> None:
    st.title(title)
    if subtitle:
        st.markdown(f'<div class="muted">{subtitle}</div>', unsafe_allow_html=True)


def section(title: str, blurb: str | None = None) -> None:
    st.subheader(title)
    if blurb:
        st.caption(blurb)


def require_games(games) -> None:
    if games.empty:
        st.warning("No games match the current filters.")
        st.stop()
