from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from app.config import get_db
from typing import List
from app.schemas.airline_schema import AirlineCreate, AirlineUpdate, AirlineResponse
from app.models.airline import Airline

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=AirlineResponse)
def create_airline(payload: AirlineCreate, db: Session = Depends(get_db)):
    existing = db.query(Airline).filter(Airline.code == payload.code.upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail="airline code already exists")
    al = Airline(name=payload.name, code=payload.code.upper())
    db.add(al)
    db.commit()
    db.refresh(al)
    return al


@router.get("/", response_model=List[AirlineResponse])
def list_airlines(db: Session = Depends(get_db)):
    return db.query(Airline).all()


@router.get("/{airline_id}", response_model=AirlineResponse)
def get_airline(airline_id: int, db: Session = Depends(get_db)):
    al = db.query(Airline).filter(Airline.id == airline_id).first()
    if not al:
        raise HTTPException(status_code=404, detail="airline not found")
    return al


@router.put("/{airline_id}", response_model=AirlineResponse)
def update_airline(airline_id: int, payload: AirlineCreate, db: Session = Depends(get_db)):
    al = db.query(Airline).filter(Airline.id == airline_id).first()
    if not al:
        raise HTTPException(status_code=404, detail="airline not found")
    al.name = payload.name
    al.code = payload.code.upper()
    db.commit()
    db.refresh(al)
    return al


@router.patch("/{airline_id}", response_model=AirlineResponse)
def patch_airline(airline_id: int, payload: AirlineUpdate = Body(...), db: Session = Depends(get_db)):
    al = db.query(Airline).filter(Airline.id == airline_id).first()
    if not al:
        raise HTTPException(status_code=404, detail="airline not found")
    data = payload.dict(exclude_unset=True)
    if "name" in data:
        al.name = data["name"]
    if "code" in data and data.get("code"):
        al.code = data["code"].upper()
    db.commit()
    db.refresh(al)
    return al


@router.delete("/{airline_id}")
def delete_airline(airline_id: int, db: Session = Depends(get_db)):
    al = db.query(Airline).filter(Airline.id == airline_id).first()
    if not al:
        raise HTTPException(status_code=404, detail="airline not found")
    db.delete(al)
    db.commit()
    return {"message": "airline deleted"}


@router.get("/{airline_code}/schedules/external")
def get_external_airline_schedules(
    airline_code: str,
    origin: str | None = None,
    destination: str | None = None,
    db: Session = Depends(get_db)
):
    """
    Simulates external airline schedule API feed.
    Returns flight schedule data for a specific airline in a format that mimics
    external airline APIs (e.g., simplified JSON with selected fields).
    """
    from app.models.flight import Flight
    from app.models.airport import Airport
    from datetime import datetime, timezone
    
    airline = db.query(Airline).filter(Airline.code == airline_code.upper()).first()
    if not airline:
        raise HTTPException(status_code=404, detail=f"airline '{airline_code}' not found")
    
    # Query flights for this airline
    query = db.query(Flight).filter(Flight.airline_id == airline.id)
    
    # Filter by future flights only
    query = query.filter(Flight.departure_time > datetime.now(timezone.utc))
    
    # Apply optional filters
    if origin:
        origin_airport = db.query(Airport).filter(Airport.code == origin.upper()).first()
        if origin_airport:
            query = query.filter(Flight.departure_airport_id == origin_airport.id)
    
    if destination:
        dest_airport = db.query(Airport).filter(Airport.code == destination.upper()).first()
        if dest_airport:
            query = query.filter(Flight.arrival_airport_id == dest_airport.id)
    
    flights = query.limit(100).all()
    
    # Simulate external API response format (simplified)
    results = []
    for flight in flights:
        dep_airport = db.query(Airport).filter(Airport.id == flight.departure_airport_id).first()
        arr_airport = db.query(Airport).filter(Airport.id == flight.arrival_airport_id).first()
        
        results.append({
            "flight_number": flight.flight_number,
            "airline": airline.name,
            "airline_code": airline.code,
            "origin": dep_airport.code if dep_airport else None,
            "origin_city": dep_airport.city if dep_airport else None,
            "destination": arr_airport.code if arr_airport else None,
            "destination_city": arr_airport.city if arr_airport else None,
            "departure_time": flight.departure_time.isoformat(),
            "arrival_time": flight.arrival_time.isoformat(),
            "status": flight.status,
            "base_fare": float(flight.base_price),
        })
    
    return {
        "airline": airline.name,
        "airline_code": airline.code,
        "schedules": results,
        "total": len(results),
        "source": "external_api_simulation"
    }
