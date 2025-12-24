from pydantic import BaseModel, ConfigDict
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

    model_config = ConfigDict(from_attributes=True, json_schema_extra={
            "example": {
                "id": 1,
                "name": "National Airlines",
                "code": "NA"
            }
        })
