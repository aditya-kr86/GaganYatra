from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.config import get_db
from app.models.seat import Seat, SEAT_POSITION_SURCHARGE
from app.models.flight import Flight
from app.models.airline import Airline
from app.models.aircraft import Aircraft
from app.schemas.seat_schema import (
    SeatResponse, SeatAvailabilityResponse, SeatAvailabilityItem,
    SeatMapResponse, SeatMapRow, SeatMapSeat, SeatMapConfig
)
from app.services.pricing_engine import compute_dynamic_price
from typing import Optional

router = APIRouter()


@router.get("/", response_model=list[SeatResponse])
def list_seats(db: Session = Depends(get_db)):
    return db.query(Seat).all()


@router.get("/map/{flight_id}", response_model=SeatMapResponse)
def get_seat_map(
    flight_id: int, 
    seat_class: Optional[str] = Query(None, description="Filter by seat class (Economy, Business, etc.)"),
    db: Session = Depends(get_db)
):
    """
    Get a visual seat map for a flight with availability and surcharge information.
    Used by the frontend to render the seat selector diagram.
    """
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    
    # Get aircraft info
    aircraft = db.query(Aircraft).filter(Aircraft.id == flight.aircraft_id).first()
    aircraft_model = aircraft.model if aircraft else None
    
    # Query seats for this flight
    query = db.query(Seat).filter(Seat.flight_id == flight_id)
    
    # Map API tier names to database seat class names
    tier_to_db_class = {
        "ECONOMY": "Economy",
        "ECONOMY_FLEX": "Premium Economy", 
        "BUSINESS": "Business",
        "FIRST": "First"
    }
    
    if seat_class:
        db_class = tier_to_db_class.get(seat_class.upper(), seat_class)
        query = query.filter(Seat.seat_class == db_class)
    
    seats = query.order_by(Seat.row_number.asc(), Seat.seat_letter.asc()).all()
    
    if not seats:
        raise HTTPException(status_code=404, detail="No seats found for this flight")
    
    # Compute current dynamic price for the flight
    total_seats = db.query(func.count(Seat.id)).filter(Seat.flight_id == flight_id).scalar() or 0
    booked_seats = db.query(func.count(Seat.id)).filter(Seat.flight_id == flight_id, Seat.is_available == False).scalar() or 0
    demand_level = getattr(flight, 'demand_level', 'medium') or 'medium'
    
    # Get seat class for pricing (use the filter or default to Economy)
    pricing_tier = seat_class.upper() if seat_class else "ECONOMY"
    if pricing_tier not in tier_to_db_class:
        pricing_tier = "ECONOMY"
    
    base_price = compute_dynamic_price(
        base_fare=flight.base_price,
        departure_time=flight.departure_time,
        total_seats=total_seats,
        booked_seats=booked_seats,
        demand_level=demand_level,
        tier=pricing_tier,
    )
    
    # Determine seat configuration based on aircraft or seats
    # Try to infer from existing seat letters
    seat_letters_set = set()
    for s in seats:
        if s.seat_letter:
            seat_letters_set.add(s.seat_letter)
    
    # Default configuration for typical aircraft
    if len(seat_letters_set) == 6:
        # 3-3 configuration (typical narrow-body: A320, B737)
        seat_letters = ["A", "B", "C", "D", "E", "F"]
        aisle_after = [3]  # Aisle after seat C
    elif len(seat_letters_set) == 4:
        # 2-2 configuration (regional jets)
        seat_letters = ["A", "B", "C", "D"]
        aisle_after = [2]
    elif len(seat_letters_set) == 9:
        # 3-3-3 configuration (typical wide-body)
        seat_letters = ["A", "B", "C", "D", "E", "F", "G", "H", "J"]
        aisle_after = [3, 6]
    else:
        # Fallback: use detected letters sorted
        seat_letters = sorted(list(seat_letters_set)) if seat_letters_set else ["A", "B", "C", "D", "E", "F"]
        aisle_after = [len(seat_letters) // 2]
    
    config = SeatMapConfig(
        seats_per_row=len(seat_letters),
        aisle_after=aisle_after,
        seat_letters=seat_letters
    )
    
    # Group seats by row with dynamically calculated surcharges
    rows_dict = {}
    for seat in seats:
        row_num = seat.row_number or int(''.join(filter(str.isdigit, seat.seat_number)) or '1')
        seat_let = seat.seat_letter or ''.join(filter(str.isalpha, seat.seat_number)) or 'A'
        
        if row_num not in rows_dict:
            rows_dict[row_num] = []
        
        # Calculate surcharge dynamically based on seat position and current base_price
        position = seat.seat_position or "middle"
        surcharge_rate = SEAT_POSITION_SURCHARGE.get(position, 0.0)
        calculated_surcharge = round(base_price * surcharge_rate, 2)
        
        rows_dict[row_num].append(SeatMapSeat(
            id=seat.id,
            seat_number=seat.seat_number,
            row_number=row_num,
            seat_letter=seat_let,
            seat_class=seat.seat_class or "Economy",
            seat_position=seat.seat_position or "middle",
            is_available=seat.is_available,
            surcharge=calculated_surcharge
        ))
    
    # Convert to sorted list of rows
    rows = []
    for row_num in sorted(rows_dict.keys()):
        # Sort seats within row by letter
        sorted_seats = sorted(rows_dict[row_num], key=lambda s: s.seat_letter)
        rows.append(SeatMapRow(row_number=row_num, seats=sorted_seats))
    
    return SeatMapResponse(
        flight_id=flight_id,
        flight_number=flight.flight_number,
        aircraft_model=aircraft_model,
        seat_class_filter=seat_class,
        config=config,
        rows=rows,
        surcharge_info=SEAT_POSITION_SURCHARGE,
        base_price=base_price
    )


@router.get("/{airline_code}/{flight_number}", response_model=SeatAvailabilityResponse)
def seats_by_airline_and_flight(airline_code: str, flight_number: str, db: Session = Depends(get_db)):
    fl = db.query(Flight).join(Airline).filter(Flight.flight_number == flight_number, func.lower(Airline.code) == airline_code.strip().lower()).first()
    if not fl:
        raise HTTPException(status_code=404, detail="flight not found for airline")

    classes = db.query(Seat.seat_class).filter(Seat.flight_id == fl.id).distinct().all()
    class_list = [c[0] for c in classes if c[0]]
    items = []
    for cls in class_list:
        # Use direct string comparison since seat_class is an ENUM
        available_q = db.query(Seat).filter(Seat.flight_id == fl.id, Seat.seat_class == cls, Seat.is_available == True).order_by(Seat.id.asc())
        booked_q = db.query(Seat).filter(Seat.flight_id == fl.id, Seat.seat_class == cls, Seat.is_available == False).order_by(Seat.id.asc())
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
