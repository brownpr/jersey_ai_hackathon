import requests


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