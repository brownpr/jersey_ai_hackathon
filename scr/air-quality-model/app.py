import math
from typing import List

from fastapi import FastAPI
from pydantic import BaseModel, conlist
import xgboost as xgb
import numpy as np

app = FastAPI(title="XGBoost Model API")

# ----- Feature schema -----
class Sample(BaseModel):
    hour: int
    day: int
    weekday: int
    month: int
    year: int
    plates_in: float
    plates_matching: float
    plates_out: float
    is_rush_hour: int  
    is_weekend: int    


class PredictRequest(BaseModel):
    samples: List[Sample]


class PredictResponse(BaseModel):
    predictions: List[List[float]]


# ----- Load model -----
model = xgb.XGBRegressor()
model.load_model("airQualityModel.json")

# Define the exact feature order expected by the model
FEATURE_ORDER = [
    "sin_hour", "cos_hour",
    "sin_day", "cos_day",
    "sin_weekday", "cos_weekday",
    "sin_month", "cos_month",
    "plates_in",
    "plates_matching",
    "plates_out",
    "is_rush_hour",
    "is_weekend",
]

def encode_cyclic(value, max_value):
    """Map value in [0, max_value) into sin/cos cyclic representation."""
    angle = 2 * math.pi * value / max_value
    return math.sin(angle), math.cos(angle)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    # Convert list[Sample] -> 2D numpy array in the correct column order
    rows = []
    for s in request.samples:

        sin_hour,   cos_hour   = encode_cyclic(s.hour, 24)
        sin_weekday, cos_weekday = encode_cyclic(s.weekday, 7)
        sin_month, cos_month   = encode_cyclic(s.month - 1, 12)   # month 1–12 → 0–11
        sin_day, cos_day       = encode_cyclic(s.day - 1, 31)     # days 1–31 → 0–30

        features = {
            "sin_hour": sin_hour,
            "cos_hour": cos_hour,
            "sin_weekday": sin_weekday,
            "cos_weekday": cos_weekday,
            "sin_month": sin_month,
            "cos_month": cos_month,
            "sin_day": sin_day,
            "cos_day": cos_day,
            "plates_in": s.plates_in,
            "plates_matching": s.plates_matching,
            "plates_out": s.plates_out,
            "is_rush_hour": s.is_rush_hour,
            "is_weekend": s.is_weekend
        }


        row = [features[name] for name in FEATURE_ORDER]
        rows.append(row)

    X = np.array(rows, dtype=float)
    preds = model.predict(X)

    return PredictResponse(predictions=preds.tolist())
