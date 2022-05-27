from enum import IntEnum, Enum

import diskcache
import requests
from fastapi import FastAPI, Body, Query, HTTPException
from pydantic import BaseModel

app = FastAPI()
cache = diskcache.Cache(".cache")

ONE_DAY_SECONDS = 24 * 60 * 60


class SearchType(IntEnum):
    ALL_VENUES = 0
    PUBS_ONLY = 1
    HOTELS_ONLY = 2


class SearchRegion(Enum):
    ENGLAND = "England"
    WALES = "Wales"
    NORTHERN_IRELAND = "N Ireland"


@cache.memoize(expire=ONE_DAY_SECONDS)
def request_spoons_data(search_region, search_type):
    return requests.post(
        "https://www.jdwetherspoon.com/api/advancedsearch",
        headers={
            "accept": "application/json",
            "content-type": "application/json;charset=UTF-8",
        },
        json={
            "region": search_region.value,
            "paging": {"UsePagination": False},
            "facilities": [],
            "searchType": search_type.value,
        },
    ).json()


@app.get("/get_spoons_in_subregion")
async def get_spoons_in_subregion(
    search_region: SearchRegion = SearchRegion.ENGLAND,
    search_type: SearchType = SearchType.ALL_VENUES,
    search_subregion: str = "London",
):
    data = request_spoons_data(search_region, search_type)
    for subregion in data["regions"][0]["subRegions"]:
        if subregion["name"] == search_subregion:
            return subregion
    else:
        raise HTTPException(status_code=404, detail="Subregion not found")


if __name__ == "__main__":
    pass
