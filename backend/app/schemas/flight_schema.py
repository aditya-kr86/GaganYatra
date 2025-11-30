from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class FlightCreate(BaseModel):
    # Accept friendly identifiers (codes/models) instead of internal IDs
    airline_code: str
    aircraft_model: str
    flight_number: str
    departure_airport_code: str
    arrival_airport_code: str
    departure_time: datetime
    arrival_time: datetime
    base_price: float


class FlightUpdate(BaseModel):
    # Friendly, client-facing update fields only (no internal IDs)
    airline: str | None = None
    aircraft_model: str | None = None
    flight_number: str | None = None
    source: str | None = None
    destination: str | None = None
    departure_time: datetime | None = None
    arrival_time: datetime | None = None
    base_price: float | None = None


class FlightResponse(BaseModel):
    id: int
    airline: str
    source: str
    flight_number: str
    aircraft_model: str | None = None
    destination: str
    departure_time: datetime
    arrival_time: datetime
    base_price: float
    seats_left: int

    class Config:
        orm_mode = True
