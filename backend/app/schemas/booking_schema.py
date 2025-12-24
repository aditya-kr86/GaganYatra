from pydantic import BaseModel, root_validator, ConfigDict
from typing import Optional, List
from datetime import datetime


class Passenger(BaseModel):
    passenger_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    # NOTE: fare is NO LONGER accepted; will be computed from dynamic pricing


class BookingCreate(BaseModel):
    user_id: int
    flight_number: str
    departure_date: str  # YYYY-MM-DD to validate correct flight and date
    passengers: List[Passenger]
    seat_class: Optional[str] = None

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "user_id": 1,
                "flight_number": "AI-123",
                "departure_date": "2025-12-15",
                "passengers": [
                    {"passenger_name": "John Doe", "age": 30, "gender": "M"}
                ],
                "seat_class": "Economy"
            }
        })


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
    payment_required: float
    currency: str
    ticket_number: Optional[str] = None
    issued_at: Optional[datetime] = None


class TicketInfoSimplified(BaseModel):
    """Simplified ticket format for user-facing responses (booking confirmation)."""
    flight_seat: str  # Format: "SEAT_CLASS - SEAT_NUMBER" (e.g., "EC - 32")
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
    payment_required: float
    currency: str
    ticket_number: Optional[str] = None
    issued_at: Optional[datetime] = None


class BookingResponse(BaseModel):
    pnr: Optional[str] = None
    booking_reference: Optional[str] = None
    status: str
    created_at: datetime
    total_fare: float  # Total fare for all passengers (computed from dynamic price)
    tickets: List[TicketInfoSimplified]
    # Payment info (returned after successful payment)
    transaction_id: Optional[str] = None
    paid_amount: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class BookingUpdate(BaseModel):
    status: Optional[str] = None
