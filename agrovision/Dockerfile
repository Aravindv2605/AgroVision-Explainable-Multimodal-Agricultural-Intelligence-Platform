FROM python:3.11-slim

WORKDIR /app

# System deps for rasterio + geopandas
RUN apt-get update && apt-get install -y \
    libgdal-dev gcc g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create output directories
RUN mkdir -p data/raw data/processed data/satellite \
             outputs/models outputs/reports

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
