import requests
import pandas as pd

def call_congestion_model(payload, timeout=10):
    API_URL = "http://congestion-model-api:8001/predict"

    response = requests.post(API_URL, json=payload, timeout=timeout)
    response.raise_for_status()  
    return response.json()


def call_airQuality_model(payload, timeout=10):
    API_URL = "http://air-quality-model-api:8002/predict"

    response = requests.post(API_URL, json=payload, timeout=timeout)
    response.raise_for_status()  
    return response.json()



def predict_24h_from_latest(df_hour: pd.DataFrame) -> pd.DataFrame:
    """
    Uses the latest row of df_hour to call both models and return
    a 24-step forecast dataframe.

    Returns a DataFrame like:
        horizon  air_quality_pred  congestion_pred
        1        ...
        2        ...
        ...
        24       ...
    """
    if df_hour is None or len(df_hour) == 0:
        raise ValueError("df_hour is empty or None")

    latest = df_hour.iloc[-1]

    # ---- Build Air Quality payload ----
    air_payload = {
        "samples": [
            {
                "Humidity": latest["Humidity"],
                "NO": latest["NO"],
                "NO2": latest["NO2"],
                "O3": latest["O3"],
                "PM 4": latest["PM 4"],
                "PM1": latest["PM1"],
                "PM10": latest["PM10"],
                "PM2.5": latest["PM2.5"],
                "Pressure": latest["Pressure"],
                "Temperature": latest["Temperature"],
                "is_weekend": int(latest["Is Weekend"]),
                "Congestion": latest["Congestion"],
            }
        ]
    }

    # ---- Build Congestion payload ----
    cong_payload = {
        "samples": [
            {
                "hour": latest["hour"],
                "day": latest["day"],
                "weekday": latest["weekday"],
                "month": latest["month"],
                "year": latest["year"],
                "plates_in": latest["Plates In"],
                "plates_matching": latest["Plates Matching"],
                "plates_out": latest["Plates Out"],
                "is_rush_hour": int(latest["Is Rush Hour"]),
                "is_weekend": int(latest["Is Weekend"]),
            }
        ]
    }

    # ---- Call models ----
    air_pred_raw = call_airQuality_model(air_payload)
    cong_pred_raw = call_congestion_model(cong_payload)

    # Assuming both are list-like of length 24
    air_series = pd.Series(air_pred_raw, name="air_quality_pred")
    cong_series = pd.Series(cong_pred_raw, name="congestion_pred")

    if len(air_series) != 24 or len(cong_series) != 24:
        raise ValueError(
            f"Expected length-24 predictions, got "
            f"{len(air_series)} and {len(cong_series)}."
        )

    forecast_df = pd.DataFrame(
        {
            "horizon": range(1, 25),  # 1..24
            "air_quality_pred": air_series.values,
            "congestion_pred": cong_series.values,
        }
    )

    return forecast_df

