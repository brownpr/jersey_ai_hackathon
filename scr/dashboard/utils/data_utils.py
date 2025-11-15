import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


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
