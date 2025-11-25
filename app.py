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

st.title("♟ Chess Position Explorer")


# -----------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------
with st.sidebar:
    st.header("Settings")

    fen = st.text_input(
        "Enter FEN:",
        value="rnbqkbnr/pppp2pp/8/4pp2/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 3"
    )

    db_choice = st.selectbox(
        "Choose database:",
        ["Masters", "Lichess"]
    )

    rating_range = None
    rating_label = ""

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

        rating_label = rating_selector

    st.markdown("---")
    run_button = st.button("Run Analysis")


# -----------------------------------------------------------
# USER CLICKED "RUN ANALYSIS"
# -----------------------------------------------------------
if run_button:

    # Render board
    try:
        board = chess.Board(fen)
        svg = chess.svg.board(board, size=400)
    except Exception:
        st.error("Invalid FEN. Please correct it.")
        st.stop()

    # Layout: Board left, Table right
    col1, col2 = st.columns([2, 3])

    with col1:
        st.subheader("Board Position")
        render_svg(svg)

    # Query database
    if db_choice == "Masters":
        data = query_lichess(fen, database="masters")
        row_label = "Masters"
    else:
        data = query_lichess(fen, database="lichess", ratings=rating_range)
        row_label = f"Lichess {rating_label}"

    if not data:
        st.error("No data returned. Try a different position or database.")
        st.stop()

    moves = data.get("moves", [])
    if len(moves) == 0:
        st.warning("No moves found for this position in the selected database.")
        st.stop()

    # Prepare move data for charts + table
    chart_rows = []

    for m in moves:
        white = m.get("white", 0) or 0
        draws = m.get("draws", 0) or 0
        black = m.get("black", 0) or 0
        games = m.get("games", white + draws + black)

        if games > 0:
            white_pct = 100 * white / games
            draw_pct = 100 * draws / games
            black_pct = 100 * black / games
        else:
            white_pct = draw_pct = black_pct = 0.0

        chart_rows.append({
            "Move": m.get("san", ""),
            "White Wins": white,
            "Draws": draws,
            "Black Wins": black,
            "Games": games,
            "White %": round(white_pct, 1),
            "Draw %": round(draw_pct, 1),
            "Black %": round(black_pct, 1)
        })

    df = pd.DataFrame(chart_rows)

    # -----------------------------------------------------------
    # NEXT-MOVE TABLE (Top 3 moves)
    # -----------------------------------------------------------
    with col2:
        st.subheader("Next Move Summary")

        top3 = df.sort_values("Games", ascending=False).head(3)
        top_moves = top3["Move"].tolist()

        # Fill missing cells if <3 moves
        while len(top_moves) < 3:
            top_moves.append("—")

        table_df = pd.DataFrame({
            "Database/Rating": [row_label],
            "1": [top_moves[0]],
            "2": [top_moves[1]],
            "3": [top_moves[2]]
        }).set_index("Database/Rating")

        st.table(table_df)

    # -----------------------------------------------------------
    # MAIN CHART (Horizontal bars)
    # -----------------------------------------------------------
    st.write("### Move Statistics (Interactive Chart)")

    games_chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            y=alt.Y("Move:N", sort="-x", title="Move"),
            x=alt.X("Games:Q", title="Games Played"),
            tooltip=["Move", "Games", "White %", "Draw %", "Black %"]
        )
        .properties(
            width="container",
            height=450,
            title="Move Popularity by Games Played"
        )
    )

    st.altair_chart(games_chart, use_container_width=True)

    # -----------------------------------------------------------
    # BEST MOVE SUMMARY
    # -----------------------------------------------------------
    best = df.sort_values("Games", ascending=False).iloc[0]
    st.success(f"Most played move: **{best['Move']}** ({best['Games']:,} games)")

else:
    st.info("Enter a FEN and select database options to begin.")


