import logging

logging.getLogger("tornado.application").setLevel(logging.ERROR)
logging.getLogger("tornado.general").setLevel(logging.ERROR)

import streamlit as st
import pandas as pd

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


def render():
    st.title("📊 Overview")

    st.write("Basic overview of data over time.")

    # col1, col2, col3 = st.columns(3)
    # last_row = df.iloc[-1]

    # col1.metric("Metric A (latest)", f"{last_row['metric_a']:.2f}")
    # col2.metric("Metric B (latest)", f"{last_row['metric_b']:.2f}")
    # col3.metric("Metric C (latest)", f"{last_row['metric_c']:.2f}")

    # st.subheader("Metric A vs Metric B (line chart)")
    # chart_df = df.set_index("date")[["metric_a", "metric_b"]]
    # st.line_chart(chart_df)

    # st.subheader("Raw data")
    # st.dataframe(df.tail(10), use_container_width=True)
