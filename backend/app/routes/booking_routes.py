from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.config import get_db
from app.schemas.booking_schema import BookingCreate, BookingResponse, TicketInfo
from app.services.flight_service import create_booking, get_booking_by_pnr, cancel_booking
from app.models.flight import Flight
from app.schemas.booking_schema import BookingUpdate
from fastapi import Body

router = APIRouter()


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking_api(payload: BookingCreate, db: Session = Depends(get_db)):
    # transform payload passengers to expected dict format
    passengers = []
    for p in payload.passengers:
        # build passenger_name from provided fields
        if p.passenger_name:
            pname = p.passenger_name
        else:
            fname = p.first_name or ""
            lname = p.last_name or ""
            pname = f"{fname} {lname}".strip()
        entry = {
            "passenger_name": pname,
            "age": p.age,
            "gender": p.gender,
        }
        # include optional fare/currency if provided
        if getattr(p, 'fare', None) is not None:
            entry['fare'] = p.fare
        if getattr(p, 'currency', None):
            entry['currency'] = p.currency
        passengers.append(entry)
    # resolve flight_number -> flight_id
    flight = db.query(Flight).filter(Flight.flight_number == payload.flight_number).first()
    if not flight:
        raise HTTPException(status_code=400, detail=f"flight '{payload.flight_number}' not found")

    try:
        booking = create_booking(
            db,
            user_id=payload.user_id,
            flight_id=flight.id,
            passengers=passengers,
            seat_ids=payload.seat_ids,
            seat_class=payload.seat_class,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    tickets = [TicketInfo(
            id=t.id,
            booking_id=t.booking_id,
            flight_id=t.flight_id,
            seat_id=t.seat_id,
            passenger_name=t.passenger_name,
            passenger_age=t.passenger_age,
            passenger_gender=t.passenger_gender,
            airline_name=t.airline_name,
            flight_number=t.flight_number,
            route=t.route,
            departure_airport=t.departure_airport,
            arrival_airport=t.arrival_airport,
            departure_city=t.departure_city,
            arrival_city=t.arrival_city,
            departure_time=t.departure_time,
            arrival_time=t.arrival_time,
            seat_number=t.seat_number,
            seat_class=t.seat_class,
            price_paid=t.price_paid,
            currency=t.currency,
            ticket_number=t.ticket_number,
            issued_at=t.issued_at,
        ) for t in booking.tickets]

    return BookingResponse(
        id=booking.id,
        pnr=booking.pnr,
        status=booking.status,
        created_at=booking.created_at,
        tickets=tickets,
    )


@router.get("/{pnr}", response_model=BookingResponse)
def get_booking_api(pnr: str, db: Session = Depends(get_db)):
    booking = get_booking_by_pnr(db, pnr)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    tickets = []
    for t in booking.tickets:
        tickets.append(TicketInfo(
            id=t.id,
            booking_id=t.booking_id,
            flight_id=t.flight_id,
            seat_id=t.seat_id,
            passenger_name=t.passenger_name,
            passenger_age=t.passenger_age,
            passenger_gender=t.passenger_gender,
            airline_name=t.airline_name,
            flight_number=t.flight_number,
            route=t.route,
            departure_airport=t.departure_airport,
            arrival_airport=t.arrival_airport,
            departure_city=t.departure_city,
            arrival_city=t.arrival_city,
            departure_time=t.departure_time,
            arrival_time=t.arrival_time,
            seat_number=t.seat_number,
            seat_class=t.seat_class,
            price_paid=t.price_paid,
            currency=t.currency,
            ticket_number=t.ticket_number,
            issued_at=t.issued_at,
        ))

    return BookingResponse(
        id=booking.id,
        pnr=booking.pnr,
        status=booking.status,
        created_at=booking.created_at,
        tickets=tickets,
    )


@router.delete("/{pnr}")
def cancel_booking_api(pnr: str, db: Session = Depends(get_db)):
    booking = cancel_booking(db, pnr)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {"message": "Booking cancelled", "pnr": booking.pnr}


@router.patch("/{pnr}", response_model=BookingResponse)
def patch_booking_api(pnr: str, payload: BookingUpdate = Body(...), db: Session = Depends(get_db)):
    booking = get_booking_by_pnr(db, pnr)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    data = payload.dict(exclude_unset=True)
    if "status" in data and data.get("status"):
        booking.status = data.get("status")
    db.commit()
    db.refresh(booking)

    tickets = [TicketInfo(
            passenger_name=t.passenger_name,
            seat_number=t.seat_number,
            seat_class=t.seat_class,
            ticket_number=t.ticket_number,
            price_paid=t.price_paid,
        ) for t in booking.tickets]

    return BookingResponse(
        id=booking.id,
        pnr=booking.pnr,
        status=booking.status,
        created_at=booking.created_at,
        tickets=tickets,
    )
