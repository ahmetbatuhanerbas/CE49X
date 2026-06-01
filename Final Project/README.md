# CE49X Final Project
## Conflict Situation Monitoring for Maritime Shipping
### Correlating Satellite Thermal Anomalies with War-Related Events

**Student:** Ahmet Batuhan Erbaş  
**Course:** CE49X – Introduction to Data Science for Civil Engineering  
**Institution:** Boğaziçi University — Spring 2026  
**Instructor:** Dr. Eyuphan Koç  

---

## Project Structure

```
Final Project/
├── notebooks/
│   ├── final_project_analysis.ipynb   ← Main analysis notebook
│   └── dashboard.png                  ← Dashboard figure (300 DPI)
├── scripts/
│   ├── collect_firms_data.py          ← Download NASA FIRMS data
│   ├── collect_news_data.py           ← Download GDELT news data
│   ├── collect_google_news_rss.py     ← Download Google News RSS data
│   ├── clean_data.py                  ← Clean + process all raw data
│   ├── setup_database.py              ← Create PostgreSQL tables & load data
│   └── build_notebook.py             ← Regenerate the notebook from source
├── data/
│   ├── raw/                           ← Raw downloaded CSVs (not committed)
│   └── processed/                     ← Cleaned CSVs (not committed)
├── figures/                           ← All saved plot images
├── reports/
│   └── data_cleaning_report.md
├── config/
│   ├── regions.json                   ← 6 selected conflict/shipping regions
│   └── project_config.json            ← Date range, API source config
├── .env                               ← FIRMS API key (not committed)
├── .env.example                       ← Template for .env
├── requirements.txt
└── README.md
```

---

## Quick Start

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Add your NASA FIRMS API key

Copy `.env.example` to `.env` and fill in your key:

```
FIRMS_MAP_KEY=your_key_here
```

Get a free key at: https://firms.modaps.eosdis.nasa.gov/api/area

### 3. Collect raw data

```bash
python scripts/collect_firms_data.py
python scripts/collect_google_news_rss.py
```

### 4. Clean the data

```bash
python scripts/clean_data.py
```

### 5. Set up the PostgreSQL database (requires Docker Desktop)

#### Install Docker Desktop
Download from: https://www.docker.com/products/docker-desktop/  
Verify it is running: `docker --version`

#### Start the PostgreSQL container

```bash
docker run --name ce49x-postgres \
    -e POSTGRES_USER=ce49x \
    -e POSTGRES_HOST_AUTH_METHOD=trust \
    -e POSTGRES_DB=conflict_monitoring \
    -p 5432:5432 \
    -d postgres:16
```

#### Load data into the database

```bash
python scripts/setup_database.py
```

#### Verify tables

```bash
docker exec -it ce49x-postgres psql -U ce49x -d conflict_monitoring -c "\dt"
```

Expected tables:
| Table | Contents |
|---|---|
| `firms_detections` | Cleaned FIRMS thermal detection records |
| `news_articles` | Conflict news articles with metadata |
| `thermal_events` | Daily thermal event summaries per region |
| `event_matches` | Thermal event to news matching results |

#### Stop / restart the container later

```bash
docker stop ce49x-postgres
docker start ce49x-postgres
```

### 6. Run the notebook

Open `notebooks/final_project_analysis.ipynb` and run all cells top to bottom.

---

## Data Sources

| Source | Type | Coverage |
|---|---|---|
| NASA FIRMS VIIRS S-NPP SP | Satellite thermal anomalies | 2024-01-01 to 2026-03-31 |
| NASA FIRMS VIIRS S-NPP NRT | Satellite thermal anomalies | 2026-04-01 to 2026-05-24 |
| GDELT Doc API v2 | Conflict news metadata | 2024 |
| Google News RSS | Conflict news metadata | 2025–2026 |

API endpoint: `https://firms.modaps.eosdis.nasa.gov/api/area`  
GDELT: `https://api.gdeltproject.org/api/v2/doc/doc`

---

## Regions of Interest

| Region | Bounding Box | Shipping Relevance |
|---|---|---|
| Ukraine / Black Sea | 27°E–42.5°E, 40°N–53°N | Grain exports, energy routes |
| Red Sea / Yemen | 32°E–45.5°E, 10°N–23.5°N | Suez Canal, Houthi attacks |
| Gaza / Israel / Lebanon | 33°E–37.5°E, 29°N–35°N | Eastern Mediterranean |
| Persian Gulf / Iraq / Iran | 38°E–60°E, 23°N–38°N | Oil exports, Strait of Hormuz |
| Sudan / Red Sea Corridor | 21.5°E–38.5°E, 8°N–23.5°N | Red Sea shipping lanes |
| Libya / Mediterranean | 9°E–26°E, 19°N–34°N | Oil infrastructure, Mediterranean routes |

---

## Requirements

See `requirements.txt`. Key packages:

```
pandas, numpy, requests, python-dotenv,
matplotlib, seaborn, scikit-learn, scipy,
sqlalchemy, psycopg2-binary, jupyter, nbconvert
```
