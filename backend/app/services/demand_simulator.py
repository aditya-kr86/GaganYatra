import random
from datetime import datetime, timezone, timedelta
from typing import List, Dict

from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.models.flight import Flight
from app.models.seat import Seat


def run_demand_simulation_once(db: Session, within_hours: int = 168) -> int:
    """Run one iteration of demand simulation for upcoming flights within `within_hours`.

    OPTIMIZED: Uses batched updates instead of per-flight commits.
    Returns number of flights updated.
    """
    now = datetime.now(timezone.utc)
    # Make naive to match database datetime (which is naive)
    if now.tzinfo is not None:
        now = now.replace(tzinfo=None)
    
    cutoff = now + timedelta(hours=within_hours)
    
    # Get flights
    flights: List[Flight] = db.query(Flight).filter(
        Flight.departure_time >= now, 
        Flight.departure_time <= cutoff
    ).all()
    
    if not flights:
        return 0
    
    flight_ids = [f.id for f in flights]
    
    # Get total seats per flight
    total_query = db.query(
        Seat.flight_id,
        func.count(Seat.id).label('total')
    ).filter(Seat.flight_id.in_(flight_ids)).group_by(Seat.flight_id).all()
    
    total_seats_map: Dict[int, int] = {r.flight_id: r.total for r in total_query}
    
    # Get available seats per flight
    avail_query = db.query(
        Seat.flight_id,
        func.count(Seat.id).label('available')
    ).filter(
        Seat.flight_id.in_(flight_ids),
        Seat.is_available == True
    ).group_by(Seat.flight_id).all()
    
    avail_seats_map: Dict[int, int] = {r.flight_id: r.available for r in avail_query}
    
    # Base rate according to demand_level
    base_rate_map = {
        "low": 1,
        "medium": 3,
        "high": 6,
        "extreme": 10,
    }
    
    all_seat_ids_to_book = []
    
    for flight in flights:
        total_seats = total_seats_map.get(flight.id, 0)
        available = avail_seats_map.get(flight.id, 0)
        
        if total_seats == 0 or available == 0:
            continue
        
        hours = (flight.departure_time - now).total_seconds() / 3600
        base_rate = base_rate_map.get((flight.demand_level or "medium").lower(), 3)
        
        # Increase booking rate as departure approaches
        if hours < 48:
            base_rate *= 2
        elif hours < 168:
            base_rate *= 1.5
        
        new_bookings = max(0, int(random.gauss(mu=base_rate, sigma=max(1, base_rate * 0.3))))
        to_book = min(new_bookings, available)
        
        if to_book > 0:
            # Get seat IDs to book
            seat_ids = [s.id for s in db.query(Seat.id).filter(
                Seat.flight_id == flight.id,
                Seat.is_available == True
            ).limit(to_book).all()]
            all_seat_ids_to_book.extend(seat_ids)
        
        # Check if demand level should escalate
        remaining_pct = (available - to_book) / total_seats if total_seats > 0 else 0
        if remaining_pct < 0.2 and (flight.demand_level or "").lower() not in ("high", "extreme"):
            flight.demand_level = "high"
    
    # Batch update all seats in one query
    if all_seat_ids_to_book:
        db.query(Seat).filter(Seat.id.in_(all_seat_ids_to_book)).update(
            {"is_available": False}, synchronize_session=False
        )
    
    # Single commit for all changes
    db.commit()
    
    return len(flights)
