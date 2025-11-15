import streamlit as st
import pandas as pd


def render(df: pd.DataFrame):
    st.title("📈 Analytics")

    st.write("Some extra plots to show different visualizations.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Metric A distribution")
        st.bar_chart(df["metric_a"])

    with col2:
        st.subheader("Metric B distribution")
        st.bar_chart(df["metric_b"])

    st.subheader("Metric A vs Metric B (scatter-like using data frame)")
    st.write(
        "Streamlit doesn't have a direct scatter shortcut, "
        "but plotting a dataframe still gives a nice exploratory view."
    )

    scatter_df = df[["metric_a", "metric_b"]]
    st.line_chart(scatter_df)
