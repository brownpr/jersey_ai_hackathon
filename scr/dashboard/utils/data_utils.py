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

    return df

# ---------- Feature functions ----------

def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()  # avoid mutating upstream cached data

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["hour"] = df["timestamp"].dt.hour
    df["day"] = df["timestamp"].dt.day
    df["weekday"] = df["timestamp"].dt.weekday
    df["month"] = df["timestamp"].dt.month
    df["year"] = df["timestamp"].dt.year
    
    return df


def pivot_variables(df: pd.DataFrame) -> pd.DataFrame:
    pivoted = df.pivot_table(
        index=["hour", "day", "weekday", "month", "year"],
        columns="variable",
        values="value",
        aggfunc="mean"     # in case multiple values per timestamp
    ).reset_index()

    return pivoted


def add_rush_hour_flag(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    hours = df["hour"]

    df["Is Rush Hour"] = (
        ((hours >= 7) & (hours < 10)) |   # Morning rush
        ((hours >= 16) & (hours < 19))    # Evening rush
    ).astype(int)

    return df


def add_is_weekend(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Is Weekend"] = df["weekday"].isin([5, 6]).astype(int)
    return df


@st.cache_data(show_spinner="Building hourly dataframe...")
def get_hour_df(dt1: datetime, dt2: datetime) -> pd.DataFrame:
    """
    Uses get_data, then adds time features, pivots, and adds flags.
    Result is the cached hourly-level dataframe.
    """
    df = get_data(dt1, dt2)

    if df is None or df.empty:
        return df

    df = add_time_features(df)
    df = pivot_variables(df)
    df = add_rush_hour_flag(df)
    df = add_is_weekend(df)

    return df