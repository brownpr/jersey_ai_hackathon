import streamlit as st
from utils.model_utils import predict_24h_from_latest

def run_latest_predictions_ui():
    if "df_hour" not in st.session_state:
        st.error("df_hour not found in session_state.")
        return

    df_hour = st.session_state.df_hour

    st.subheader("df_hour preview")
    st.dataframe(df_hour.head(), use_container_width=True)

    # Call pure prediction function
    forecast_df = predict_24h_from_latest(df_hour)

    st.subheader("24-step forecast from latest row")
    st.dataframe(forecast_df, use_container_width=True)

    # Optional: quick plots
    st.line_chart(
        forecast_df.set_index("horizon")[["air_quality_pred", "congestion_pred"]]
    )

    return forecast_df