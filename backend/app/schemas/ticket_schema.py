from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class TicketResponse(BaseModel):
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
    seat_number: Optional[str]
    seat_class: str
    payment_required: float
    currency: str
    ticket_number: Optional[str]
    issued_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
