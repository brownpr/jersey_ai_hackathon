import streamlit as st
import pandas as pd


def render(df: pd.DataFrame):
    st.title("📊 Overview")

    st.write("Basic overview of synthetic metrics over time.")

    col1, col2, col3 = st.columns(3)
    last_row = df.iloc[-1]

    col1.metric("Metric A (latest)", f"{last_row['metric_a']:.2f}")
    col2.metric("Metric B (latest)", f"{last_row['metric_b']:.2f}")
    col3.metric("Metric C (latest)", f"{last_row['metric_c']:.2f}")

    st.subheader("Metric A vs Metric B (line chart)")
    chart_df = df.set_index("date")[["metric_a", "metric_b"]]
    st.line_chart(chart_df)

    st.subheader("Raw data")
    st.dataframe(df.tail(10), use_container_width=True)
