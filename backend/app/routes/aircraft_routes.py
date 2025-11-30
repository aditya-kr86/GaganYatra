from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from app.config import get_db
from app.models.aircraft import Aircraft
from app.models.aircraft_seat_template import AircraftSeatTemplate
from typing import List
from app.schemas.aircraft_schema import AircraftCreate, AircraftUpdate, AircraftResponse

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=AircraftResponse)
def create_aircraft(payload: AircraftCreate, db: Session = Depends(get_db)):
    # If class counts provided, compute capacity from their sum to keep data consistent
    total = payload.capacity
    sum_counts = (payload.economy_count or 0) + (payload.premium_economy_count or 0) + (payload.business_count or 0) + (payload.first_count or 0)
    if sum_counts > 0:
        total = sum_counts
    ac = Aircraft(
        model=payload.model,
        capacity=total,
        economy_count=payload.economy_count or 0,
        premium_economy_count=payload.premium_economy_count or 0,
        business_count=payload.business_count or 0,
        first_count=payload.first_count or 0,
    )
    db.add(ac)
    db.commit()
    db.refresh(ac)

    # Create aircraft seat templates so flights can be auto-seated from the template.
    # Skip if templates already exist for this aircraft.
    existing = db.query(AircraftSeatTemplate).filter(AircraftSeatTemplate.aircraft_id == ac.id).first()
    if not existing:
        eco = int(ac.economy_count or 0)
        prem = int(ac.premium_economy_count or 0)
        bus = int(ac.business_count or 0)
        first = int(ac.first_count or 0)

        templates = []
        idx = 1
        def add_block(count, cls_name):
            nonlocal idx
            for _ in range(count):
                templates.append(AircraftSeatTemplate(aircraft_id=ac.id, seat_number=str(idx), seat_class=cls_name))
                idx += 1

        if first > 0:
            add_block(first, "First")
        if bus > 0:
            add_block(bus, "Business")
        if prem > 0:
            add_block(prem, "Premium Economy")
        if eco > 0:
            add_block(eco, "Economy")

        if templates:
            db.add_all(templates)
            db.commit()
    return ac


@router.get("/", response_model=List[AircraftResponse])
def list_aircraft(db: Session = Depends(get_db)):
    return db.query(Aircraft).all()


@router.get("/{aircraft_id}", response_model=AircraftResponse)
def get_aircraft(aircraft_id: int, db: Session = Depends(get_db)):
    ac = db.query(Aircraft).filter(Aircraft.id == aircraft_id).first()
    if not ac:
        raise HTTPException(status_code=404, detail="aircraft not found")
    return ac


@router.put("/{aircraft_id}", response_model=AircraftResponse)
def update_aircraft(aircraft_id: int, payload: AircraftCreate, db: Session = Depends(get_db)):
    ac = db.query(Aircraft).filter(Aircraft.id == aircraft_id).first()
    if not ac:
        raise HTTPException(status_code=404, detail="aircraft not found")
    # For full update use provided values; if counts provided, compute capacity
    ac.model = payload.model
    sum_counts = (payload.economy_count or 0) + (payload.premium_economy_count or 0) + (payload.business_count or 0) + (payload.first_count or 0)
    ac.capacity = sum_counts if sum_counts > 0 else payload.capacity
    ac.economy_count = payload.economy_count or 0
    ac.premium_economy_count = payload.premium_economy_count or 0
    ac.business_count = payload.business_count or 0
    ac.first_count = payload.first_count or 0
    db.commit()
    db.refresh(ac)
    return ac


@router.patch("/{aircraft_id}", response_model=AircraftResponse)
def patch_aircraft(aircraft_id: int, payload: AircraftUpdate = Body(...), db: Session = Depends(get_db)):
    ac = db.query(Aircraft).filter(Aircraft.id == aircraft_id).first()
    if not ac:
        raise HTTPException(status_code=404, detail="aircraft not found")
    data = payload.dict(exclude_unset=True)
    if "model" in data:
        ac.model = data["model"]
    if "capacity" in data:
        ac.capacity = data["capacity"]
    if "economy_count" in data:
        ac.economy_count = data["economy_count"]
    if "premium_economy_count" in data:
        ac.premium_economy_count = data["premium_economy_count"]
    if "business_count" in data:
        ac.business_count = data["business_count"]
    if "first_count" in data:
        ac.first_count = data["first_count"]
    db.commit()
    db.refresh(ac)
    return ac


@router.delete("/{aircraft_id}")
def delete_aircraft(aircraft_id: int, db: Session = Depends(get_db)):
    ac = db.query(Aircraft).filter(Aircraft.id == aircraft_id).first()
    if not ac:
        raise HTTPException(status_code=404, detail="aircraft not found")
    db.delete(ac)
    db.commit()
    return {"message": "aircraft deleted"}
