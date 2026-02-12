# Weather–Accident Data Pipeline

A Dockerized data engineering pipeline that ingests NOAA weather station metadata and daily weather observations, preparing the data for downstream analysis of weather impacts on traffic accidents.

This project is built incrementally using a **Bronze → Silver → Gold** data modeling approach and is intentionally scoped to demonstrate real-world ELT pipeline design, not just analysis scripts.

---

## Current Scope (Implemented)

### ✅ Station Metadata
- Download NOAA GHCN station metadata (fixed-width format)
- Convert raw metadata into structured CSV
- Load raw station data into PostgreSQL (**Bronze layer**)
- Clean and normalize station records into a queryable **Silver layer**
- Archive ingested source files for traceability

### 🚧 Weather Data (Partial)
- Download selected NOAA `.dly` daily weather files
- Convert `.dly` records into CSV subsets (station-scoped)
- Store raw daily weather data in landing area
- **Database ingestion for daily weather is not yet implemented**

---

## Data Sources

- **NOAA Global Historical Climatology Network (GHCN)**
  - Station metadata: `ghcnd-stations.txt`
  - Daily weather observations: `.dly` files
  - Source: https://www.ncei.noaa.gov/pub/data/ghcn/daily/

---

## Architecture Overview

```
NOAA (raw)
   ↓
Landing (CSV / raw extracts)
   ↓
PostgreSQL Bronze (raw, append-only)
   ↓
PostgreSQL Silver (cleaned, typed)
   ↓
Future: Gold / Analytics
```

---

## Tech Stack

- Python 3.11
- Pandas
- PostgreSQL 16
- SQLAlchemy
- Docker & Docker Compose
- Jupyter Notebook

---

## Repository Structure

```
.
├── data/
│   ├── landing/
│   │   ├── stations/
│   │   ├── weather/
│   │   └── accidents/
│   ├── archive/
│   │   └── stations/
│   │   ├── weather/
│   │   └── accidents/
│   └── quarantine/
│
├── notebooks/
│   ├── 01_download_station.ipynb
│   ├── 02_ingest_station.ipynb
│   ├── 03_clean_station.ipynb
│   ├── 04_download_weather.ipynb
│   └── ghcn_meta/
│
├── sql/
│   │   init.sql
│
├── docker-compose.yml
├── requirements.txt
├── .env
└── README.md
```

---

## Notebook Workflow

1. **01_download_station.ipynb**
   - Downloads and converts NOAA station metadata

2. **02_ingest_station.ipynb**
   - Loads station CSV into `bronze.stations` and archives the file

3. **03_clean_station.ipynb**
   - Cleans and filters station data into `silver.stations`

4. **04_download_weather.ipynb**
   - Downloads `.dly` daily weather files and converts to CSV

---

## Database Layers

### Bronze: `bronze.stations`
- Raw station metadata
- Loose typing
- Append-only
- Includes ingestion metadata

### Silver: `silver.stations`
- Cleaned and typed station reference table
- One row per station
- Designed to join with weather and accident fact tables

---

## Setup Instructions

### 1️⃣ Clone the repository
```bash
git clone <repo-url>
cd weather-accident-data-pipeline
```

### 2️⃣ Create `.env` file
```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=postgres
```

### 3️⃣ Start services
```bash
docker compose up -d
```

### 4️⃣ Open Jupyter
```
http://localhost:8888
```

### 5️⃣ Run notebooks in order
1. `01_download_station.ipynb`
2. `02_ingest_station.ipynb`
3. `03_clean_station.ipynb`
4. `04_download_weather.ipynb`

---

## What Is Not Implemented Yet

- Weather data ingestion into PostgreSQL
- Weather Bronze/Silver fact tables
- Accident data ingestion
- Weather–accident correlation logic
- Gold / analytics layer

---

## Status

🚧 **Active Development**
