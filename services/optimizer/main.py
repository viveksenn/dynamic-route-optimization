from fastapi import FastAPI
from .models import OptimizeRequest, OptimizeResponse, VehiclePlan, StopPlan
from .solver import solve_routes

app = FastAPI(title="Dynamic Route Optimizer", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/optimize", response_model=OptimizeResponse)
def optimize(req: OptimizeRequest):
    routes, dropped, kpis = solve_routes(req.depot, req.orders, req.vehicles, freeze_next_stops=None, time_limit_sec=10)
    plans = []
    for r in routes:
        vname = req.vehicles[r["vehicle"]].vehicle_id
        stops = []
        for s in r["stops"]:
            order_id = None
            if s["node"] >= 1:
                order_id = req.orders[s["node"]-1].id
            stops.append(StopPlan(node=s["node"], arrival_epoch=s["arrival_epoch"], order_id=order_id))
        plans.append(VehiclePlan(vehicle=vname, stops=stops))
    return OptimizeResponse(routes=plans, dropped_orders=dropped, kpis=kpis)