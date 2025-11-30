from pydantic import BaseModel
from typing import Optional


class SeatCreate(BaseModel):
    flight_id: int
    seat_number: str
    seat_class: Optional[str] = "Economy"
    is_available: Optional[bool] = True


class SeatUpdate(BaseModel):
    seat_number: Optional[str] = None
    seat_class: Optional[str] = None
    is_available: Optional[bool] = None


class SeatResponse(BaseModel):
    id: int
    flight_id: int
    seat_number: str
    seat_class: Optional[str]
    is_available: bool

    class Config:
        from_attributes = True


class SeatBulkCreate(BaseModel):
    flight_number: str
    seat_class: Optional[str] = "Economy"
    seat_numbers: Optional[list[str]] = None
    count: Optional[int] = None


class SeatBulkUpdateItem(BaseModel):
    id: int
    seat_number: Optional[str] = None
    seat_class: Optional[str] = None
    is_available: Optional[bool] = None


class SeatBulkUpdate(BaseModel):
    seats: list[SeatBulkUpdateItem]


class SeatBulkDelete(BaseModel):
    seat_ids: Optional[list[int]] = None
    flight_number: Optional[str] = None
    seat_class: Optional[str] = None


class SeatAvailabilityItem(BaseModel):
    seat_class: str
    available_count: int
    booked_count: int
    available_seats: list[SeatResponse]
    booked_seats: list[SeatResponse]


class SeatAvailabilityResponse(BaseModel):
    flight_id: int
    flight_number: str
    classes: list[SeatAvailabilityItem]

    class Config:
        from_attributes = True


class SeatOverviewResponse(BaseModel):
    model: Optional[str] = None
    flight_no: str
    total_capacity: int
    available_capacity: int
    economy_count: int
    available_economy_count: int
    premium_economy_count: int
    available_premium_economy_count: int
    business_count: int
    available_business_count: int
    first_count: int
    available_first_count: int

    class Config:
        from_attributes = True


class SeatClassBatch(BaseModel):
    seat_class: Optional[str] = "Economy"
    seat_numbers: Optional[list[str]] = None
    count: Optional[int] = None


class SeatBulkByFlightCreate(BaseModel):
    airline_code: str
    flight_number: str
    classes: list[SeatClassBatch]
