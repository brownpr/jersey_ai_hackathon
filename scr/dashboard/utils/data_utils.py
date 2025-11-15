import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests

@st.cache_data
def generate_time_series(days: int = 30) -> pd.DataFrame:
    """Generate simple synthetic time-series data for the demo."""
    now = datetime.now()
    dates = [now - timedelta(days=i) for i in range(days)][::-1]
    data = {
        "date": dates,
        "metric_a": np.random.normal(loc=50, scale=10, size=days).cumsum(),
        "metric_b": np.random.normal(loc=30, scale=5, size=days).cumsum(),
        "metric_c": np.random.normal(loc=10, scale=3, size=days).cumsum(),
    }
    df = pd.DataFrame(data)
    return df


def fetch_sensor_readings(start: datetime, end: datetime, limit: int = 100000):
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