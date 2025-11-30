from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PaymentCreate(BaseModel):
    booking_id: int
    amount: float
    method: str


class PaymentResponse(BaseModel):
    id: int
    booking_id: int
    amount: float
    method: str
    status: str
    transaction_id: Optional[str]
    paid_at: datetime

    class Config:
        orm_mode = True


class PaymentUpdate(BaseModel):
    status: Optional[str] = None
