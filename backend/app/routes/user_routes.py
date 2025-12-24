from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.config import get_db
from app.models.user import User
from app.schemas.user_schema import UserCreate, UserUpdate, UserResponse

router = APIRouter()


@router.get("/", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()


@router.post("/", response_model=UserResponse, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    # NOTE: password is stored in `password_hash` as provided for demo purposes.
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="email already registered")
    user = User(full_name=payload.full_name, email=payload.email, password_hash=payload.password, role=payload.role, airline_id=payload.airline_id, airport_id=payload.airport_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="user not found")
    return u


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="user not found")
    data = payload.dict(exclude_unset=True)
    for k, v in data.items():
        if k == "password":
            setattr(u, "password_hash", v)
        else:
            setattr(u, k, v)
    db.commit()
    db.refresh(u)
    return u


@router.patch("/{user_id}")
def patch_user(user_id: int, payload: UserUpdate = Body(...), db: Session = Depends(get_db)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="user not found")
    data = payload.dict(exclude_unset=True)
    for k, v in data.items():
        if k == "password":
            setattr(u, "password_hash", v)
        else:
            setattr(u, k, v)
    db.commit()
    db.refresh(u)
    return u


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="user not found")
    db.delete(u)
    db.commit()
    return {"message": "user deleted"}


@router.get("/{user_id}/bookings")
def get_user_booking_history(
    user_id: int,
    status: str | None = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get booking history for a user with optional status filter.
    
    Args:
        user_id: User ID
        status: Optional booking status filter (e.g., 'Confirmed', 'Cancelled', 'Payment Pending')
        limit: Maximum number of bookings to return (default: 50)
    """
    from app.models.booking import Booking
    from app.schemas.booking_schema import BookingResponse, TicketInfoSimplified
    
    # Verify user exists
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="user not found")
    
    # Query bookings
    query = db.query(Booking).filter(Booking.user_id == user_id)
    
    # Apply status filter if provided
    if status:
        query = query.filter(Booking.status == status)
    
    # Order by most recent first
    query = query.order_by(Booking.created_at.desc())
    
    # Apply limit
    bookings = query.limit(limit).all()
    
    # Format response
    results = []
    for booking in bookings:
        total_fare = sum(t.payment_required for t in booking.tickets) if booking.tickets else 0.0
        
        # Get payment info if exists
        successful_payment = None
        for payment in booking.payments:
            if payment.status == "SUCCESS":
                successful_payment = payment
                break
        
        tickets_simplified = []
        for t in booking.tickets:
            tickets_simplified.append(TicketInfoSimplified(
                flight_seat=f"{t.seat_class[:2].upper()} - {t.seat_number or 'TBA'}",
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
                seat_number=t.seat_number or "",
                seat_class=t.seat_class,
                payment_required=t.payment_required,
                currency=t.currency,
                ticket_number=t.ticket_number,
                issued_at=t.issued_at,
            ))
        
        results.append(BookingResponse(
            pnr=booking.pnr,
            booking_reference=booking.booking_reference,
            status=booking.status,
            created_at=booking.created_at,
            total_fare=total_fare,
            tickets=tickets_simplified,
            transaction_id=successful_payment.transaction_id if successful_payment else None,
            paid_amount=successful_payment.amount if successful_payment else None,
        ))
    
    return {
        "user_id": user_id,
        "user_name": u.full_name,
        "total_bookings": len(results),
        "bookings": results
    }
