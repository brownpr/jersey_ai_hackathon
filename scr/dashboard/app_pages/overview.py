import logging

logging.getLogger("tornado.application").setLevel(logging.ERROR)
logging.getLogger("tornado.general").setLevel(logging.ERROR)

import streamlit as st
import pandas as pd

from utils.ui_utils import run_latest_predictions_ui

def render():
    st.title("📊 Overview")

    st.subheader("🔮 Latest 24h model forecast")

    run_latest_predictions_ui()
    st.markdown("---")

    st.subheader("🔎 Basic overview of data over time.")

    # --- Load cached data --- 
    df = st.session_state.df
    if df is None or df.empty:
        st.info("No data available.")
        return
    
    # st.write("Columns in df:", list(df.columns))


    # Make sure timestamp is datetime
    if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        df["timestamp"] = pd.to_datetime(df["timestamp"])

    # --- Global summary metrics ---
    total_points = len(df)
    num_sensors = df["sensor_name"].nunique()
    num_variables = df["variable"].nunique()
    first_ts = df["timestamp"].min()
    last_ts = df["timestamp"].max()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Data points", f"{total_points:,}")
    col2.metric("Unique sensors", num_sensors)
    col3.metric("Unique variables", num_variables)
    col4.metric("Date start", f"{first_ts.strftime('%Y-%m-%d %H:%M')}")
    col5.metric("Date end", f"{last_ts.strftime('%Y-%m-%d %H:%M')}")

    st.markdown("---")

    st.subheader("Average sensor readings")

    window_end = last_ts

    avg_by_var = (
        df.groupby("variable", as_index=False)
        .agg(
            Average_value=("value", "mean"),
            Count=("value", "count")
        )
    )
    # Show table
    st.dataframe(avg_by_var, use_container_width=True)

    # Plot bar chart of averages per variable
    st.bar_chart(
        avg_by_var.set_index("variable")["Average_value"]
    )

    st.markdown("---")
    st.subheader("First 25 rows of raw data")
    st.dataframe(df.head(25), use_container_width=True)
