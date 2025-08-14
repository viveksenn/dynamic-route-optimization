from ortools.constraint_solver import routing_enums_pb2, pywrapcp
from typing import List, Dict
from .models import Order, Vehicle
from .matrix_provider import time_matrix as build_time_matrix

def make_data_model(depot, orders: List[Order], vehicles: List[Vehicle]):
    coords = [(depot.lat, depot.lng)] + [(o.lat, o.lng) for o in orders]
    tm = build_time_matrix(coords, depot.tw_start)

    time_windows = [(depot.tw_start, depot.tw_end)] + [(o.tw_start, o.tw_end) for o in orders]
    service_times = [0] + [o.service_sec for o in orders]
    demands = [0] + [o.demand for o in orders]
    vehicle_caps = [v.capacity for v in vehicles]
    vehicle_tw = [(v.shift_start, v.shift_end) for v in vehicles]

    return dict(
        time_matrix=tm,
        time_windows=time_windows,
        service_times=service_times,
        demands=demands,
        vehicle_capacities=vehicle_caps,
        num_vehicles=len(vehicles),
        depot=0,
        vehicle_time_windows=vehicle_tw
    )

def solve_routes(depot, orders: List[Order], vehicles: List[Vehicle], freeze_next_stops=None, time_limit_sec: int = 10):
    data = make_data_model(depot, orders, vehicles)

    manager = pywrapcp.RoutingIndexManager(len(data["time_matrix"]), data["num_vehicles"], data["depot"])
    routing = pywrapcp.RoutingModel(manager)

    def time_cb(from_index, to_index):
        f = manager.IndexToNode(from_index)
        t = manager.IndexToNode(to_index)
        return data["time_matrix"][f][t] + data["service_times"][f]
    transit = routing.RegisterTransitCallback(time_cb)
    routing.SetArcCostEvaluatorOfAllVehicles(transit)

    # Capacity
    def demand_cb(from_index):
        return data["demands"][manager.IndexToNode(from_index)]
    dcb = routing.RegisterUnaryTransitCallback(demand_cb)
    routing.AddDimensionWithVehicleCapacity(dcb, 0, data["vehicle_capacities"], True, "Capacity")

    # Time windows
    routing.AddDimension(transit, 60*20, 24*3600, False, "Time")
    time_dim = routing.GetDimensionOrDie("Time")
    for node, (start, end) in enumerate(data["time_windows"]):
        idx = manager.NodeToIndex(node)
        time_dim.CumulVar(idx).SetRange(start, end)

    for v in range(data["num_vehicles"]):
        s = routing.Start(v); e = routing.End(v)
        vs, ve = data["vehicle_time_windows"][v]
        time_dim.CumulVar(s).SetRange(vs, ve)
        time_dim.CumulVar(e).SetRange(vs, ve)

    # Soft drop with priority-weighted penalties
    BASE = 60000
    for node in range(1, len(data["time_matrix"])):
        # priority scaling handled externally if needed
        routing.AddDisjunction([manager.NodeToIndex(node)], BASE * 2)

    # Freeze horizon (optional) - demo placeholder
    if freeze_next_stops:
        for v, locked_nodes in freeze_next_stops.items():
            prev = routing.Start(v)
            for node in locked_nodes:
                idx = manager.NodeToIndex(node)
                routing.NextVar(prev).SetValue(idx)
                prev = idx

    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    params.time_limit.FromSeconds(time_limit_sec)

    solution = routing.SolveWithParameters(params)
    if not solution:
        return [], [], {"status": "no_solution"}

    # Extract routes
    routes = []
    visited = set()
    for v in range(data["num_vehicles"]):
        idx = routing.Start(v)
        plan = []
        while not routing.IsEnd(idx):
            node = manager.IndexToNode(idx)
            arr = solution.Value(time_dim.CumulVar(idx))
            plan.append({"node": node, "arrival_epoch": int(arr)})
            visited.add(node)
            idx = solution.Value(routing.NextVar(idx))
        routes.append({"vehicle": v, "stops": plan})

    all_nodes = set(range(1, len(data["time_matrix"])))
    dropped_nodes = sorted(list(all_nodes - (visited - {0})))
    dropped = [orders[n-1].id for n in dropped_nodes]

    kpis = {
        "vehicles_used": sum(1 for r in routes if len(r["stops"]) > 1),
        "served_orders": len(orders) - len(dropped),
        "dropped_orders": len(dropped)
    }
    return routes, dropped, kpis