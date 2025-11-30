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
