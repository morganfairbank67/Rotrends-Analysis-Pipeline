import streamlit as st


def compact(value: float) -> str:
    value = float(value)
    for limit, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(value) >= limit:
            return f"{value / limit:.1f}{suffix}"
    return f"{value:,.0f}"


def page_header(title: str, question: str) -> None:
    st.title(title)
    st.markdown(f"##### {question}")


def takeaway(text: str) -> None:
    st.info(text, icon="💡")


def how_to_read(text: str) -> None:
    with st.expander("How to read this"):
        st.markdown(text)


def section(title: str, blurb: str) -> None:
    st.subheader(title)
    st.caption(blurb)


def require_games(games) -> None:
    if games.empty:
        st.warning("No games match your filters. Widen them in the sidebar or press Reset filters.")
        st.stop()
