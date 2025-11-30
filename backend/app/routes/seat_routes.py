from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.config import get_db
from app.models.seat import Seat
from app.models.flight import Flight
from app.models.airline import Airline
from app.schemas.seat_schema import SeatCreate, SeatUpdate, SeatResponse
from app.schemas.seat_schema import SeatBulkCreate, SeatBulkUpdate, SeatBulkDelete, SeatAvailabilityResponse, SeatAvailabilityItem, SeatBulkUpdateItem, SeatBulkByFlightCreate

router = APIRouter()


@router.get("/", response_model=list[SeatResponse])
def list_seats(db: Session = Depends(get_db)):
    return db.query(Seat).all()


@router.get("/available", response_model=list[SeatResponse])
def available_seats(flight_id: int | None = Query(None, ge=1), flight_number: str | None = Query(None, min_length=1), seat_class: str | None = Query(None), limit: int | None = Query(None, ge=1), db: Session = Depends(get_db)):
    """List available seats for a flight.

    Either `flight_id` or `flight_number` must be provided. Optionally filter by `seat_class`.
    """
    if not flight_id and not flight_number:
        raise HTTPException(status_code=400, detail="flight_id or flight_number required")

    if flight_number and not flight_id:
        fl = db.query(Flight).filter(Flight.flight_number == flight_number).first()
        if not fl:
            raise HTTPException(status_code=404, detail="flight not found")
        flight_id = fl.id

    q = db.query(Seat).filter(Seat.flight_id == flight_id, Seat.is_available == True)
    if seat_class:
        sc = seat_class.strip().lower()
        q = q.filter(func.lower(Seat.seat_class) == sc)
    if limit:
        q = q.limit(limit)

    seats = q.order_by(Seat.id.asc()).all()
    return seats


@router.post("/bulk_create", response_model=list[SeatResponse], status_code=201)
def bulk_create_seats(payload: SeatBulkCreate, db: Session = Depends(get_db)):
    # resolve flight_number
    fl = db.query(Flight).filter(Flight.flight_number == payload.flight_number).first()
    if not fl:
        raise HTTPException(status_code=404, detail="flight not found")

    created = []
    # normalize class
    sc = payload.seat_class.strip().title() if payload.seat_class else "Economy"

    if payload.seat_numbers:
        # create provided seat numbers
        for sn in payload.seat_numbers:
            exists = db.query(Seat).filter(Seat.flight_id == fl.id, Seat.seat_number == sn).first()
            if exists:
                continue
            s = Seat(flight_id=fl.id, seat_number=sn, seat_class=sc, is_available=True)
            db.add(s)
            created.append(s)
    elif payload.count and payload.count > 0:
        # auto-generate numeric seat numbers starting after current max numeric seat_number
        existing_numbers = db.query(Seat).filter(Seat.flight_id == fl.id).all()
        max_num = 0
        for s in existing_numbers:
            if s.seat_number and s.seat_number.isdigit():
                num = int(s.seat_number)
                if num > max_num:
                    max_num = num
        for i in range(1, payload.count + 1):
            sn = str(max_num + i)
            s = Seat(flight_id=fl.id, seat_number=sn, seat_class=sc, is_available=True)
            db.add(s)
            created.append(s)
    else:
        raise HTTPException(status_code=400, detail="provide seat_numbers or count")

    db.commit()
    for s in created:
        db.refresh(s)
    return created


@router.patch("/bulk_update", response_model=list[SeatResponse])
def bulk_update_seats(payload: SeatBulkUpdate, db: Session = Depends(get_db)):
    updated = []
    for it in payload.seats:
        s = db.query(Seat).filter(Seat.id == it.id).first()
        if not s:
            continue
        data = it.dict(exclude_unset=True)
        if "seat_number" in data and data.get("seat_number") is not None:
            s.seat_number = data.get("seat_number")
        if "seat_class" in data and data.get("seat_class") is not None:
            s.seat_class = data.get("seat_class")
        if "is_available" in data and data.get("is_available") is not None:
            s.is_available = data.get("is_available")
        updated.append(s)
    db.commit()
    for s in updated:
        db.refresh(s)
    return updated


