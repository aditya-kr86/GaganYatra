from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy import func
from app.models.airport import Airport
from app.models.airline import Airline
from app.models.seat import Seat
from app.models.aircraft import Aircraft
from app.config import get_db
from app.schemas.flight_schema import FlightResponse
from app.services.flight_service import search_flights
from app.services.flight_service import create_flight
from app.schemas.flight_schema import FlightCreate, FlightResponse
from fastapi import Body, Path
from app.models.flight import Flight
from app.config import get_db
from sqlalchemy.orm import Session
from app.services.flight_service import get_booking_by_pnr
from app.services.flight_service import cancel_booking
from app.schemas.flight_schema import FlightUpdate
from app.models.airline import Airline
from app.models.airport import Airport

router = APIRouter()


@router.get("/", response_model=list[FlightResponse])
def list_flights_api(
    limit: int | None = Query(None, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Return all flights (optionally limited)."""
    flights = search_flights(db, limit=limit)
    return flights


@router.get("/search", response_model=list[FlightResponse])
def search_flights_api(
    origin: str | None = Query(None, min_length=3, max_length=10),
    destination: str | None = Query(None, min_length=3, max_length=10),
    date: str | None = Query(None, regex=r"^\d{4}-\d{2}-\d{2}$"),
    sort_by: str | None = Query(None, regex="^(price|duration)$"),
    limit: int | None = Query(50, ge=1, le=200),
    days_flex: int | None = Query(0, ge=0, le=30),
    db: Session = Depends(get_db)
):
    # Normalize codes
    if origin:
        origin = origin.upper()
    if destination:
        destination = destination.upper()

    # Validate date format if provided
    if date:
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD")

    flights = search_flights(db, origin=origin, destination=destination, date=date, sort_by=sort_by, limit=limit, days_flex=days_flex or 0)

    # Return empty list when no flights found (consistent with list endpoint)
    return flights or []



@router.post("/admin", response_model=FlightResponse, status_code=201)
def create_flight_api(payload: FlightCreate, db: Session = Depends(get_db)):
    # resolve friendly identifiers to internal IDs
    al_val = payload.airline_code
    al = db.query(Airline).filter((Airline.code == al_val.upper()) | (Airline.name == al_val)).first()
    if not al:
        raise HTTPException(status_code=400, detail=f"airline '{al_val}' not found")

    ac_val = payload.aircraft_model
    ac = db.query(Aircraft).filter(Aircraft.model == ac_val).first()
    if not ac:
        raise HTTPException(status_code=400, detail=f"aircraft model '{ac_val}' not found")

    dep_val = payload.departure_airport_code
    dep_ap = db.query(Airport).filter((Airport.code == dep_val.upper()) | (Airport.name == dep_val)).first()
    if not dep_ap:
        raise HTTPException(status_code=400, detail=f"departure airport '{dep_val}' not found")

    arr_val = payload.arrival_airport_code
    arr_ap = db.query(Airport).filter((Airport.code == arr_val.upper()) | (Airport.name == arr_val)).first()
    if not arr_ap:
        raise HTTPException(status_code=400, detail=f"arrival airport '{arr_val}' not found")

    # create flight (admin)
    flight = create_flight(
        db,
        airline_id=al.id,
        aircraft_id=ac.id,
        flight_number=payload.flight_number,
        departure_airport_id=dep_ap.id,
        arrival_airport_id=arr_ap.id,
        departure_time=payload.departure_time,
        arrival_time=payload.arrival_time,
        base_price=payload.base_price,
    )

    # map flight to response model
    # compute seats_left
    seats_left = db.query(func.count(Seat.id)).filter(Seat.flight_id == flight.id, Seat.is_available == True).scalar() or 0
    # we return a minimal FlightResponse mapping
    dep = db.query(Airport).filter(Airport.id == flight.departure_airport_id).first()
    arr = db.query(Airport).filter(Airport.id == flight.arrival_airport_id).first()
    airline = db.query(Airline).filter(Airline.id == flight.airline_id).first()

    return FlightResponse(
        id=flight.id,
        airline=airline.name if airline else "",
        flight_number=flight.flight_number,
        aircraft_model=(db.query(Aircraft).filter(Aircraft.id == flight.aircraft_id).first().model if db.query(Aircraft).filter(Aircraft.id == flight.aircraft_id).first() else None),
        source=dep.code if dep else "",
        destination=arr.code if arr else "",
        departure_time=flight.departure_time,
        arrival_time=flight.arrival_time,
        base_price=flight.base_price,
        seats_left=seats_left,
    )



@router.get("/{flight_id}", response_model=FlightResponse)
def get_flight(flight_id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    f = db.query(Flight).filter(Flight.id == flight_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="flight not found")
    dep = db.query(Airport).filter(Airport.id == f.departure_airport_id).first()
    arr = db.query(Airport).filter(Airport.id == f.arrival_airport_id).first()
    airline = db.query(Airline).filter(Airline.id == f.airline_id).first()
    seats_left = db.query(func.count(Seat.id)).filter(Seat.flight_id == f.id, Seat.is_available == True).scalar() or 0
    aircraft = db.query(Aircraft).filter(Aircraft.id == f.aircraft_id).first()
    return FlightResponse(
        id=f.id,
        airline=airline.name if airline else "",
        flight_number=f.flight_number,
        aircraft_model=aircraft.model if aircraft else None,
        source=dep.code if dep else "",
        destination=arr.code if arr else "",
        departure_time=f.departure_time,
        arrival_time=f.arrival_time,
        base_price=f.base_price,
        seats_left=seats_left,
    )


@router.put("/{flight_id}", response_model=FlightResponse)
def update_flight(flight_id: int, payload: FlightUpdate = Body(...), db: Session = Depends(get_db)):
    """Flexible partial update: accepts either IDs (e.g. `airline_id`) or
    human-friendly fields (`airline` by code/name, `source`/`destination` by
    airport code). Ignores `id` if sent.
    """
    f = db.query(Flight).filter(Flight.id == flight_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="flight not found")
    # convert Pydantic model to dict containing only provided fields
    payload_data = payload.dict(exclude_unset=True)

    # map friendly airline -> airline_id
    if "airline" in payload_data and payload_data.get("airline"):
        val = payload_data.get("airline")
        al = db.query(Airline).filter((Airline.code == val.upper()) | (Airline.name == val)).first()
        if not al:
            raise HTTPException(status_code=400, detail=f"airline '{val}' not found")
        f.airline_id = al.id

    # map aircraft_model -> aircraft_id
    if "aircraft_model" in payload_data and payload_data.get("aircraft_model"):
        am = payload_data.get("aircraft_model")
        ac = db.query(Aircraft).filter(Aircraft.model == am).first()
        if not ac:
            raise HTTPException(status_code=400, detail=f"aircraft model '{am}' not found")
        f.aircraft_id = ac.id

    # map source/destination to airport ids
    # support both `source` (code/name) and `departure_airport_code`
    if "source" in payload_data and payload_data.get("source"):
        sval = payload_data.get("source")
        ap = db.query(Airport).filter((Airport.code == sval.upper()) | (Airport.name == sval)).first()
        if not ap:
            raise HTTPException(status_code=400, detail=f"source airport '{sval}' not found")
        f.departure_airport_id = ap.id

    if "departure_airport_code" in payload_data and payload_data.get("departure_airport_code"):
        dcode = payload_data.get("departure_airport_code")
        apd = db.query(Airport).filter((Airport.code == dcode.upper()) | (Airport.name == dcode)).first()
        if not apd:
            raise HTTPException(status_code=400, detail=f"departure airport '{dcode}' not found")
        f.departure_airport_id = apd.id

    if "destination" in payload_data and payload_data.get("destination"):
        dval = payload_data.get("destination")
        ap2 = db.query(Airport).filter((Airport.code == dval.upper()) | (Airport.name == dval)).first()
        if not ap2:
            raise HTTPException(status_code=400, detail=f"destination airport '{dval}' not found")
        f.arrival_airport_id = ap2.id

    if "arrival_airport_code" in payload_data and payload_data.get("arrival_airport_code"):
        acode = payload_data.get("arrival_airport_code")
        apa = db.query(Airport).filter((Airport.code == acode.upper()) | (Airport.name == acode)).first()
        if not apa:
            raise HTTPException(status_code=400, detail=f"arrival airport '{acode}' not found")
        f.arrival_airport_id = apa.id

    # accept direct id fields if provided
    if "airline_id" in payload_data and payload_data.get("airline_id") is not None:
        f.airline_id = payload_data.get("airline_id")
    if "aircraft_id" in payload_data and payload_data.get("aircraft_id") is not None:
        f.aircraft_id = payload_data.get("aircraft_id")
    if "flight_number" in payload_data and payload_data.get("flight_number") is not None:
        f.flight_number = payload_data.get("flight_number")
    if "departure_airport_id" in payload_data and payload_data.get("departure_airport_id") is not None:
        f.departure_airport_id = payload_data.get("departure_airport_id")
    if "arrival_airport_id" in payload_data and payload_data.get("arrival_airport_id") is not None:
        f.arrival_airport_id = payload_data.get("arrival_airport_id")
    if "departure_time" in payload_data and payload_data.get("departure_time") is not None:
        f.departure_time = payload_data.get("departure_time")
    if "arrival_time" in payload_data and payload_data.get("arrival_time") is not None:
        f.arrival_time = payload_data.get("arrival_time")
    if "base_price" in payload_data and payload_data.get("base_price") is not None:
        f.base_price = payload_data.get("base_price")

    db.commit()
    db.refresh(f)
    dep = db.query(Airport).filter(Airport.id == f.departure_airport_id).first()
    arr = db.query(Airport).filter(Airport.id == f.arrival_airport_id).first()
    airline = db.query(Airline).filter(Airline.id == f.airline_id).first()
    seats_left = db.query(func.count(Seat.id)).filter(Seat.flight_id == f.id, Seat.is_available == True).scalar() or 0
    aircraft = db.query(Aircraft).filter(Aircraft.id == f.aircraft_id).first()
    return FlightResponse(
        id=f.id,
        airline=airline.name if airline else "",
        flight_number=f.flight_number,
        aircraft_model=aircraft.model if aircraft else None,
        source=dep.code if dep else "",
        destination=arr.code if arr else "",
        departure_time=f.departure_time,
        arrival_time=f.arrival_time,
        base_price=f.base_price,
        seats_left=seats_left,
    )


@router.delete("/{flight_id}")
def delete_flight(flight_id: int, db: Session = Depends(get_db)):
    f = db.query(Flight).filter(Flight.id == flight_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="flight not found")
    db.delete(f)
    db.commit()
    return {"message": "flight deleted"}
