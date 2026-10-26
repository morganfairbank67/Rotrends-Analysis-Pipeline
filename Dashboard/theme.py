import streamlit as st

CSS = """
<style>
footer, [data-testid="stHeaderActionElements"] { display: none; }
.block-container { padding-top: 2.5rem; max-width: 1280px; }
h1 { font-size: 1.75rem; letter-spacing: -0.01em; margin-bottom: 0.15rem; }
h2, h3 { letter-spacing: -0.005em; }
[data-testid="stMetricLabel"] { opacity: 0.7; }
[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 8px; }
[data-testid="stSidebar"] h3 { font-size: 0.8rem; text-transform: uppercase;
  letter-spacing: 0.06em; opacity: 0.7; }
.muted { opacity: 0.65; font-size: 0.9rem; margin-bottom: 1.25rem; }
</style>
"""


def apply() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
