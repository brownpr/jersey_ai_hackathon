# Install
Prior to running install docker desktop
```
docker-compose up --build

docker exec -it ollama ollama pull llama3.2
```

# Endpoints
```
# Call endpoint to get the last limit=100 datapoints 
http://localhost:8000/sensor-readings?limit=100

# Call endpoint to get data between two dates
http://localhost:8000/sensor-readings/range?start=2025-09-14T00:00:00&end=2025-09-15T00:00:00
```

# Dashboard
```
http://localhost:8501/
```