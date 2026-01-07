"""
Airline Staff Routes - For airline personnel to manage their flights.

Features:
- View all flights for their airline
- Update flight status (Scheduled, Boarding, Delayed, Departed, Landed, Cancelled)
- View passenger manifests
- Add delay information
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from pydantic import BaseModel

from app.config import get_db
from app.models.flight import Flight
from app.models.ticket import Ticket
from app.models.booking import Booking
from app.models.seat import Seat
from app.models.airline import Airline
from app.models.airport import Airport
from app.models.user import User
from app.auth.dependencies import get_current_user

router = APIRouter()


# ============== Schemas ==============

class FlightStatusUpdate(BaseModel):
    status: str  # Scheduled, Boarding, Delayed, Departed, Landed, Cancelled
    delay_minutes: Optional[int] = 0
    delay_reason: Optional[str] = None
    remarks: Optional[str] = None


class PassengerInfo(BaseModel):
    ticket_id: int
    passenger_name: str
    passenger_age: Optional[int]
    passenger_gender: Optional[str]
    seat_number: Optional[str]
    seat_class: str
    booking_pnr: Optional[str]
    booking_status: str


class FlightManifest(BaseModel):
    flight_id: int
    flight_number: str
    route: str
    departure_time: datetime
    arrival_time: datetime
    status: str
    total_seats: int
    booked_seats: int
    passengers: List[PassengerInfo]


class AirlineFlightInfo(BaseModel):
    id: int
    flight_number: str
    departure_airport: str
    departure_city: str
    arrival_airport: str
    arrival_city: str
    departure_time: datetime
    arrival_time: datetime
    status: str
    delay_minutes: int
    delay_reason: Optional[str]
    remarks: Optional[str]
    departure_gate: Optional[str]
    arrival_gate: Optional[str]
    total_seats: int
    booked_seats: int
    available_seats: int


class AirlineDashboardStats(BaseModel):
    airline_name: str
    airline_code: str
    total_flights_today: int
    total_flights_week: int
    scheduled: int
    boarding: int
    delayed: int
    departed: int
    landed: int
    cancelled: int
    total_passengers_today: int


# ============== Helper Functions ==============

def require_airline_staff(current_user: User = Depends(get_current_user)) -> User:
    """Ensure user is airline staff."""
    if current_user.role not in ("airline_staff", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Airline staff privileges required."
        )
    if current_user.role == "airline_staff" and not current_user.airline_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff account not linked to any airline."
        )
    return current_user


# ============== Routes ==============

@router.get("/dashboard", response_model=AirlineDashboardStats)
def get_airline_dashboard(
    current_user: User = Depends(require_airline_staff),
    db: Session = Depends(get_db)
):
    """Get airline dashboard statistics."""
    airline = db.query(Airline).filter(Airline.id == current_user.airline_id).first()
    if not airline:
        raise HTTPException(status_code=404, detail="Airline not found")
    
    # Use local time (flights are stored in local time)
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    week_end = today_start + timedelta(days=7)
    
    # Today's flights
    today_flights = db.query(Flight).filter(
        Flight.airline_id == airline.id,
        Flight.departure_time >= today_start,
        Flight.departure_time < today_end
    ).all()
    
    # This week's flights
    week_flights_count = db.query(func.count(Flight.id)).filter(
        Flight.airline_id == airline.id,
        Flight.departure_time >= today_start,
        Flight.departure_time < week_end
    ).scalar() or 0
    
    # Status counts for today
    status_counts = {
        "scheduled": 0, "boarding": 0, "delayed": 0,
        "departed": 0, "landed": 0, "cancelled": 0
    }
    for f in today_flights:
        status_key = (f.status or "Scheduled").lower()
        if status_key in status_counts:
            status_counts[status_key] += 1
    
    # Total passengers today
    today_flight_ids = [f.id for f in today_flights]
    passengers_today = 0
    if today_flight_ids:
        passengers_today = db.query(func.count(Ticket.id)).filter(
            Ticket.flight_id.in_(today_flight_ids)
        ).join(Booking).filter(Booking.status == "Confirmed").scalar() or 0
    
    return AirlineDashboardStats(
        airline_name=airline.name,
        airline_code=airline.code,
        total_flights_today=len(today_flights),
        total_flights_week=week_flights_count,
        scheduled=status_counts["scheduled"],
        boarding=status_counts["boarding"],
        delayed=status_counts["delayed"],
        departed=status_counts["departed"],
        landed=status_counts["landed"],
        cancelled=status_counts["cancelled"],
        total_passengers_today=passengers_today,
    )


@router.get("/flights", response_model=List[AirlineFlightInfo])
def get_airline_flights(
    date: Optional[str] = None,  # YYYY-MM-DD
    status_filter: Optional[str] = None,
    current_user: User = Depends(require_airline_staff),
    db: Session = Depends(get_db)
):
    """Get all flights for the airline, optionally filtered by date and status."""
    query = db.query(Flight).filter(Flight.airline_id == current_user.airline_id)
    
    if date:
        try:
            d = datetime.strptime(date, "%Y-%m-%d")
            query = query.filter(
                Flight.departure_time >= d,
                Flight.departure_time < d + timedelta(days=1)
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        # Default to today and next 7 days
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        query = query.filter(Flight.departure_time >= today_start)
    
    if status_filter:
        query = query.filter(Flight.status == status_filter)
    
    flights = query.order_by(Flight.departure_time.asc()).limit(100).all()
    
    result = []
    for flight in flights:
        dep_airport = db.query(Airport).filter(Airport.id == flight.departure_airport_id).first()
        arr_airport = db.query(Airport).filter(Airport.id == flight.arrival_airport_id).first()
        
        total = db.query(func.count(Seat.id)).filter(Seat.flight_id == flight.id).scalar() or 0
        available = db.query(func.count(Seat.id)).filter(
            Seat.flight_id == flight.id, Seat.is_available == True
        ).scalar() or 0
        
        result.append(AirlineFlightInfo(
            id=flight.id,
            flight_number=flight.flight_number,
            departure_airport=dep_airport.code if dep_airport else "N/A",
            departure_city=dep_airport.city if dep_airport else "N/A",
            arrival_airport=arr_airport.code if arr_airport else "N/A",
            arrival_city=arr_airport.city if arr_airport else "N/A",
            departure_time=flight.departure_time,
            arrival_time=flight.arrival_time,
            status=flight.status or "Scheduled",
            delay_minutes=flight.delay_minutes or 0,
            delay_reason=flight.delay_reason,
            remarks=flight.remarks,
            departure_gate=flight.departure_gate,
            arrival_gate=flight.arrival_gate,
            total_seats=total,
            booked_seats=total - available,
            available_seats=available,
        ))
    
    return result


@router.put("/flights/{flight_id}/status")
def update_flight_status(
    flight_id: int,
    update: FlightStatusUpdate,
    current_user: User = Depends(require_airline_staff),
    db: Session = Depends(get_db)
):
    """Update flight status (airline staff only for their airline)."""
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    
    # Verify airline ownership (admin can update any)
    if current_user.role == "airline_staff" and flight.airline_id != current_user.airline_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this flight")
    
    valid_statuses = ["Scheduled", "Boarding", "Delayed", "Departed", "Landed", "Cancelled"]
    if update.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    flight.status = update.status
    if update.delay_minutes is not None:
        flight.delay_minutes = update.delay_minutes
    if update.delay_reason:
        flight.delay_reason = update.delay_reason
    if update.remarks:
        flight.remarks = update.remarks
    
    db.commit()
    
    return {
        "message": f"Flight {flight.flight_number} status updated to {update.status}",
        "flight_id": flight.id,
        "new_status": flight.status,
    }


@router.get("/flights/{flight_id}/manifest", response_model=FlightManifest)
def get_passenger_manifest(
    flight_id: int,
    current_user: User = Depends(require_airline_staff),
    db: Session = Depends(get_db)
):
    """Get passenger manifest for a flight."""
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    
    # Verify airline ownership
    if current_user.role == "airline_staff" and flight.airline_id != current_user.airline_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this manifest")
    
    dep = db.query(Airport).filter(Airport.id == flight.departure_airport_id).first()
    arr = db.query(Airport).filter(Airport.id == flight.arrival_airport_id).first()
    
    # Get confirmed tickets
    tickets = db.query(Ticket).filter(Ticket.flight_id == flight_id).join(Booking).filter(
        Booking.status == "Confirmed"
    ).all()
    
    passengers = []
    for ticket in tickets:
        booking = ticket.booking
        passengers.append(PassengerInfo(
            ticket_id=ticket.id,
            passenger_name=ticket.passenger_name,
            passenger_age=ticket.passenger_age,
            passenger_gender=ticket.passenger_gender,
            seat_number=ticket.seat_number,
            seat_class=ticket.seat_class,
            booking_pnr=booking.pnr if booking else None,
            booking_status=booking.status if booking else "Unknown",
        ))
    
    total = db.query(func.count(Seat.id)).filter(Seat.flight_id == flight.id).scalar() or 0
    
    return FlightManifest(
        flight_id=flight.id,
        flight_number=flight.flight_number,
        route=f"{dep.code if dep else 'N/A'} → {arr.code if arr else 'N/A'}",
        departure_time=flight.departure_time,
        arrival_time=flight.arrival_time,
        status=flight.status or "Scheduled",
        total_seats=total,
        booked_seats=len(passengers),
        passengers=passengers,
    )
