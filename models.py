from enum import Enum
from typing import List

from pydantic import BaseModel


class GmapsMatrixElementData(BaseModel):
    text: str
    value: int


class GmapsMatrixElement(BaseModel):
    distance: GmapsMatrixElementData
    duration: GmapsMatrixElementData
    status: str


class GmapsMatrixRow(BaseModel):
    elements: List[GmapsMatrixElement]


class GmapsMatrixResponse(BaseModel):
    destination_addresses: List[str]
    origin_addresses: List[str]
    rows: List[GmapsMatrixRow]


class TravelMode(Enum):
    TRANSIT = "transit"
    CYCLING = "bicycling"
    WALKING = "walking"


class Attendee(BaseModel):
    name: str
    start_point: str
    end_point: str
    travel_mode: TravelMode = TravelMode.TRANSIT