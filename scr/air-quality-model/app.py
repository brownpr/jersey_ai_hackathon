import math
from typing import List

from fastapi import FastAPI
from pydantic import BaseModel, Field
import xgboost as xgb
import numpy as np

app = FastAPI(title="XGBoost Model API")

# ----- Feature schema -----
class Sample(BaseModel):
    # environmental / air-quality features
    humidity: float = Field(alias="Humidity")
    no: float = Field(alias="NO")
    no2: float = Field(alias="NO2")
    o3: float = Field(alias="O3")
    pm4: float = Field(alias="PM 4")       # alias for column "PM 4"
    pm1: float = Field(alias="PM1")
    pm10: float = Field(alias="PM10")
    pm25: float = Field(alias="PM2.5")     # alias for column "PM2.5"
    pressure: float = Field(alias="Pressure")
    temperature: float = Field(alias="Temperature")

    # other features
    is_weekend: int
    congestion: float = Field(alias="Congestion")

    class Config:
        # Optional: if you want to *forbid* any extra fields (e.g. sin_hour, etc.)
        extra = "forbid"


class PredictRequest(BaseModel):
    samples: List[Sample]


class PredictResponse(BaseModel):
    # assuming 1D regression output per sample
    predictions: List[List[float]]


# ----- Load model -----
model = xgb.XGBRegressor()
model.load_model("airQualityModel.json")

# Define the exact feature order expected by the model
FEATURE_ORDER = [
    "humidity", "no", "no2", "o3",
    "pm4", "pm1", "pm10", "pm25",
    "pressure", "temperature",
    "is_weekend",
    "congestion",
]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    rows = []
    for s in request.samples:
        # Build row in the exact order expected by the model
        row = [getattr(s, name) for name in FEATURE_ORDER]
        rows.append(row)

    X = np.array(rows, dtype=float)
    preds = model.predict(X)   # shape (n_samples,) for regressor

    # return as simple 1D list of floats
    return PredictResponse(predictions=preds.tolist())
