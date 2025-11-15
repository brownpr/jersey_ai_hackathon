from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from datetime import datetime

from db_service import load_last_n_rows, load_rows_between

app = FastAPI(title="Sensor Readings API")


@app.get("/sensor-readings")
def get_sensor_readings(
    limit: int = Query(100, gt=0, le=10000, description="Number of latest points"),
):
    try:
        rows = load_last_n_rows(limit)
        rows_encoded = jsonable_encoder(rows)
        return JSONResponse(content=rows_encoded)
    except Exception as e:
        # For debugging; in prod you’d log this
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
        )


@app.get("/sensor-readings/range")
def get_sensor_readings_range(
    start: datetime = Query(
        ...,
        description="Start datetime (inclusive), e.g. 2025-11-14T00:00:00",
    ),
    end: datetime = Query(
        ...,
        description="End datetime (exclusive), e.g. 2025-11-15T00:00:00",
    ),
    limit: int = Query(
        10000,
        gt=0,
        le=10_000_000,
        description="Maximum number of points in the range",
    ),
):
    try:
        rows = load_rows_between(start, end, limit)
        return jsonable_encoder(rows)
    except ValueError as ve:
        # por ejemplo cuando start >= end
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))