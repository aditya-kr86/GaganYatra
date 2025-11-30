from pydantic import BaseModel
from typing import Optional


class AirlineCreate(BaseModel):
    name: str
    code: str


class AirlineUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None


class AirlineResponse(BaseModel):
    id: int
    name: str
    code: str

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "name": "National Airlines",
                "code": "NA"
            }
        }
