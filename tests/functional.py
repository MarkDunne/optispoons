from main import gmaps_matrix, solve
from models import Spoons, SpoonsSubRegion, Attendee, TravelMode


def test_gmaps_matrix():
    origins = ["London SW1A 1AA", "Beckenham Hill Rd, Beckenham BR3 1SY"]
    destinations = [
        "51.545456,-0.055087",
        "51.543751,0.003998",
        "51.511494,-0.072858",
        "51.517643,-0.080963",
    ]
    result = gmaps_matrix(origins=origins, destinations=destinations)

    assert result.shape == (len(origins), len(destinations))


def test_solve():
    spoons = [
        Spoons(
            lat=51.5454559326172,
            lng=-0.0550870001316071,
            address1="282–284 Mare Street",
            city="Hackney",
            county="London",
            postcode="E8 1HE",
            name="Baxter’s Court",
        ),
        Spoons(
            lat=51.5437507629395,
            lng=0.00399800017476082,
            address1="146–148 The Grove",
            city="Stratford",
            county="London",
            postcode="E15 1NS",
            name="Goldengrove",
        ),
        Spoons(
            lat=51.5114936828613,
            lng=-0.0728579983115196,
            address1="87–91 Mansell Street",
            city="Tower Hamlets",
            county="London",
            postcode="E1 8AN",
            name="Goodman’s Field",
        ),
    ]

    attendees = [
        Attendee(
            name="Lizz",
            start_point="London SW1A 1AA",
            end_point="London SW1A 1AA",
            travel_mode=TravelMode.TRANSIT,
        ),
        Attendee(
            name="Lord Beckenham",
            start_point="Beckenham Hill Rd, Beckenham BR3 1SY",
            end_point="Beckenham Hill Rd, Beckenham BR3 1SY",
            travel_mode=TravelMode.CYCLING,
        ),
        Attendee(
            name="Lord Sutton",
            start_point="High St, Sutton SM1 1JA",
            end_point="High St, Sutton SM1 1JA",
            travel_mode=TravelMode.TRANSIT,
        ),
    ]

    result = solve(spoons, attendees)

    assert result.shape == (len(spoons), len(attendees))
