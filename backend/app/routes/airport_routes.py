from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from app.config import get_db
from app.models.airport import Airport
from typing import List
from app.schemas.airport_schema import AirportCreate, AirportUpdate, AirportResponse

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=AirportResponse)
def create_airport(payload: AirportCreate, db: Session = Depends(get_db)):
    existing = db.query(Airport).filter(Airport.code == payload.code.upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail="airport code already exists")
    ap = Airport(code=payload.code.upper(), name=payload.name, city=payload.city, country=payload.country)
    db.add(ap)
    db.commit()
    db.refresh(ap)
    return ap


@router.get("/", response_model=List[AirportResponse])
def list_airports(db: Session = Depends(get_db)):
    return db.query(Airport).all()


@router.get("/{airport_id}", response_model=AirportResponse)
def get_airport(airport_id: int, db: Session = Depends(get_db)):
    ap = db.query(Airport).filter(Airport.id == airport_id).first()
    if not ap:
        raise HTTPException(status_code=404, detail="airport not found")
    return ap


@router.put("/{airport_id}", response_model=AirportResponse)
def update_airport(airport_id: int, payload: AirportCreate, db: Session = Depends(get_db)):
    ap = db.query(Airport).filter(Airport.id == airport_id).first()
    if not ap:
        raise HTTPException(status_code=404, detail="airport not found")
    ap.code = payload.code.upper()
    ap.name = payload.name
    ap.city = payload.city
    ap.country = payload.country
    db.commit()
    db.refresh(ap)
    return ap


@router.patch("/{airport_id}", response_model=AirportResponse)
def patch_airport(airport_id: int, payload: AirportUpdate = Body(...), db: Session = Depends(get_db)):
    ap = db.query(Airport).filter(Airport.id == airport_id).first()
    if not ap:
        raise HTTPException(status_code=404, detail="airport not found")
    data = payload.dict(exclude_unset=True)
    if "code" in data and data.get("code"):
        ap.code = data["code"].upper()
    if "name" in data:
        ap.name = data["name"]
    if "city" in data:
        ap.city = data["city"]
    if "country" in data:
        ap.country = data["country"]
    db.commit()
    db.refresh(ap)
    return ap


@router.delete("/{airport_id}")
def delete_airport(airport_id: int, db: Session = Depends(get_db)):
    ap = db.query(Airport).filter(Airport.id == airport_id).first()
    if not ap:
        raise HTTPException(status_code=404, detail="airport not found")
    db.delete(ap)
    db.commit()
    return {"message": "airport deleted"}
