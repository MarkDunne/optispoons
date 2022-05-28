import datetime
from collections import defaultdict
from datetime import datetime as datetime_type
from enum import IntEnum, Enum
from operator import xor
from typing import List

import diskcache
import requests
from fastapi import FastAPI, Body, Query, HTTPException
from pydantic import BaseModel, BaseSettings, Field, parse_obj_as


# TODO use an LRU cache here
#  See https://fastapi.tiangolo.com/advanced/settings/
from models import GmapsMatrixResponse, Attendee


class Settings(BaseSettings):
    gmaps_api_key: str = Field(description="some desc")

    class Config:
        secrets_dir = "/var/run/"


settings = Settings()
print(settings)

app = FastAPI()
cache = diskcache.Cache(".cache")

ONE_DAY_SECONDS = 24 * 60 * 60


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

    class Config:
        frozen = True


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


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i : i + n]


def gmaps_matrix(origins=None, destinations=None, travel_mode="transit", **kwargs):

    if not xor(len(origins) > 1, len(destinations) > 1):
        raise Exception("Unexpected args")

    base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "units": "imperial",
        "origins": '|'.join(origins),
        "destinations": '|'.join(destinations),
        "mode": travel_mode,
        "key": settings.gmaps_api_key,
        **kwargs
    }

    url = base_url + '?' + '&'.join(f"{key}={value}" for key, value in params.items())
    response = requests.get(url)
    response.raise_for_status()

    gmaps_response = GmapsMatrixResponse.parse_obj(response.json())

    return [
        elem.duration.value / 60 for row in gmaps_response.rows for elem in row.elements
    ]


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


def solve(attendees: List[Attendee], spoons: SpoonsSubRegion):
    results = defaultdict(dict)
    for attendee in attendees:
        print(f"Calculating routes for {attendee.name}")
        for pubs in chunks(spoons.items, 20):
            pubs_locations = [pub.coord_string() for pub in pubs]

            travel_times_to_pubs = gmaps_matrix(
                origins=[attendee.start_point],
                destinations=pubs_locations,
                travel_mode=attendee.travel_mode.value,
                arrival_time=int(get_next_meeting_time().timestamp())
            )
            travel_times_from_pubs = gmaps_matrix(
                origins=pubs_locations,
                destinations=[attendee.end_point],
                travel_mode=attendee.travel_mode.value,
                departure_time=int((get_next_meeting_time() + datetime.timedelta(hours=2)).timestamp())
            )

            for pub, tt_from, tt_to in zip(
                pubs, travel_times_to_pubs, travel_times_from_pubs, strict=True
            ):
                results[pub][attendee.name] = tt_from + tt_to
    return results


#
@app.post("/calculate_optimal_spoons")
def calculate_optimal_spoons(request: OptiSpoonsRequest):
    return solve(
        request.attendees,
        request_spoons_data(SearchRegion.ENGLAND, SearchType.ALL_VENUES, "London"),
    )


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
