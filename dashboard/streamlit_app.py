import streamlit as st
import pandas as pd
import requests, time
import pydeck as pdk
from datetime import datetime

st.set_page_config(page_title="Dynamic Route Optimizer", layout="wide")
st.title("🚚 Dynamic Route Optimization — BIG Data Demo")

API = st.sidebar.text_input("Optimizer API URL", "http://localhost:8000")
now = int(time.time())

depot_lat = st.sidebar.number_input("Depot Lat", value=28.6139, format="%.6f")
depot_lng = st.sidebar.number_input("Depot Lng", value=77.2090, format="%.6f")
window_hr = st.sidebar.slider("Depot time window (hours)", 4, 12, 10)

orders_path = st.sidebar.text_input("Orders CSV", "data/orders_12000.csv")
vehicles_path = st.sidebar.text_input("Vehicles CSV", "data/vehicles_120.csv")
sample_n = st.sidebar.slider("Sample N orders (for solve)", 100, 1200, 400, step=50)

def to_abs(epoch, mins): return epoch + int(mins*60)

if st.button("Optimize"):
    orders_df = pd.read_csv(orders_path).sample(sample_n, random_state=42)
    vehicles_df = pd.read_csv(vehicles_path)

    orders_payload = []
    for _, r in orders_df.iterrows():
        orders_payload.append(dict(
            id=str(r["id"]), lat=float(r["lat"]), lng=float(r["lng"]),
            demand=int(r["demand"]), service_sec=int(r["service_sec"]),
            tw_start=to_abs(now, float(r["tw_start_offset_min"])),
            tw_end=to_abs(now, float(r["tw_end_offset_min"])),
            priority=int(r["priority"]),
        ))
    vehicles_payload = []
    for _, r in vehicles_df.iterrows():
        vehicles_payload.append(dict(
            vehicle_id=str(r["vehicle_id"]), capacity=int(r["capacity"]),
            shift_start=to_abs(now, float(r["shift_start_offset_min"])),
            shift_end=to_abs(now, float(r["shift_end_offset_min"])),
        ))

    req = dict(
        depot=dict(lat=depot_lat, lng=depot_lng, tw_start=now, tw_end=now + window_hr*3600),
        orders=orders_payload,
        vehicles=vehicles_payload,
        freeze_horizon=1
    )

    with st.spinner("Solving..."):
        resp = requests.post(f"{API}/optimize", json=req, timeout=120)
    if resp.status_code != 200:
        st.error(f"API error: {resp.status_code} {resp.text}")
        st.stop()
    data = resp.json()
    st.success("Done")
    st.write(data.get("kpis", {}))

    rows = []
    for r in data["routes"]:
        for s in r["stops"]:
            rows.append(dict(vehicle=r["vehicle"], node=s["node"], order_id=s.get("order_id"), arrival_epoch=s["arrival_epoch"]))
    st.dataframe(pd.DataFrame(rows), use_container_width=True, height=300)

    # Map
    oid2coord = {str(o["id"]):(o["lat"],o["lng"]) for o in orders_payload}
    layers = []
    for r in data["routes"]:
        path = [[depot_lat, depot_lng]]
        for s in r["stops"]:
            if s["order_id"]:
                lat,lng = oid2coord[s["order_id"]]; path.append([lat,lng])
        path.append([depot_lat, depot_lng])
        layers.append(pdk.Layer("PathLayer", data=[{"path": path}], get_path="path", width_min_pixels=2))
    st.pydeck_chart(pdk.Deck(initial_view_state=pdk.ViewState(latitude=depot_lat, longitude=depot_lng, zoom=9), layers=layers))