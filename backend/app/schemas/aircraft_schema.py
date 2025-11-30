from pydantic import BaseModel
from typing import Optional


class AircraftCreate(BaseModel):
    model: str
    capacity: int


class AircraftUpdate(BaseModel):
    model: Optional[str] = None
    capacity: Optional[int] = None


class AircraftResponse(BaseModel):
    id: int
    model: str
    capacity: int

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "model": "Boeing 737",
                "capacity": 180
            }
        }
