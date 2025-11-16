import datetime

import streamlit as st
import pandas as pd 

from utils.model_utils import call_model_api  

def render():
    st.title("🚦 Congestion Prediction")

    st.write("Adjust the input parameters below and run a prediction using the congestion model.")

    # Date & Time Section
    st.subheader("📅 Date & Time")

    col1, col2 = st.columns(2)

    with col1:
        date = st.date_input("Select date", datetime.date.today())

    with col2:
        hour = st.slider("Hour of day", min_value=0, max_value=23, value=12)

    day = date.day
    month = date.month
    year = date.year
    weekday = date.weekday()  # Monday=0, Sunday=6

    st.caption(f"Detected weekday: {weekday} (0=Mon, 6=Sun)")

    # Flags
    st.subheader("🚩 Flags")

    colf1, colf2 = st.columns(2)

    with colf1:
        is_weekend = st.checkbox("Weekend?", value=weekday >= 5)

    with colf2:
        # Auto-rush-hour suggestion (you can override)
        default_rush = (7 <= hour <= 9) or (16 <= hour <= 19)
        is_rush_hour = st.checkbox("Rush hour?", value=default_rush)

    # Traffic Plate Metrics
    st.subheader("🧮 Traffic Metrics")

    colm1, colm2, colm3, colm4 = st.columns(4)

    with colm1:
        plates_in = st.number_input("Plates In", min_value=0.0, value=10.0, step=1.0)

    with colm2:
        plates_matching = st.number_input("Plates Matching", min_value=0.0, value=3.0, step=1.0)

    with colm3:
        plates_out = st.number_input("Plates Out", min_value=0.0, value=10.0, step=1.0)

    with colm4:
        journey_time = st.number_input(
            "Journey Time",
            min_value=0.0,
            value=110.0,
            step=1.0,
        )
    # Prepare payload
    payload = {
        "samples": [
            {
                "hour": hour,
                "day": day,
                "weekday": weekday,
                "month": month,
                "year": year,
                "plates_in": plates_in,
                "plates_matching": plates_matching,
                "plates_out": plates_out,
                "is_rush_hour": int(is_rush_hour),
                "is_weekend": int(is_weekend),
                "journey_time": journey_time,
            }
        ]
    }

    # Prediction Button
    st.markdown("---")

    if st.button("🚀 Run Prediction"):
        try:
            with st.spinner("Calling prediction API..."):
                response_json = call_model_api(payload)

            predictions = response_json.get("predictions", [])[0]

            if not predictions:
                st.warning("API returned no predictions.")
                return

            # Handle 24-hour prediction array
            n_preds = len(predictions)

            if n_preds == 24:
                # Build timestamps for next 24 hours starting from selected date+hour
                start_dt = datetime.datetime(year, month, day, hour)
                timestamps = [
                    start_dt + datetime.timedelta(hours=i) for i in range(24)
                ]

                df = pd.DataFrame({
                    "timestamp": timestamps,
                    "congestion": predictions
                }).set_index("timestamp")

                st.success(
                    f"Predicted congestion for the next 24 hours "
                    f"(starting {start_dt.strftime('%Y-%m-%d %H:%M')})"
                )

                # Show first-hour prediction prominently
                st.metric(
                    label="Next hour congestion",
                    value=f"{predictions[0]:.2f}"
                )

                st.line_chart(df["congestion"], height=300)

            else:
                # Fallback if model returns a different length
                st.warning(f"Model returned {n_preds} predictions instead of 24.")
                df = pd.DataFrame({
                    "step": list(range(n_preds)),
                    "congestion": predictions,
                }).set_index("step")
                st.line_chart(df["congestion"], height=300)

            # Optionally show raw response
            with st.expander("🔍 Raw API response"):
                st.json(response_json)

        except Exception as e:
            st.error(f"Error contacting API: {e}")

    else:
        st.info("Set your inputs, then click **Run Prediction**.")
