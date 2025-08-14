from pydantic import BaseModel, Field
from typing import List, Optional

class Depot(BaseModel):
    lat: float
    lng: float
    tw_start: int
    tw_end: int

class Order(BaseModel):
    id: str
    lat: float
    lng: float
    demand: int = 1
    service_sec: int = 120
    tw_start: int
    tw_end: int
    priority: int = 2

class Vehicle(BaseModel):
    vehicle_id: str
    capacity: int = 10
    shift_start: int
    shift_end: int

class OptimizeRequest(BaseModel):
    depot: Depot
    orders: List[Order]
    vehicles: List[Vehicle]
    freeze_horizon: int = Field(1, ge=0, le=3)

class StopPlan(BaseModel):
    node: int
    arrival_epoch: int
    order_id: Optional[str]

class VehiclePlan(BaseModel):
    vehicle: str
    stops: List[StopPlan]

class OptimizeResponse(BaseModel):
    routes: List[VehiclePlan]
    dropped_orders: List[str]
    kpis: dict