from datetime import datetime, timedelta, timezone
import os
import traceback
from requests.exceptions import HTTPError


import psycopg2
from psycopg2.extras import execute_values
import uo_pyfetch

from utils import wait_for_db, wait_for_history, normalize_for_uo

PG_HOST = os.getenv("PG_HOST", "db")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_DB   = os.getenv("PG_DB", "mydb")
PG_USER = os.getenv("PG_USER", "myuser")
PG_PASS = os.getenv("PG_PASS", "mypassword")

def get_variable_data(dt1: datetime, dt2: datetime, bbox):
    sensor_data_df = uo_pyfetch.get_sensor_data(
        start=dt1,
        end=dt2,
        variables=None,  # or list of vars if you want to filter
        bbox=bbox,
        limit=1000
    )
    return sensor_data_df


def insert_sensor_data(sensor_df):
    """
    Insert or update sensor readings into PostgreSQL.
    Assumes all columns align exactly with the DB schema.
    """

    # Convert PySpark → pandas if needed
    if hasattr(sensor_df, "toPandas"):
        pdf = sensor_df.toPandas()
    else:
        pdf = sensor_df 

    if pdf is None or pdf.empty:
        print("No rows to insert into sensor_readings.")
        return
    
    # Convert UO column names to lowercase
    pdf.columns = pdf.columns.str.lower()

    cols = [
        "sensor_name", "variable", "value", "timestamp", "flagged",
        "location_wkt", "sensor_centroid_longitude",
        "ground_height_above_sea_level", "sensor_centroid_latitude",
        "sensor_height_above_ground", "broker_name", "raw_id",
    ]

    # Make sure all required columns exist
    missing = [c for c in cols if c not in pdf.columns]
    if missing:
        raise ValueError(f"Missing columns in sensor_df: {missing}")

    insert_sql = f"""
        INSERT INTO sensor_readings ({",".join(cols)})
        VALUES %s
    """

    rows = [tuple(row[col] for col in cols) for _, row in pdf.iterrows()]

    with psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASS,
    ) as conn, conn.cursor() as cur:
        execute_values(cur, insert_sql, rows)

    print(f"Inserted {len(rows)} rows into sensor_readings.")


def get_last_timestamp():
    """
    Return the last timestamp in sensor_readings, or None if table is empty.
    """
    with psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASS,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT MAX(timestamp) FROM sensor_readings;")
            (dt1,) = cur.fetchone()
    return dt1


def run():
    print("INFO - Updating sensor database ...")
    dt2 = datetime.now(timezone.utc)

    dt1 = get_last_timestamp()
    if dt1 is None:
        # Fallback if table is empty: e.g., pull last hour
        dt1 = dt2 - timedelta(hours=1)
        print(f"No existing data. Using dt1={dt1} as start time instead.")
    else:
        print(f"Found existing data. Last register was at: {dt1}")

    bbox = [-1.652756, 54.973377, -1.620483, 54.983721]

    # Normalize the dts for uo fetch
    dt1 = normalize_for_uo(dt1)
    dt2 = normalize_for_uo(dt2)

    try:
        sensor_df = get_variable_data(dt1, dt2, bbox=bbox)
        insert_sensor_data(sensor_df)
        print("INFO - Sensor database updated correctly.")
    except HTTPError as e:
        print("ERROR - UO API HTTP error while fetching sensor data: %s", e)
    except Exception as e:
        print("ERROR - Error updating sensor database:")
        traceback.print_exc()


if __name__ == "__main__":
    if not wait_for_db():
        raise SystemExit(1)

    wait_for_history()

    run()
