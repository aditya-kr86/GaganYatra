from pydantic import BaseModel, EmailStr
from typing import Optional


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: Optional[str] = "customer"
    airline_id: Optional[int] = None
    airport_id: Optional[int] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[str] = None
    airline_id: Optional[int] = None
    airport_id: Optional[int] = None


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str
    airline_id: Optional[int] = None
    airport_id: Optional[int] = None

    class Config:
        orm_mode = True
