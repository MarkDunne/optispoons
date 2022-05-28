import datetime
from datetime import datetime as datetime_type
from enum import IntEnum, Enum
from typing import List

import diskcache
import requests
from fastapi import FastAPI, Body, Query, HTTPException
from pydantic import BaseModel, BaseSettings, Field, parse_obj_as


# TODO use an LRU cache here
#  See https://fastapi.tiangolo.com/advanced/settings/
class Settings(BaseSettings):
    gmaps_api_key: str = Field(description="some desc")

    class Config:
        secrets_dir = "/var/run/"


settings = Settings()
print(settings)

app = FastAPI()
cache = diskcache.Cache(".cache")

ONE_DAY_SECONDS = 24 * 60 * 60


class SearchType(Enum):
    ALL_VENUES = "all_venues", 0
    PUBS_ONLY = "pubs_only", 1
    HOTELS_ONLY = "hotels_only", 2

    def __new__(cls, label, query_value):
        obj = object.__new__(cls)
        obj._value_ = label
        obj.query_value = query_value
        return obj


class SearchRegion(Enum):
    ENGLAND = "England"
    WALES = "Wales"
    NORTHERN_IRELAND = "N Ireland"


class Spoons(BaseModel):
    lat: float
    lng: float
    address1: str
    city: str
    county: str
    postcode: str
    name: str

    def coord_string(self) -> str:
        return f"{self.lat:.6f},{self.lng:.6f}"


class SpoonsSubRegion(BaseModel):
    name: str
    items: List[Spoons]


@cache.memoize(expire=1)
def request_spoons_data(
    search_region, search_type, search_subregion
) -> SpoonsSubRegion:
    response = requests.post(
        "https://www.jdwetherspoon.com/api/advancedsearch",
        headers={
            "accept": "application/json",
            "content-type": "application/json;charset=UTF-8",
        },
        json={
            "region": search_region,
            "paging": {"UsePagination": False},
            "facilities": [],
            "searchType": search_type,
        },
    ).json()

    for subregion in response["regions"][0]["subRegions"]:
        if subregion["name"] == search_subregion:
            return SpoonsSubRegion.parse_obj(subregion)
    else:
        raise HTTPException(status_code=404, detail="Subregion not found")


def gmaps_matrix(origins=None, destinations=None, travel_mode="transit"):
    base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    url = f"{base_url}?units=imperial&mode={travel_mode}&origins={'|'.join(origins)}&destinations={'|'.join(destinations)}&key={settings.gmaps_api_key}"

    response = requests.get(url).json()

    for origin, row in zip(origins, response["rows"]):
        for dest, duration in zip(
            dests, [elem["duration"]["value"] for elem in row["elements"]]
        ):
            print(origin, " -> ", dest, " : ", duration / 60)
            spoons_times[origin][dests[dest]] += duration / 60


class Attendee(BaseModel):
    name: str
    start_point: str
    end_point: str
    mode_of_transport: str = "transit"


def get_next_meeting_time():
    # Todo parameterize default day and time
    days = 0 - datetime.datetime.today().weekday() + 7
    return datetime.datetime.combine(
        (datetime.datetime.today() + datetime.timedelta(days=days)).date(),
        datetime.time(hour=19, minute=0),
    )


class OptiSpoonsRequest(BaseModel):
    attendees: List[Attendee]
    datetime: datetime_type = get_next_meeting_time()


def solve(attendees: List[Attendee], spoons: List[Spoons]):
    pass


@app.post("/calculate_optimal_spoons")
def calculate_optimal_spoons(request: OptiSpoonsRequest):
    return dict(msg="ok")


@app.get("/get_spoons_in_subregion")
async def get_spoons_in_subregion(
    search_region: SearchRegion = SearchRegion.ENGLAND,
    search_type: SearchType = SearchType.ALL_VENUES,
    search_subregion: str = "London",
) -> SpoonsSubRegion:
    return request_spoons_data(
        search_region.value, search_type.query_value, search_subregion
    )


if __name__ == "__main__":
    pass
