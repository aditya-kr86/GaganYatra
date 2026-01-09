"""User management routes with role-based access control."""
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.config import get_db
from app.models.user import User
from app.schemas.user_schema import (
    UserCreate,
    UserUpdate,
    UserAdminUpdate,
    UserResponse,
    UserProfileResponse,
)
from app.auth.password import hash_password
from app.auth.dependencies import get_current_user, require_admin


def _format_flight_seat(seat_class: str, seat_number: str) -> str:
    """Format flight seat as 'SEAT_CLASS - SEAT_NUMBER' (e.g., 'EC - 32')."""
    seat_class_abbr = {
        "ECONOMY": "EC",
        "ECONOMY_FLEX": "ECF",
        "BUSINESS": "BUS",
        "FIRST": "FC",
        "Economy": "EC",
        "Premium Economy": "ECF",
        "Business": "BUS",
        "First": "FC",
    }.get(seat_class, seat_class[:2].upper() if seat_class else "EC")
    
    return f"{seat_class_abbr} - {seat_number}"


router = APIRouter()


# ============== User Profile Endpoints (Authenticated Users) ==============

@router.get("/profile", response_model=UserProfileResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the current user's profile with booking count."""
    from app.models.booking import Booking
    
    # Count user's bookings
    booking_count = db.query(Booking).filter(Booking.user_id == current_user.id).count()
    
    return UserProfileResponse(
        id=current_user.id,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        full_name=current_user.full_name,
        email=current_user.email,
        mobile=current_user.mobile,
        country=current_user.country,
        role=current_user.role,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
        airline_id=current_user.airline_id,
        airport_id=current_user.airport_id,
        total_bookings=booking_count,
    )


@router.put("/profile", response_model=UserResponse)
def update_my_profile(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update the current user's profile."""
    data = payload.model_dump(exclude_unset=True)
    
    # Check if email is being changed and if it's already taken
    if "email" in data and data["email"] != current_user.email:
        existing = db.query(User).filter(User.email == data["email"].lower()).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        data["email"] = data["email"].lower()
    
    for key, value in data.items():
        setattr(current_user, key, value)
    
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/my-bookings")
def get_my_bookings(
    status: Optional[str] = Query(None, description="Filter by booking status"),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the current user's booking history."""
    from app.models.booking import Booking
    from app.schemas.booking_schema import BookingResponse, TicketInfoSimplified
    
    query = db.query(Booking).filter(Booking.user_id == current_user.id)
    
    if status:
        query = query.filter(Booking.status == status)
    
    query = query.order_by(Booking.created_at.desc())
    bookings = query.limit(limit).all()
    
    results = []
    for booking in bookings:
        total_fare = sum(t.payment_required for t in booking.tickets) if booking.tickets else 0.0
        
        tickets_simplified = []
        for t in booking.tickets:
            tickets_simplified.append(TicketInfoSimplified(
                flight_seat=_format_flight_seat(t.seat_class or "Economy", t.seat_number or "TBA"),
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
                seat_class=t.seat_class or "Economy",
                payment_required=t.payment_required,
                currency=t.currency,
                ticket_number=t.ticket_number,
                issued_at=t.issued_at,
            ))
        
        # Get payment info
        successful_payment = None
        for payment in booking.payments:
            if payment.status == "Success":
                successful_payment = payment
                break
        
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
        "user_id": current_user.id,
        "user_name": current_user.full_name,
        "total_bookings": len(results),
        "bookings": results
    }


# ============== Admin Endpoints ==============

@router.get("/", response_model=List[UserResponse])
def list_users(
    role: Optional[str] = Query(None, description="Filter by user role"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    limit: int = Query(100, ge=1, le=500),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List all users (Admin only)."""
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.first_name.ilike(search_term)) |
            (User.last_name.ilike(search_term)) |
            (User.email.ilike(search_term))
        )
    
    users = query.order_by(User.created_at.desc()).limit(limit).all()
    return users


@router.post("/", response_model=UserResponse, status_code=201)
def create_user(
    payload: UserCreate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a new user with specified role (Admin only)."""
    # Check if email already exists
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate role
    valid_roles = ["customer", "airline_staff", "airport_authority", "admin"]
    if payload.role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {valid_roles}")
    
    # Validate airline_id for airline_staff
    if payload.role == "airline_staff" and not payload.airline_id:
        raise HTTPException(status_code=400, detail="airline_id is required for airline_staff role")
    
    # Validate airport_id for airport_authority
    if payload.role == "airport_authority" and not payload.airport_id:
        raise HTTPException(status_code=400, detail="airport_id is required for airport_authority role")
    
    user = User(
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email.lower(),
        mobile=payload.mobile,
        country=payload.country,
        password_hash=hash_password(payload.password),
        role=payload.role,
        airline_id=payload.airline_id,
        airport_id=payload.airport_id,
        is_active=True,
        is_verified=True,  # Admin-created users are verified by default
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get a specific user by ID (Admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    payload: UserAdminUpdate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update a user (Admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    data = payload.model_dump(exclude_unset=True)
    
    # Check if email is being changed
    if "email" in data and data["email"] != user.email:
        existing = db.query(User).filter(User.email == data["email"].lower()).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        data["email"] = data["email"].lower()
    
    for key, value in data.items():
        setattr(user, key, value)
    
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserResponse)
def patch_user(
    user_id: int,
    payload: UserAdminUpdate = Body(...),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Partially update a user (Admin only)."""
    return update_user(user_id, payload, admin_user, db)


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete a user (Admin only)."""
    if user_id == admin_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}


@router.post("/{user_id}/deactivate")
def deactivate_user(
    user_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Deactivate a user account (Admin only)."""
    if user_id == admin_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = False
    db.commit()
    return {"message": f"User {user.email} has been deactivated"}


@router.post("/{user_id}/activate")
def activate_user(
    user_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Activate a user account (Admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = True
    db.commit()
    return {"message": f"User {user.email} has been activated"}


@router.get("/{user_id}/bookings")
def get_user_bookings(
    user_id: int,
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get booking history for a specific user (Admin only)."""
    from app.models.booking import Booking
    from app.schemas.booking_schema import BookingResponse, TicketInfoSimplified
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    query = db.query(Booking).filter(Booking.user_id == user_id)
    
    if status:
        query = query.filter(Booking.status == status)
    
    query = query.order_by(Booking.created_at.desc())
    bookings = query.limit(limit).all()
    
    results = []
    for booking in bookings:
        total_fare = sum(t.payment_required for t in booking.tickets) if booking.tickets else 0.0
        
        tickets_simplified = []
        for t in booking.tickets:
            tickets_simplified.append(TicketInfoSimplified(
                flight_seat=f"{t.seat_class[:2].upper() if t.seat_class else 'EC'} - {t.seat_number or 'TBA'}",
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
                seat_class=t.seat_class or "ECONOMY",
                payment_required=t.payment_required,
                currency=t.currency,
                ticket_number=t.ticket_number,
                issued_at=t.issued_at,
            ))
        
        successful_payment = None
        for payment in booking.payments:
            if payment.status == "Success":
                successful_payment = payment
                break
        
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
        "user_name": user.full_name,
        "total_bookings": len(results),
        "bookings": results
    }
