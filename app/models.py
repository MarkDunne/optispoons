from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, validator


class SearchType(str, Enum):
    ALL_VENUES = "all_venues", 0
    PUBS_ONLY = "pubs_only", 1
    HOTELS_ONLY = "hotels_only", 2

    def __new__(cls, label, query_value):
        obj = str.__new__(cls)
        obj._value_ = label
        obj.query_value = query_value
        return obj


class SearchRegion(str, Enum):
    ENGLAND = "England"
    WALES = "Wales"
    NORTHERN_IRELAND = "N Ireland"
    IRELAND = "Republic of Ireland"


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
    status: str

    @validator("status")
    def check_status(cls, value):
        if value != "OK":
            raise ValueError(f"Status not OK: {value}")
        return value


class TravelMode(Enum):
    TRANSIT = "transit"
    CYCLING = "bicycling"
    WALKING = "walking"


class Attendee(BaseModel):
    name: str
    start_point: str
    end_point: str
    travel_mode: TravelMode = TravelMode.TRANSIT


class Spoons(BaseModel):
    lat: float
    lng: float
    address1: str
    city: str
    county: str
    postcode: str
    name: str
    score: Optional[float]

    def coord_string(self) -> str:
        return f"{self.lat:.6f},{self.lng:.6f}"

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"{self.name}({self.coord_string()})"

    class Config:
        frozen = True


class SpoonsSubRegion(BaseModel):
    name: str
    items: List[Spoons]
