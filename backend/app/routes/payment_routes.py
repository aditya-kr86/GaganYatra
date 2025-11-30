from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from app.config import get_db
from app.schemas.payment_schema import PaymentCreate, PaymentResponse, PaymentUpdate
from app.schemas.booking_schema import BookingResponse, TicketInfo
from app.models.booking import Booking
from app.services.flight_service import create_payment, get_payment_by_transaction

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_payment_api(payload: PaymentCreate, db: Session = Depends(get_db)):
    # very small validation
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="amount must be > 0")

    # use booking_reference only (booking_id removed from API)
    identifier = payload.booking_reference
    try:
        tx = create_payment(db, booking_reference=identifier, amount=payload.amount, method=payload.method)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    # If payment failed, return informative payload with transaction id so client can retry
    if tx.status != "Success":
        return {"transaction_id": tx.transaction_id, "status": tx.status, "detail": "payment failed or insufficient amount"}

    # load updated booking (create_payment issues tickets and PNR on success)
    booking = db.query(Booking).filter(Booking.id == tx.booking_id).first()
    if not booking:
        raise HTTPException(status_code=500, detail="payment recorded but booking not found")

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
        booking_reference=booking.booking_reference,
        status=booking.status,
        created_at=booking.created_at,
        tickets=tickets,
        transaction_id=tx.transaction_id,
        paid_amount=tx.amount,
    )


@router.get("/{transaction_id}", response_model=PaymentResponse)
def get_payment_api(transaction_id: str, db: Session = Depends(get_db)):
    tx = get_payment_by_transaction(db, transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail="transaction not found")
    return tx


@router.patch("/{transaction_id}", response_model=PaymentResponse)
def patch_payment_api(transaction_id: str, payload: PaymentUpdate = Body(...), db: Session = Depends(get_db)):
    tx = get_payment_by_transaction(db, transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail="transaction not found")
    data = payload.dict(exclude_unset=True)
    if "status" in data and data.get("status"):
        tx.status = data.get("status")
    db.commit()
    db.refresh(tx)
    return tx
