import os

from pyspark.sql import SparkSession, functions as F

PG_HOST = os.getenv("PG_HOST", "db")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_DB   = os.getenv("PG_DB", "mydb")
PG_USER = os.getenv("PG_USER", "myuser")
PG_PASS = os.getenv("PG_PASS", "mypassword")

spark = (
    SparkSession.builder
    .appName("sensor-readings-api")
    .config(
        "spark.driver.extraClassPath",
        "/opt/spark/jars/postgresql-42.7.3.jar",
    )
    .getOrCreate()
)

jdbc_url = f"jdbc:postgresql://{PG_HOST}:{PG_PORT}/{PG_DB}"
jdbc_properties = {
    "user": PG_USER,
    "password": PG_PASS,
    "driver": "org.postgresql.Driver",
}