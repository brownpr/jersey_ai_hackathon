import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

from utils.data_utils import fetch_sensor_readings 

def get_data(dt1=None, dt2=None):
    # Safer defaults: last year if dt1 not provided, now for dt2
    if dt2 is None:
        dt2 = datetime.now()
    if dt1 is None:
        dt1 = dt2 - timedelta(days=365)

    return fetch_sensor_readings(dt1, dt2)

def render():
    st.title("📈 Analytics")
    st.write("Data exploration dashboard showing sensor time-series.")

    # --- Date range selector (default: last year) ---
    today = date.today()
    one_year_ago = today - timedelta(days=182)

    start_date, end_date = st.date_input(
        "Date range",
        value=(one_year_ago, today),
        help="Select the date range to load data from the database.",
    )

    # Ensure we always have a proper range
    if isinstance(start_date, date) and isinstance(end_date, date):
        # Convert to datetimes for get_data
        dt1 = datetime.combine(start_date, datetime.min.time())
        dt2 = datetime.combine(end_date, datetime.max.time())
    else:
        # Fallback just in case Streamlit returns something unexpected
        dt1 = datetime.combine(one_year_ago, datetime.min.time())
        dt2 = datetime.combine(today, datetime.max.time())

    # --- Load data from DB for the selected date range ---
    try:
        df = get_data(dt1, dt2)
    except RuntimeError as e:
        st.error(str(e))
        st.stop()
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        st.stop()

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

    # Choose the first sensor as default
    default_sensor = sensor_names[0]

    selected_sensor = st.selectbox(
        "Sensor",
        options=sorted(sensor_names),
        index=list(sorted(sensor_names)).index(default_sensor),
        help="Select which sensor to visualize.",
    )

    # Filter by selected sensor
    df_sensor = df[df["sensor_name"] == selected_sensor]

    if df_sensor.empty:
        st.warning("No data for the selected sensor in this date range.")
        return

    st.markdown(f"### Sensor: `{selected_sensor}`")

    # --- Plot one graph per variable ---
    # Example columns: sensor_name, variable, value, timestamp, flagged, ...
    variables = df_sensor["variable"].dropna().unique()

    if len(variables) == 0:
        st.warning("No variables found for this sensor.")
        return

    for var in sorted(variables):
        var_df = df_sensor[df_sensor["variable"] == var].copy()
        if var_df.empty:
            continue

        # Sort by time and set index for nicer plotting
        var_df = var_df.sort_values("timestamp")
        var_df = var_df.set_index("timestamp")

        st.subheader(f"{var} over time")

        # Only keep the 'value' column for the line chart
        plot_df = var_df[["value"]]

        st.line_chart(plot_df, use_container_width=True)

    # Optionally, show raw filtered data
    with st.expander("Show raw data"):
        st.dataframe(df_sensor)
