import streamlit as st
import requests
import chess
import chess.svg
from base64 import b64encode

# -----------------------------
# Helper: Render board SVG
# -----------------------------
def render_svg(svg):
    """Renders the given svg string."""
    b64 = b64encode(svg.encode("utf-8")).decode("utf-8")
    html = f'<img src="data:image/svg+xml;base64,{b64}"/>'
    st.write(html, unsafe_allow_html=True)


# -----------------------------
# Query Lichess Opening Explorer
# -----------------------------
def query_lichess(fen, database="masters", ratings=None):
    base_url = "https://explorer.lichess.ovh/"

    if database == "masters":
        url = f"{base_url}masters?fen={fen}"

    elif database == "lichess":
        # ratings = [low, high]
        if ratings:
            url = f"{base_url}lichess?fen={fen}&ratings={ratings[0]},{ratings[1]}"
        else:
            url = f"{base_url}lichess?fen={fen}"

    response = requests.get(url)
    if response.status_code != 200:
        return None
    return response.json()


# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(
    page_title="Chess Next-Move Explorer",
    page_icon="♟",
    layout="wide"
)

st.title("♟ Chess Position Explorer — Masters & Lichess Databases")

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
    query_button = st.button("Run Analysis")


# -----------------------------
# When user clicks "Run Analysis"
# -----------------------------
if query_button:

    # Display board
    try:
        board = chess.Board(fen)
        svg = chess.svg.board(board, size=450)
        st.subheader("Board Position")
        render_svg(svg)
    except:
        st.error("Invalid FEN. Please correct it.")
        st.stop()

    st.subheader("Database Results")

    # Query database
    if db_choice == "Masters":
        data = query_lichess(fen, database="masters")

    else:
        data = query_lichess(fen, database="lichess", ratings=rating_range)

    if not data:
        st.error("No data returned. Try another position.")
        st.stop()

    moves = data.get("moves", [])

    if len(moves) == 0:
        st.warning("No moves available for this database/position.")
        st.stop()

    # Show move list
    st.write("### Move Statistics")
    move_rows = []

    for m in moves:
        move_rows.append({
            "Move": m["san"],
            "White Wins %": round(m["white"], 1),
            "Draw %": round(m["draws"], 1),
            "Black Wins %": round(m["black"], 1),
            "Games": m["games"]
        })

    st.dataframe(move_rows, use_container_width=True)

    # Best move highlight
    best = max(moves, key=lambda x: x["games"])
    st.success(
        f"Most played move: **{best['san']}** ({best['games']} games)"
    )

else:
    st.info("Enter a FEN and select database options in the sidebar to begin.")
