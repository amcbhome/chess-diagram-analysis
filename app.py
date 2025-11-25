import streamlit as st
import requests
import chess
import chess.svg
from base64 import b64encode
import altair as alt
import pandas as pd

# -----------------------------------------------------------
# Helper: Render SVG chessboard
# -----------------------------------------------------------
def render_svg(svg):
    """Render SVG chessboard in Streamlit."""
    b64 = b64encode(svg.encode("utf-8")).decode("utf-8")
    html = f'<img src="data:image/svg+xml;base64,{b64}"/>'
    st.write(html, unsafe_allow_html=True)


# -----------------------------------------------------------
# Query Lichess Opening Explorer API
# -----------------------------------------------------------
def query_lichess(fen, database="masters", ratings=None):
    base_url = "https://explorer.lichess.ovh/"

    if database == "masters":
        url = f"{base_url}masters?fen={fen}"

    elif database == "lichess":
        if ratings:
            low, high = ratings
            url = f"{base_url}lichess?fen={fen}&ratings={low},{high}"
        else:
            url = f"{base_url}lichess?fen={fen}"

    response = requests.get(url)

    if response.status_code != 200:
        return None

    return response.json()


# -----------------------------------------------------------
# Streamlit Page Config
# -----------------------------------------------------------
st.set_page_config(
    page_title="Chess Next-Move Explorer",
    page_icon="♟",
    layout="wide"
)

st.title("♟ Chess Position Explorer — Masters & Lichess Databases")


# -----------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------
with st.sidebar:
    st.header("Position & Database Settings")

    fen = st.text_input(
        "Enter FEN:",
        value="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    )

    db_choice = st.selectbox(
        "Choose database:",
        ["Masters", "Lichess"]
    )

    rating_range = None
    if db_choice == "Lichess":
        st.subheader("Rating Filter")
        rating_selector = st.selectbox(
            "Select rating range:",
            ["1200–1600", "1600–2000", "2000–2500", "2500+"]
        )

        if rating_selector == "1200–1600":
            rating_range = (1200, 1600)
        elif rating_selector == "1600–2000":
            rating_range = (1600, 2000)
        elif rating_selector == "2000–2500":
            rating_range = (2000, 2500)
        elif rating_selector == "2500+":
            rating_range = (2500, 2900)

    st.markdown("---")
    run_button = st.button("Run Analysis")


# -----------------------------------------------------------
# USER CLICKED "RUN ANALYSIS"
# -----------------------------------------------------------
if run_button:

    # Render board
    try:
        board = chess.Board(fen)
        svg = chess.svg.board(board, size=450)
        st.subheader("Bo

