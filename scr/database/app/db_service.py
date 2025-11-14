from datetime import datetime

from spark_session import spark, jdbc_url, jdbc_properties

def load_last_n_rows(limit: int):
    # IMPORTANTE: que 'limit' venga validado de FastAPI (ya lo tienes con Query)
    query = f"""
        (SELECT
            sensor_name,
            variable,
            value,
            timestamp,
            flagged,
            location_wkt,
            sensor_centroid_longitude,
            ground_height_above_sea_level,
            sensor_centroid_latitude,
            sensor_height_above_ground,
            broker_name,
            raw_id
         FROM sensor_readings
         ORDER BY timestamp DESC
         LIMIT {limit}
        ) AS latest
    """

    df = (
        spark.read
        .format("jdbc")
        .option("url", jdbc_url)
        .option("dbtable", query)   # <- en vez de "sensor_readings"
        .options(**jdbc_properties)
        .load()
    )

    rows = df.toPandas().to_dict(orient="records")
    return rows


def load_rows_between(start: datetime, end: datetime, limit: int):
    # Por seguridad / lógica del endpoint
    if start >= end:
        raise ValueError("start must be earlier than end")

    start_iso = start.isoformat()
    end_iso = end.isoformat()

    query = f"""
        (SELECT
            sensor_name,
            variable,
            value,
            timestamp,
            flagged,
            location_wkt,
            sensor_centroid_longitude,
            ground_height_above_sea_level,
            sensor_centroid_latitude,
            sensor_height_above_ground,
            broker_name,
            raw_id
         FROM sensor_readings
         WHERE timestamp >= '{start_iso}'
           AND timestamp <  '{end_iso}'
         ORDER BY timestamp ASC
         LIMIT {limit}
        ) AS range_data
    """

    df = (
        spark.read
        .format("jdbc")
        .option("url", jdbc_url)
        .option("dbtable", query)
        .options(**jdbc_properties)
        .load()
    )

    pdf = df.toPandas()
    # opcional: normalizar timestamp
    # if "timestamp" in pdf.columns:
    #     pdf["timestamp"] = pdf["timestamp"].astype(str)

    return pdf.to_dict(orient="records")