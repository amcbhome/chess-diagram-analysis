import streamlit as st
import requests
import chess
import chess.svg
from base64 import b64encode
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
        low, high = ratings
        url = f"{base_url}lichess?fen={fen}&ratings={low},{high}"

    response = requests.get(url)

    if response.status_code != 200:
        return None

    return response.json()

# -----------------------------------------------------------
# Page Config
# -----------------------------------------------------------
st.set_page_config(
    page_title="Chess Next Move Comparison",
    page_icon="♟",
    layout="wide"
)

st.title("♟ Chess Position Explorer")

# -----------------------------------------------------------
# Sidebar (simplified)
# -----------------------------------------------------------
with st.sidebar:
    st.header("Input")
    fen = st.text_input(
        "Enter FEN:",
        value="rnbqkbnr/pppp2pp/8/4pp2/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 3"
    )
    run_button = st.button("Run Analysis")

# -----------------------------------------------------------
# EXECUTE QUERIES
# -----------------------------------------------------------
if run_button:

    # --- Display board ---
    try:
        board = chess.Board(fen)
        svg = chess.svg.board(board, size=350)
    except:
        st.error("Invalid FEN.")
        st.stop()

    col_board, col_table = st.columns([2, 3])

    with col_board:
        st.subheader("Board")
        render_svg(svg)

    # --- Databases to query ---
    databases = [
        ("Masters", None),
        ("Lichess 1200–1600", (1200, 1600)),
        ("Lichess 1600–2000", (1600, 2000)),
        ("Lichess 2000–2500", (2000, 2500)),
        ("Lichess 2500+", (2500, 2900)),
    ]

    results = []

    # --- Run all 5 queries ---
    for label, rating_range in databases:

        if label == "Masters":
            data = query_lichess(fen, database="masters")
        else:
            data = query_lichess(fen, database="lichess", ratings=rating_range)

        if not data or "moves" not in data or len(data["moves"]) == 0:
            moves = ["—", "—", "—"]
        else:
            df = pd.DataFrame(data["moves"])
            df["games"] = df["games"].fillna(
                df["white"].fillna(0) + df["draws"].fillna(0) + df["black"].fillna(0)
            )
            df = df.sort_values("games", ascending=False)
            moves = df["san"].head(3).tolist()

            while len(moves) < 3:
                moves.append("—")

        results.append([label] + moves)

    # --- Build final table ---
    table_df = pd.DataFrame(
        results,
        columns=["Database/Rating", "1", "2", "3"]
    ).set_index("Database/Rating")

    with col_table:
        st.subheader("Next Move Table")
        st.table(table_df)

else:
    st.info("Enter a FEN and run the analysis.")


