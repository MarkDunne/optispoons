import datetime
from datetime import datetime as datetime_type
from itertools import groupby
from typing import List

import diskcache
import numpy as np
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, BaseSettings, Field
from starlette.responses import RedirectResponse

from models import (
    GmapsMatrixResponse,
    Attendee,
    SpoonsSubRegion,
    Spoons,
    SearchRegion,
    SearchType,
)


# TODO use an LRU cache here
#  See https://fastapi.tiangolo.com/advanced/settings/
class Settings(BaseSettings):
    gmaps_api_key: str = Field(description="Google Maps API Key")

    class Config:
        env_file = ".env"


settings = Settings()

app = FastAPI()
cache = diskcache.Cache(".cache")

ONE_DAY_SECONDS = 24 * 60 * 60


@cache.memoize(expire=ONE_DAY_SECONDS)
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


@cache.memoize(expire=ONE_DAY_SECONDS)
def gmaps_matrix(origins=None, destinations=None, travel_mode="transit", **kwargs):
    """
    Return travel times to each destination for each origin
    """
    base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "units": "imperial",
        "origins": "|".join(origins),
        "destinations": "|".join(destinations),
        "mode": travel_mode,
        "key": settings.gmaps_api_key,
        **kwargs,
    }

    url = base_url + "?" + "&".join(f"{key}={value}" for key, value in params.items())
    response = requests.get(url)
    response.raise_for_status()

    gmaps_response = GmapsMatrixResponse.parse_obj(response.json())

    return np.array(
        [
            [elem.duration.value / 60 for elem in row.elements]
            for row in gmaps_response.rows
        ]
    )


def get_next_meeting_time():
    # Todo parameterize default day and time
    days = 0 - datetime.datetime.today().weekday() + 7
    return datetime.datetime.combine(
        (datetime.datetime.today() + datetime.timedelta(days=days)).date(),
        datetime.time(hour=19, minute=0),
    )


# Todo add region option to this
class OptiSpoonsRequest(BaseModel):
    attendees: List[Attendee]
    datetime: datetime_type = get_next_meeting_time()


def group_attendees_by_travel_mode(attendees):
    key_func = lambda attendee: attendee.travel_mode.value
    iterable_result = groupby(sorted(attendees, key=key_func), key=key_func)
    return [(mode, list(attendees)) for (mode, attendees) in iterable_result]


def round_trip_travel_times_for_travel_mode(
    start_points, mid_points, end_points, travel_mode
):
    """
    Return results by midpoint
    """
    assert len(start_points) == len(end_points)

    travel_times_to_pubs = gmaps_matrix(
        origins=start_points,
        destinations=mid_points,
        travel_mode=travel_mode,
        arrival_time=int(get_next_meeting_time().timestamp()),
    )

    travel_times_from_pubs = gmaps_matrix(
        origins=mid_points,
        destinations=end_points,
        travel_mode=travel_mode,
        departure_time=int(
            (get_next_meeting_time() + datetime.timedelta(hours=2)).timestamp()
        ),
    )

    return travel_times_to_pubs.T + travel_times_from_pubs


def calculate_pub_travel_times(spoons: List[Spoons], attendees: List[Attendee]):
    """
    For a given set of pubs and attendees, return the travel time statistics
    for each pub and attendee, in order of pub
    """
    attendee_groups = group_attendees_by_travel_mode(attendees)
    pub_chunk_travel_times = []
    for pubs_chunk in chunks(spoons, 20):
        attendee_group_travel_times = []
        for travel_mode, attendees_group in attendee_groups:
            travel_times = round_trip_travel_times_for_travel_mode(
                [attendee.start_point for attendee in attendees_group],
                [pub.coord_string() for pub in pubs_chunk],
                [attendee.end_point for attendee in attendees_group],
                travel_mode,
            )
            attendee_group_travel_times.append(travel_times)
        pub_chunk_travel_times.append(np.hstack(attendee_group_travel_times))
    return np.vstack(pub_chunk_travel_times)


@app.post("/calculate_optimal_spoons")
def calculate_optimal_spoons(request: OptiSpoonsRequest):
    pubs = request_spoons_data(SearchRegion.ENGLAND, SearchType.ALL_VENUES, "London")

    pub_travel_times = calculate_pub_travel_times(pubs.items, request.attendees)
    pub_scores = (pub_travel_times ** 2).sum(axis=1)

    return pubs.items[pub_scores.argmin()]


@app.get("/get_spoons_in_subregion")
async def get_spoons_in_subregion(
    search_region: SearchRegion = SearchRegion.ENGLAND,
    search_type: SearchType = SearchType.ALL_VENUES,
    search_subregion: str = "London",
) -> SpoonsSubRegion:
    return request_spoons_data(
        search_region.value, search_type.query_value, search_subregion
    )


@app.get("/")
async def root():
    return RedirectResponse("/docs")


if __name__ == "__main__":
    pass
