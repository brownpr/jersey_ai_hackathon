import requests


def call_model_api(payload, timeout=10):
    API_URL = "http://congestion-model-api:8001/predict"

    response = requests.post(API_URL, json=payload, timeout=timeout)
    response.raise_for_status()  
    return response.json()
