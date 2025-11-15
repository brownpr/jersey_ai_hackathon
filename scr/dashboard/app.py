import streamlit as st

from utils.data_utils import generate_time_series
from app_pages import overview, analytics, prediction, chatbot

# ----------------- CONFIG -----------------
st.set_page_config(
    page_title="Demo Dashboard with Chatbot",
    layout="wide",
)

# ----------------- SHARED DATA -----------------
# Cached function inside data_utils, so this call is cheap
df = generate_time_series(60)


def main():
    st.sidebar.title("Demo Navigation")
    page = st.sidebar.radio(
        "Go to",
        ("Overview", "Analytics", "Prediction", "Chatbot"),
    )

    if page == "Overview":
        overview.render(df)
    elif page == "Analytics":
        analytics.render()
    elif page == "Prediction":
        prediction.render()
    elif page == "Chatbot":
        chatbot.render()


if __name__ == "__main__":
    main()
