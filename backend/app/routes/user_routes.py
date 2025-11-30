from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.config import get_db
from app.models.user import User
from app.schemas.user_schema import UserCreate, UserUpdate, UserResponse

router = APIRouter()


@router.get("/", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()


@router.post("/", response_model=UserResponse, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    # NOTE: password is stored in `password_hash` as provided for demo purposes.
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="email already registered")
    user = User(full_name=payload.full_name, email=payload.email, password_hash=payload.password, role=payload.role, airline_id=payload.airline_id, airport_id=payload.airport_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="user not found")
    return u


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="user not found")
    data = payload.dict(exclude_unset=True)
    for k, v in data.items():
        if k == "password":
            setattr(u, "password_hash", v)
        else:
            setattr(u, k, v)
    db.commit()
    db.refresh(u)
    return u


@router.patch("/{user_id}")
def patch_user(user_id: int, payload: UserUpdate = Body(...), db: Session = Depends(get_db)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="user not found")
    data = payload.dict(exclude_unset=True)
    for k, v in data.items():
        if k == "password":
            setattr(u, "password_hash", v)
        else:
            setattr(u, k, v)
    db.commit()
    db.refresh(u)
    return u


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="user not found")
    db.delete(u)
    db.commit()
    return {"message": "user deleted"}
