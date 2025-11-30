from pydantic import BaseModel
from typing import Optional


class AircraftCreate(BaseModel):
    model: str
    capacity: int
    economy_count: Optional[int] = 0
    premium_economy_count: Optional[int] = 0
    business_count: Optional[int] = 0
    first_count: Optional[int] = 0


class AircraftUpdate(BaseModel):
    model: Optional[str] = None
    capacity: Optional[int] = None
    economy_count: Optional[int] = None
    premium_economy_count: Optional[int] = None
    business_count: Optional[int] = None
    first_count: Optional[int] = None


class AircraftResponse(BaseModel):
    id: int
    model: str
    capacity: int
    economy_count: int
    premium_economy_count: int
    business_count: int
    first_count: int

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "model": "Boeing 737",
                "capacity": 180
            }
        }
