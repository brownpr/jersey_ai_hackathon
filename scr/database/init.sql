CREATE TABLE IF NOT EXISTS sensor_readings (
    sensor_name TEXT,
    variable TEXT,
    value DOUBLE PRECISION,
    timestamp TIMESTAMPTZ,
    flagged BOOLEAN,
    location_wkt TEXT,
    sensor_centroid_longitude DOUBLE PRECISION,
    ground_height_above_sea_level DOUBLE PRECISION,
    sensor_centroid_latitude DOUBLE PRECISION,
    sensor_height_above_ground DOUBLE PRECISION,
    broker_name TEXT,
    raw_id BIGINT
);