import logging

logging.getLogger("tornado.application").setLevel(logging.ERROR)
logging.getLogger("tornado.general").setLevel(logging.ERROR)

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests

def fetch_sensor_readings(start: datetime, end: datetime, limit: int = 1_000_000):
    """
    Calls the /sensor-readings/range endpoint and returns the JSON response.

    Args:
        start (datetime): Start datetime (inclusive)
        end (datetime): End datetime (exclusive)
        limit (int): Maximum number of points to return

    Returns:
        list or dict: Parsed JSON response from the API
    """
    url = "http://db-api:8000/sensor-readings/range"
    
    params = {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "limit": limit,
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        # FastAPI typically returns JSON with a "detail" field on 422
        try:
            error_json = response.json()
        except Exception:
            error_json = response.text

        raise RuntimeError(
            f"API error {response.status_code} when calling {url} "
            f"with params={params}.\nDetails: {error_json}"
        )

    data = response.json()

    # If no data, return empty df
    if not data:
        return pd.DataFrame()

    # Convert to DataFrame
    df = pd.DataFrame(data)

    return df

@st.cache_data(show_spinner="Loading data from database...")
def get_data(dt1: datetime, dt2: datetime):
    """
    Cached wrapper around fetch_sensor_readings.
    Ensures dataframe column names are clean + standardised.
    """
    df = fetch_sensor_readings(dt1, dt2)

    if df is None or df.empty:
        return df

    # --- Normalize column names ---
    df = df.rename(columns=lambda c: c.strip() if isinstance(c, str) else c)

    # --- Ensure Timestamp is datetime ---
    if "Timestamp" in df.columns:
        if not pd.api.types.is_datetime64_any_dtype(df["Timestamp"]):
            df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
        df = df.dropna(subset=["Timestamp"])

    return df