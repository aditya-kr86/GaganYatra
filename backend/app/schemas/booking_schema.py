from pydantic import BaseModel, root_validator
from typing import Optional, List
from datetime import datetime


class Passenger(BaseModel):
    # Accept either a full passenger_name or first_name+last_name
    passenger_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    # Optional per-passenger fare override and currency
    fare: Optional[float] = None
    currency: Optional[str] = None

    @root_validator(pre=True)
    def ensure_name(cls, values):
        # require either passenger_name or both first_name and last_name
        if not values.get('passenger_name'):
            if not (values.get('first_name') and values.get('last_name')):
                raise ValueError('passenger must have passenger_name or first_name and last_name')
        return values


class BookingCreate(BaseModel):
    user_id: int
    # Use flight_number for client-friendly booking requests
    flight_number: str
    passengers: List[Passenger]
    # Optional: preferred seat class (e.g., "Economy", "Business")
    seat_class: Optional[str] = None
    # Optional: explicit seat ids (one per passenger) — if provided length must match passengers
    seat_ids: Optional[List[int]] = None

    class Config:
        schema_extra = {
            "example": {
                "user_id": 1,
                "flight_number": "AI-123",
                "passengers": [
                    {"first_name": "John", "last_name": "Doe", "age": 30, "gender": "M"}
                ],
                "seat_class": "Economy",
                "seat_ids": []
            }
        }


class TicketInfo(BaseModel):
    id: int
    booking_id: int
    flight_id: int
    seat_id: Optional[int]
    passenger_name: str
    passenger_age: Optional[int]
    passenger_gender: Optional[str]
    airline_name: str
    flight_number: str
    route: str
    departure_airport: str
    arrival_airport: str
    departure_city: str
    arrival_city: str
    departure_time: datetime
    arrival_time: datetime
    seat_number: str
    seat_class: str
    price_paid: float
    currency: str
    ticket_number: str
    issued_at: datetime


class BookingResponse(BaseModel):
    id: int
    pnr: str
    status: str
    created_at: datetime
    tickets: List[TicketInfo]

    class Config:
        orm_mode = True


class BookingUpdate(BaseModel):
    status: Optional[str] = None
