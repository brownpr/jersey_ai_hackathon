import logging

logging.getLogger("tornado.application").setLevel(logging.ERROR)
logging.getLogger("tornado.general").setLevel(logging.ERROR)

import streamlit as st
from datetime import datetime, timedelta, date

from utils.data_utils import get_data
from app_pages import overview, analytics, prediction, chatbot

# ----------------- CONFIG -----------------
st.set_page_config(
    page_title="Demo Dashboard with Chatbot",
    layout="wide",
)

# ----------------- SHARED DATA (INIT ON STARTUP) -----------------
def init_data():
    """Load data once per user session and store it in session_state."""
    if "df" in st.session_state:
        return  # already initialized for this session

    today = date.today()
    start = today - timedelta(days=182)  # ~ last 6 months; change if you want

    dt1 = datetime.combine(start, datetime.min.time())
    dt2 = datetime.combine(today, datetime.max.time())

    # call your utils.get_data
    df = get_data(dt1, dt2)

    st.session_state.df = df
    st.session_state.start_date = start
    st.session_state.end_date = today


def main():
    st.sidebar.title("Demo Navigation")
    page = st.sidebar.radio(
        "Go to",
        ("Overview", "Analytics", "Prediction", "Chatbot"),
    )

    init_data()

    if page == "Overview":
        overview.render()
    elif page == "Analytics":
        analytics.render()
    elif page == "Prediction":
        prediction.render()
    elif page == "Chatbot":
        chatbot.render()


if __name__ == "__main__":
    main()
