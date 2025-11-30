from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.config import get_db
from app.models.seat import Seat
from app.models.flight import Flight
from app.models.airline import Airline
from app.schemas.seat_schema import SeatResponse, SeatAvailabilityResponse, SeatAvailabilityItem

router = APIRouter()


@router.get("/", response_model=list[SeatResponse])
def list_seats(db: Session = Depends(get_db)):
    return db.query(Seat).all()
@router.get("/{airline_code}/{flight_number}", response_model=SeatAvailabilityResponse)
def seats_by_airline_and_flight(airline_code: str, flight_number: str, db: Session = Depends(get_db)):
    fl = db.query(Flight).join(Airline).filter(Flight.flight_number == flight_number, func.lower(Airline.code) == airline_code.strip().lower()).first()
    if not fl:
        raise HTTPException(status_code=404, detail="flight not found for airline")

    classes = db.query(Seat.seat_class).filter(Seat.flight_id == fl.id).distinct().all()
    class_list = [c[0] for c in classes if c[0]]
    items = []
    for cls in class_list:
        available_q = db.query(Seat).filter(Seat.flight_id == fl.id, func.lower(Seat.seat_class) == func.lower(cls), Seat.is_available == True).order_by(Seat.id.asc())
        booked_q = db.query(Seat).filter(Seat.flight_id == fl.id, func.lower(Seat.seat_class) == func.lower(cls), Seat.is_available == False).order_by(Seat.id.asc())
        available = available_q.all()
        booked = booked_q.all()
        items.append(SeatAvailabilityItem(
            seat_class=cls,
            available_count=len(available),
            booked_count=len(booked),
            available_seats=available,
            booked_seats=booked,
        ))

    return SeatAvailabilityResponse(flight_id=fl.id, flight_number=fl.flight_number, classes=items)
