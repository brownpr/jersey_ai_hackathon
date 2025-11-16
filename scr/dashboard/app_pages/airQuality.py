import datetime

import streamlit as st
import pandas as pd

from utils.model_utils import call_airQuality_model


def render():
    st.title("🚦 Congestion Prediction (Air Quality Model)")

    st.write(
        "Adjust the input parameters below and run a prediction using the air quality-based congestion model."
    )

    # Date (used only to help set weekend flag)
    st.subheader("📅 Date")

    date = st.date_input("Select date", datetime.date.today())
    weekday = date.weekday()  # Monday=0, Sunday=6
    st.caption(f"Detected weekday: {weekday} (0=Mon, 6=Sun)")

    # Flags
    st.subheader("🚩 Flags")

    # default weekend based on selected date
    is_weekend = st.checkbox("Weekend?", value=weekday >= 5)

    # Air Quality & Environment Features
    st.subheader("🌫️ Air Quality & Environment")

    col1, col2, col3 = st.columns(3)

    with col1:
        humidity = st.number_input("Humidity", min_value=0.0, value=50.0, step=1.0)
        no = st.number_input("NO", min_value=0.0, value=10.0, step=1.0)
        no2 = st.number_input("NO2", min_value=0.0, value=10.0, step=1.0)
        o3 = st.number_input("O3", min_value=0.0, value=10.0, step=1.0)

    with col2:
        pm4 = st.number_input("PM 4", min_value=0.0, value=5.0, step=0.5)
        pm1 = st.number_input("PM1", min_value=0.0, value=5.0, step=0.5)
        pm10 = st.number_input("PM10", min_value=0.0, value=10.0, step=0.5)
        pm25 = st.number_input("PM2.5", min_value=0.0, value=10.0, step=0.5)

    with col3:
        pressure = st.number_input("Pressure", min_value=800.0, value=1013.0, step=1.0)
        temperature = st.number_input("Temperature (°C)", min_value=-20.0, value=20.0, step=0.5)
        congestion = st.number_input("Current Congestion", min_value=0.0, value=50.0, step=1.0)

    # Prepare payload (must match FastAPI aliases exactly)
    payload = {
        "samples": [
            {
                "Humidity": humidity,
                "NO": no,
                "NO2": no2,
                "O3": o3,
                "PM 4": pm4,
                "PM1": pm1,
                "PM10": pm10,
                "PM2.5": pm25,
                "Pressure": pressure,
                "Temperature": temperature,
                "is_weekend": int(is_weekend),
                "Congestion": congestion,
            }
        ]
    }

    # Prediction Button
    st.markdown("---")

    if st.button("🚀 Run Prediction"):
        try:
            with st.spinner("Calling air quality prediction API..."):
                response_json = call_airQuality_model(payload)

            predictions = response_json.get("predictions", [])[0]

            if not predictions:
                st.warning("API returned no predictions.")
                return

            # For this model: 1D regression output per sample
            pred_value = predictions[0]

            st.success("Prediction received from the model.")
            st.metric(
                label="Predicted congestion",
                value=f"{pred_value:.2f}",
            )

            # Optionally show raw response
            with st.expander("🔍 Raw API response"):
                st.json(response_json)

        except Exception as e:
            st.error(f"Error contacting API: {e}")

    else:
        st.info("Set your inputs, then click **Run Prediction**.")