@router.delete("/bulk_delete")
def bulk_delete_seats(payload: SeatBulkDelete = Body(...), db: Session = Depends(get_db)):
    deleted_count = 0
    if payload.seat_ids:
        for sid in payload.seat_ids:
            s = db.query(Seat).filter(Seat.id == sid).first()
            if s:
                db.delete(s)
                deleted_count += 1
        db.commit()
        return {"deleted": deleted_count}

    if not payload.flight_number:
        raise HTTPException(status_code=400, detail="provide seat_ids or flight_number")

    fl = db.query(Flight).filter(Flight.flight_number == payload.flight_number).first()
    if not fl:
        raise HTTPException(status_code=404, detail="flight not found")

    q = db.query(Seat).filter(Seat.flight_id == fl.id)
    if payload.seat_class:
        q = q.filter(func.lower(Seat.seat_class) == payload.seat_class.strip().lower())
    deleted_count = q.delete(synchronize_session=False)
    db.commit()
    return {"deleted": deleted_count}


@router.get("/availability", response_model=SeatAvailabilityResponse)
def seats_availability(flight_number: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    fl = db.query(Flight).filter(Flight.flight_number == flight_number).first()
    if not fl:
        raise HTTPException(status_code=404, detail="flight not found")

    classes = db.query(Seat.seat_class).filter(Seat.flight_id == fl.id).distinct().all()
    class_list = [c[0] for c in classes if c[0]]
    items = []
    for cls in class_list:
        available_q = db.query(Seat).filter(Seat.flight_id == fl.id, func.lower(Seat.seat_class) == func.lower(cls), Seat.is_available == True).order_by(Seat.id.asc())
        booked_q = db.query(Seat).filter(Seat.flight_id == fl.id, func.lower(Seat.seat_class) == func.lower(cls), Seat.is_available == False).order_by(Seat.id.asc())
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


@router.post("/", response_model=SeatResponse, status_code=201)
def create_seat(payload: SeatCreate, db: Session = Depends(get_db)):
    seat = Seat(flight_id=payload.flight_id, seat_number=payload.seat_number, seat_class=payload.seat_class, is_available=payload.is_available)
    db.add(seat)
    db.commit()
    db.refresh(seat)
    return seat


@router.get("/{airline_code}/{flight_number}", response_model=SeatAvailabilityResponse)
def seats_by_airline_and_flight(airline_code: str, flight_number: str, db: Session = Depends(get_db)):
    fl = db.query(Flight).join(Airline).filter(Flight.flight_number == flight_number, func.lower(Airline.code) == airline_code.strip().lower()).first()
    if not fl:
        raise HTTPException(status_code=404, detail="flight not found for airline")

    classes = db.query(Seat.seat_class).filter(Seat.flight_id == fl.id).distinct().all()
    class_list = [c[0] for c in classes if c[0]]
    items = []
    for cls in class_list:
        available_q = db.query(Seat).filter(Seat.flight_id == fl.id, func.lower(Seat.seat_class) == func.lower(cls), Seat.is_available == True).order_by(Seat.id.asc())
        booked_q = db.query(Seat).filter(Seat.flight_id == fl.id, func.lower(Seat.seat_class) == func.lower(cls), Seat.is_available == False).order_by(Seat.id.asc())
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


@router.post("/add_seats", response_model=list[SeatResponse], status_code=201)
def add_seats_by_airline_and_flight(payload: SeatBulkByFlightCreate, db: Session = Depends(get_db)):
    # find flight by airline_code + flight_number
    fl = db.query(Flight).join(Airline).filter(Flight.flight_number == payload.flight_number, func.lower(Airline.code) == payload.airline_code.strip().lower()).first()
    if not fl:
        raise HTTPException(status_code=404, detail="flight not found for airline")

    created: list[Seat] = []
    # fetch existing seat numbers to compute numeric max
    existing = db.query(Seat).filter(Seat.flight_id == fl.id).all()
    max_num = 0
    for s in existing:
        if s.seat_number and s.seat_number.isdigit():
            n = int(s.seat_number)
            if n > max_num:
                max_num = n

    for cls in payload.classes:
        sc = cls.seat_class.strip().title() if cls.seat_class else "Economy"
        if cls.seat_numbers:
            for sn in cls.seat_numbers:
                exists = db.query(Seat).filter(Seat.flight_id == fl.id, Seat.seat_number == sn).first()
                if exists:
                    continue
                s = Seat(flight_id=fl.id, seat_number=sn, seat_class=sc, is_available=True)
                db.add(s)
                created.append(s)
        elif cls.count and cls.count > 0:
            for i in range(1, cls.count + 1):
                sn = str(max_num + i)
                s = Seat(flight_id=fl.id, seat_number=sn, seat_class=sc, is_available=True)
                db.add(s)
                created.append(s)
            max_num += cls.count
        else:
            # nothing provided for this class
            continue

    db.commit()
    for s in created:
        db.refresh(s)
    return created
