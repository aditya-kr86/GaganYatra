from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class PaymentCreate(BaseModel):
    # Only booking_reference is required now; booking_id removed.
    booking_reference: str
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

    model_config = ConfigDict(from_attributes=True)


class PaymentUpdate(BaseModel):
    status: Optional[str] = None
