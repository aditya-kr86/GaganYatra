from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from app.config import get_db
from app.models.aircraft import Aircraft
from typing import List
from app.schemas.aircraft_schema import AircraftCreate, AircraftUpdate, AircraftResponse

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=AircraftResponse)
def create_aircraft(payload: AircraftCreate, db: Session = Depends(get_db)):
    ac = Aircraft(model=payload.model, capacity=payload.capacity)
    db.add(ac)
    db.commit()
    db.refresh(ac)
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
    ac.model = payload.model
    ac.capacity = payload.capacity
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
