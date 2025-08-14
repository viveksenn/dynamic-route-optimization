# Dynamic Route Optimization (TDVRPTW) — FastAPI + Streamlit + BIG Dataset

A demo-ready system for **time-dependent vehicle routing with time windows** using **Google OR-Tools**, with a **FastAPI** backend, **Streamlit** dashboard, **Docker/Compose** deployment, and a **large synthetic dataset** for stress-testing.

## Run locally
```bash
pip install -r requirements.txt
uvicorn services.optimizer.main:app --reload --port 8000
# in another terminal
streamlit run dashboard/streamlit_app.py
```

## Run with Docker Compose
```bash
docker compose up --build
# API:     http://localhost:8000
# UI:      http://localhost:8501
```

## Folders
- `services/optimizer` — FastAPI app + OR-Tools solver
- `mock_providers/traffic.py` — time-of-day traffic simulator (replace with Google/Mapbox/OSRM later)
- `dashboard/streamlit_app.py` — UI to run scenarios and visualize routes
- `data/` — BIG synthetic dataset (orders_12000.csv, vehicles_120.csv)

## Notes
- The **BIG dataset** is for demo/benchmarks; solving 12k orders exactly is computationally heavy.
  Use it to sample subsets (e.g., 200–800 stops) or run per-cluster demos.
- For production demos, set `time_limit_sec` low (5–30s) and use **rolling-horizon** and **clustering**.
