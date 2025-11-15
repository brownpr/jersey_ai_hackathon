import logging

logging.getLogger("tornado.application").setLevel(logging.ERROR)
logging.getLogger("tornado.general").setLevel(logging.ERROR)

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

from utils.data_utils import get_data  # cached function above


def render():
    st.title("📈 Analytics")
    st.write("Data exploration dashboard showing sensor time-series.")

    # --- Defaults for date range in session_state (shared across pages) ---
    today = date.today()
    default_start = today - timedelta(days=182)  # ~6 months

    if "start_date" not in st.session_state:
        st.session_state.start_date = default_start
    if "end_date" not in st.session_state:
        st.session_state.end_date = today

    # Use a key so Streamlit can track widget state
    start_date, end_date = st.date_input(
        "Date range",
        value=(st.session_state.start_date, st.session_state.end_date),
        help="Select the date range to load data from the database.",
        key="date_range",
    )

    # Keep session_state in sync with widget
    st.session_state.start_date = start_date
    st.session_state.end_date = end_date

    # Convert to datetimes for querying
    if isinstance(start_date, date) and isinstance(end_date, date):
        dt1 = datetime.combine(start_date, datetime.min.time())
        dt2 = datetime.combine(end_date, datetime.max.time())
    else:
        dt1 = datetime.combine(default_start, datetime.min.time())
        dt2 = datetime.combine(today, datetime.max.time())

    # --- Load / reload logic ---
    # First time: if we don't have df in session_state, load it
    if "df" not in st.session_state:
        try:
            st.session_state.df = get_data(dt1, dt2)
        except RuntimeError as e:
            st.error(str(e))
            st.stop()
        except Exception as e:
            st.error(f"Unexpected error: {e}")
            st.stop()

    # Button that *forces* reload from DB for the selected dates
    if st.button("🔄 Reload data from database"):
        try:
            st.session_state.df = get_data(dt1, dt2)
            st.success("Data reloaded.")
        except RuntimeError as e:
            st.error(str(e))
            st.stop()
        except Exception as e:
            st.error(f"Unexpected error: {e}")
            st.stop()

    df = st.session_state.df

    if df.empty:
        st.warning("No data found for the selected date range.")
        return

    # Make sure timestamp is datetime
    if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        df["timestamp"] = pd.to_datetime(df["timestamp"])

    # --- Sensor dropdown (from sensor_name.unique()) ---
    sensor_names = df["sensor_name"].dropna().unique()

    if len(sensor_names) == 0:
        st.warning("No sensors found in the data.")
        return

    default_sensor = sensor_names[0]

    selected_sensor = st.selectbox(
        "Sensor",
        options=sorted(sensor_names),
        index=list(sorted(sensor_names)).index(default_sensor),
        help="Select which sensor to visualize.",
        key="sensor_select",
    )

    # Filter by selected sensor
    df_sensor = df[df["sensor_name"] == selected_sensor]

    if df_sensor.empty:
        st.warning("No data for the selected sensor in this date range.")
        return

    st.markdown(f"### Sensor: `{selected_sensor}`")

    # --- Plot one graph per variable ---
    variables = df_sensor["variable"].dropna().unique()

    if len(variables) == 0:
        st.warning("No variables found for this sensor.")
        return

    for var in sorted(variables):
        var_df = df_sensor[df_sensor["variable"] == var].copy()
        if var_df.empty:
            continue

        var_df = var_df.sort_values("timestamp").set_index("timestamp")

        st.subheader(f"{var} over time")
        st.line_chart(var_df[["value"]], use_container_width=True)

    with st.expander("Show raw data"):
        st.dataframe(df_sensor)
