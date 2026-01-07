"""
Airport Authority Routes - For airport personnel to manage flights at their airport.

Features:
- View FIDS (Flight Information Display System) - arrivals and departures
- Assign/update gates for flights
- Monitor flight traffic at their airport
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from pydantic import BaseModel

from app.config import get_db
from app.models.flight import Flight
from app.models.airline import Airline
from app.models.airport import Airport
from app.models.seat import Seat
from app.models.user import User
from app.auth.dependencies import get_current_user

router = APIRouter()


# ============== Schemas ==============

class GateAssignment(BaseModel):
    departure_gate: Optional[str] = None
    arrival_gate: Optional[str] = None
    remarks: Optional[str] = None


class FIDSFlightInfo(BaseModel):
    id: int
    flight_number: str
    airline_name: str
    airline_code: str
    origin_city: str
    origin_code: str
    destination_city: str
    destination_code: str
    scheduled_time: datetime
    estimated_time: Optional[datetime]
    status: str
    gate: Optional[str]
    terminal: Optional[str]
    remarks: Optional[str]
    delay_minutes: int
    flight_type: str  # "Departure" or "Arrival"


class AirportDashboardStats(BaseModel):
    airport_name: str
    airport_code: str
    city: str
    total_departures_today: int
    total_arrivals_today: int
    on_time_departures: int
    delayed_departures: int
    on_time_arrivals: int
    delayed_arrivals: int
    cancelled_flights: int
    gates_in_use: int


# ============== Helper Functions ==============

def require_airport_authority(current_user: User = Depends(get_current_user)) -> User:
    """Ensure user is airport authority staff."""
    if current_user.role not in ("airport_authority", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Airport authority privileges required."
        )
    if current_user.role == "airport_authority" and not current_user.airport_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff account not linked to any airport."
        )
    return current_user


# ============== Routes ==============

@router.get("/dashboard", response_model=AirportDashboardStats)
def get_airport_dashboard(
    current_user: User = Depends(require_airport_authority),
    db: Session = Depends(get_db)
):
    """Get airport dashboard statistics."""
    airport = db.query(Airport).filter(Airport.id == current_user.airport_id).first()
    if not airport:
        raise HTTPException(status_code=404, detail="Airport not found")
    
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    # Departures today
    departures = db.query(Flight).filter(
        Flight.departure_airport_id == airport.id,
        Flight.departure_time >= today_start,
        Flight.departure_time < today_end
    ).all()
    
    # Arrivals today
    arrivals = db.query(Flight).filter(
        Flight.arrival_airport_id == airport.id,
        Flight.arrival_time >= today_start,
        Flight.arrival_time < today_end
    ).all()
    
    # Count statuses
    on_time_deps = sum(1 for f in departures if (f.delay_minutes or 0) < 15 and f.status != "Cancelled")
    delayed_deps = sum(1 for f in departures if (f.delay_minutes or 0) >= 15 and f.status != "Cancelled")
    on_time_arrs = sum(1 for f in arrivals if (f.delay_minutes or 0) < 15 and f.status != "Cancelled")
    delayed_arrs = sum(1 for f in arrivals if (f.delay_minutes or 0) >= 15 and f.status != "Cancelled")
    cancelled = sum(1 for f in departures + arrivals if f.status == "Cancelled") // 2  # Avoid double count
    
    # Gates in use (unique departure gates for active flights)
    active_statuses = ["Boarding", "Scheduled"]
    gates = set()
    for f in departures:
        if f.departure_gate and f.status in active_statuses:
            gates.add(f.departure_gate)
    
    return AirportDashboardStats(
        airport_name=airport.name,
        airport_code=airport.code,
        city=airport.city,
        total_departures_today=len(departures),
        total_arrivals_today=len(arrivals),
        on_time_departures=on_time_deps,
        delayed_departures=delayed_deps,
        on_time_arrivals=on_time_arrs,
        delayed_arrivals=delayed_arrs,
        cancelled_flights=cancelled,
        gates_in_use=len(gates),
    )


@router.get("/fids/departures", response_model=List[FIDSFlightInfo])
def get_departures_fids(
    hours_ahead: int = 12,
    current_user: User = Depends(require_airport_authority),
    db: Session = Depends(get_db)
):
    """Get FIDS departures board for the airport."""
    airport = db.query(Airport).filter(Airport.id == current_user.airport_id).first()
    if not airport:
        raise HTTPException(status_code=404, detail="Airport not found")
    
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    end_time = now + timedelta(hours=hours_ahead)
    
    flights = db.query(Flight).filter(
        Flight.departure_airport_id == airport.id,
        Flight.departure_time >= now - timedelta(hours=2),  # Include recent departed
        Flight.departure_time <= end_time
    ).order_by(Flight.departure_time.asc()).limit(50).all()
    
    result = []
    for f in flights:
        airline = db.query(Airline).filter(Airline.id == f.airline_id).first()
        dest = db.query(Airport).filter(Airport.id == f.arrival_airport_id).first()
        
        # Calculate estimated time
        est_time = f.departure_time
        if f.delay_minutes:
            est_time = f.departure_time + timedelta(minutes=f.delay_minutes)
        
        result.append(FIDSFlightInfo(
            id=f.id,
            flight_number=f.flight_number,
            airline_name=airline.name if airline else "Unknown",
            airline_code=airline.code if airline else "XX",
            origin_city=airport.city,
            origin_code=airport.code,
            destination_city=dest.city if dest else "Unknown",
            destination_code=dest.code if dest else "XXX",
            scheduled_time=f.departure_time,
            estimated_time=est_time if f.delay_minutes else None,
            status=f.status or "Scheduled",
            gate=f.departure_gate,
            terminal=None,  # Can add terminal field to airport model if needed
            remarks=f.remarks,
            delay_minutes=f.delay_minutes or 0,
            flight_type="Departure",
        ))
    
    return result


@router.get("/fids/arrivals", response_model=List[FIDSFlightInfo])
def get_arrivals_fids(
    hours_ahead: int = 12,
    current_user: User = Depends(require_airport_authority),
    db: Session = Depends(get_db)
):
    """Get FIDS arrivals board for the airport."""
    airport = db.query(Airport).filter(Airport.id == current_user.airport_id).first()
    if not airport:
        raise HTTPException(status_code=404, detail="Airport not found")
    
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    end_time = now + timedelta(hours=hours_ahead)
    
    flights = db.query(Flight).filter(
        Flight.arrival_airport_id == airport.id,
        Flight.arrival_time >= now - timedelta(hours=2),  # Include recent landed
        Flight.arrival_time <= end_time
    ).order_by(Flight.arrival_time.asc()).limit(50).all()
    
    result = []
    for f in flights:
        airline = db.query(Airline).filter(Airline.id == f.airline_id).first()
        origin = db.query(Airport).filter(Airport.id == f.departure_airport_id).first()
        
        # Calculate estimated time
        est_time = f.arrival_time
        if f.delay_minutes:
            est_time = f.arrival_time + timedelta(minutes=f.delay_minutes)
        
        result.append(FIDSFlightInfo(
            id=f.id,
            flight_number=f.flight_number,
            airline_name=airline.name if airline else "Unknown",
            airline_code=airline.code if airline else "XX",
            origin_city=origin.city if origin else "Unknown",
            origin_code=origin.code if origin else "XXX",
            destination_city=airport.city,
            destination_code=airport.code,
            scheduled_time=f.arrival_time,
            estimated_time=est_time if f.delay_minutes else None,
            status=f.status or "Scheduled",
            gate=f.arrival_gate,
            terminal=None,
            remarks=f.remarks,
            delay_minutes=f.delay_minutes or 0,
            flight_type="Arrival",
        ))
    
    return result


@router.put("/flights/{flight_id}/gate")
def assign_gate(
    flight_id: int,
    assignment: GateAssignment,
    current_user: User = Depends(require_airport_authority),
    db: Session = Depends(get_db)
):
    """Assign or update gate for a flight at this airport."""
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    
    # Check if flight is associated with this airport
    is_departure = flight.departure_airport_id == current_user.airport_id
    is_arrival = flight.arrival_airport_id == current_user.airport_id
    
    if current_user.role == "airport_authority" and not (is_departure or is_arrival):
        raise HTTPException(
            status_code=403,
            detail="This flight does not operate from your airport"
        )
    
    # Update appropriate gate
    updated = False
    if is_departure and assignment.departure_gate is not None:
        flight.departure_gate = assignment.departure_gate
        updated = True
    
    if is_arrival and assignment.arrival_gate is not None:
        flight.arrival_gate = assignment.arrival_gate
        updated = True
    
    if assignment.remarks:
        flight.remarks = assignment.remarks
        updated = True
    
    if not updated:
        raise HTTPException(
            status_code=400,
            detail="No valid gate assignment provided for this airport"
        )
    
    db.commit()
    
    return {
        "message": f"Gate assignment updated for flight {flight.flight_number}",
        "flight_id": flight.id,
        "departure_gate": flight.departure_gate,
        "arrival_gate": flight.arrival_gate,
    }


@router.get("/flights/all", response_model=List[FIDSFlightInfo])
def get_all_airport_flights(
    date: Optional[str] = None,  # YYYY-MM-DD
    current_user: User = Depends(require_airport_authority),
    db: Session = Depends(get_db)
):
    """Get all flights (arrivals and departures) for the airport."""
    airport = db.query(Airport).filter(Airport.id == current_user.airport_id).first()
    if not airport:
        raise HTTPException(status_code=404, detail="Airport not found")
    
    if date:
        try:
            d = datetime.strptime(date, "%Y-%m-%d")
            start = d
            end = d + timedelta(days=1)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
    
    # Get departures
    departures = db.query(Flight).filter(
        Flight.departure_airport_id == airport.id,
        Flight.departure_time >= start,
        Flight.departure_time < end
    ).all()
    
    # Get arrivals
    arrivals = db.query(Flight).filter(
        Flight.arrival_airport_id == airport.id,
        Flight.arrival_time >= start,
        Flight.arrival_time < end
    ).all()
    
    result = []
    
    # Process departures
    for f in departures:
        airline = db.query(Airline).filter(Airline.id == f.airline_id).first()
        dest = db.query(Airport).filter(Airport.id == f.arrival_airport_id).first()
        
        est_time = f.departure_time
        if f.delay_minutes:
            est_time = f.departure_time + timedelta(minutes=f.delay_minutes)
        
        result.append(FIDSFlightInfo(
            id=f.id,
            flight_number=f.flight_number,
            airline_name=airline.name if airline else "Unknown",
            airline_code=airline.code if airline else "XX",
            origin_city=airport.city,
            origin_code=airport.code,
            destination_city=dest.city if dest else "Unknown",
            destination_code=dest.code if dest else "XXX",
            scheduled_time=f.departure_time,
            estimated_time=est_time if f.delay_minutes else None,
            status=f.status or "Scheduled",
            gate=f.departure_gate,
            terminal=None,
            remarks=f.remarks,
            delay_minutes=f.delay_minutes or 0,
            flight_type="Departure",
        ))
    
    # Process arrivals
    for f in arrivals:
        airline = db.query(Airline).filter(Airline.id == f.airline_id).first()
        origin = db.query(Airport).filter(Airport.id == f.departure_airport_id).first()
        
        est_time = f.arrival_time
        if f.delay_minutes:
            est_time = f.arrival_time + timedelta(minutes=f.delay_minutes)
        
        result.append(FIDSFlightInfo(
            id=f.id,
            flight_number=f.flight_number,
            airline_name=airline.name if airline else "Unknown",
            airline_code=airline.code if airline else "XX",
            origin_city=origin.city if origin else "Unknown",
            origin_code=origin.code if origin else "XXX",
            destination_city=airport.city,
            destination_code=airport.code,
            scheduled_time=f.arrival_time,
            estimated_time=est_time if f.delay_minutes else None,
            status=f.status or "Scheduled",
            gate=f.arrival_gate,
            terminal=None,
            remarks=f.remarks,
            delay_minutes=f.delay_minutes or 0,
            flight_type="Arrival",
        ))
    
    # Sort by scheduled time
    result.sort(key=lambda x: x.scheduled_time)
    
    return result
