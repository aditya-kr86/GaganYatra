from pydantic import BaseModel
from typing import Optional


class AirportCreate(BaseModel):
    code: str
    name: str
    city: Optional[str] = None
    country: Optional[str] = None


class AirportUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None


class AirportResponse(BaseModel):
    id: int
    code: str
    name: str
    city: Optional[str]
    country: Optional[str]

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "code": "DEL",
                "name": "Indira Gandhi Intl",
                "city": "Delhi",
                "country": "India"
            }
        }
