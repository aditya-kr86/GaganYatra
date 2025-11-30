from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from app.config import get_db
from app.schemas.payment_schema import PaymentCreate, PaymentResponse, PaymentUpdate
from app.services.flight_service import create_payment, get_payment_by_transaction

router = APIRouter()


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment_api(payload: PaymentCreate, db: Session = Depends(get_db)):
    # very small validation
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="amount must be > 0")

    tx = create_payment(db, booking_id=payload.booking_id, amount=payload.amount, method=payload.method)
    return tx


@router.get("/{transaction_id}", response_model=PaymentResponse)
def get_payment_api(transaction_id: str, db: Session = Depends(get_db)):
    tx = get_payment_by_transaction(db, transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail="transaction not found")
    return tx


@router.patch("/{transaction_id}", response_model=PaymentResponse)
def patch_payment_api(transaction_id: str, payload: PaymentUpdate = Body(...), db: Session = Depends(get_db)):
    tx = get_payment_by_transaction(db, transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail="transaction not found")
    data = payload.dict(exclude_unset=True)
    if "status" in data and data.get("status"):
        tx.status = data.get("status")
    db.commit()
    db.refresh(tx)
    return tx
