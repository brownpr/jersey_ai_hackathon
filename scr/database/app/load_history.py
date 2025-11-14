import glob
import os
import time
import csv
import io

import psycopg2
from psycopg2 import OperationalError

# Read connection config from environment, with sane defaults for docker-compose
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


if not wait_for_db():
    raise SystemExit(1)


csv_files = glob.glob("historical/*.csv")  # folder containing CSVs

if not csv_files:
    print("WARN - No CSV files found in 'historical/' – nothing to load.")
    raise SystemExit(0)

columns = (
    "sensor_name, variable, value, timestamp, flagged, "
    "location_wkt, sensor_centroid_longitude, ground_height_above_sea_level, "
    "sensor_centroid_latitude, sensor_height_above_ground, "
    "broker_name, raw_id"
)

print(f"Found {len(csv_files)} CSV file(s). Starting load...")

conn = psycopg2.connect(**DB_CONFIG)

with conn:
    with conn.cursor() as cur:
        for csv_path in csv_files:
            print(f"INFO - Loading {csv_path} ...")

            # Read original CSV, drop first column, write to in-memory CSV
            output = io.StringIO()
            writer = csv.writer(output)

            with open(csv_path, "r", newline="") as f:
                reader = csv.reader(f)
                for row in reader:
                    if not row:
                        continue
                    # Drop the first column (the leading index / id)
                    new_row = row[1:]
                    writer.writerow(new_row)

            # Reset pointer to start so COPY can read it
            output.seek(0)

            # Stream modified CSV into Postgres
            cur.copy_expert(
                f"""
                COPY sensor_readings ({columns})
                FROM STDIN
                WITH (FORMAT csv, HEADER true)
                """,
                output,
            )


print("INFO - Done loading all historical CSVs!")
