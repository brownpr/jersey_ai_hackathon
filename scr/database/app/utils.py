import time 
import os

import psycopg2
from psycopg2 import OperationalError
from datetime import datetime, timezone


DB_CONFIG = dict(
    dbname=os.getenv("POSTGRES_DB", "mydb"),
    user=os.getenv("POSTGRES_USER", "myuser"),
    password=os.getenv("POSTGRES_PASSWORD", "mypassword"),
    host=os.getenv("POSTGRES_HOST", "db"),
    port=os.getenv("POSTGRES_PORT", "5432"),
)

def wait_for_db(max_retries=30, delay=1):
    """Poll the DB until it accepts connections or we give up."""

    for attempt in range(1, max_retries + 1):
        try:
            print(f"INFO - Trying to connect to DB (attempt {attempt}/{max_retries})...")
            conn = psycopg2.connect(**DB_CONFIG)
            conn.close()
            print("INFO - Database is ready.")
            return True
        except OperationalError as e:
            print(f"DB not ready yet: {e}")
            time.sleep(delay)
    print("ERROR - Database never became ready, aborting initial CSV load.")
    return False


def wait_for_history(max_attempts: int = 60, delay: int = 10):
    """
    Wait until load_history.py has populated sensor_readings.
    We assume 'history loaded' == table has at least 1 row.
    """
    for attempt in range(1, max_attempts + 1):
        try:
            with psycopg2.connect(**DB_CONFIG) as conn, conn.cursor() as cur:
                cur.execute("SELECT EXISTS (SELECT 1 FROM sensor_readings);")
                (exists,) = cur.fetchone()
            if exists:
                print("INFO - History already loaded (sensor_readings has data).")
                return
            else:
                print(
                    "INFO - History not loaded yet (sensor_readings empty). "
                    "Waiting %s seconds before retrying...", delay
                )
        except psycopg2.Error as e:
            print("WARN - Error checking history table: %s", e)

        time.sleep(delay)

    print(
        "WARN - History still not loaded after %s attempts. "
        "Continuing anyway.", max_attempts
    )

def normalize_for_uo(dt: datetime) -> datetime:
    """
    Convert any datetime into naive UTC with seconds precision,
    like your working notebook example.
    """
    if dt.tzinfo is not None:
        # convert to UTC, then drop tzinfo
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    # drop microseconds for cleaner URLs
    return dt.replace(microsecond=0)