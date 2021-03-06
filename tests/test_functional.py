from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_spoons_listing():
    response = client.get("/get_spoons_in_subregion")
    assert response.status_code == 200


def test_optimal_spoons():
    response = client.post(
        "/calculate_optimal_spoons",
        json={
            "attendees": [
                {
                    "name": "Lizz",
                    "start_point": "London SW1A 1AA",
                    "end_point": "London SW1A 1AA",
                },
                {
                    "name": "Lord Beckenham",
                    "start_point": "Beckenham Hill Rd, Beckenham BR3 1SY",
                    "end_point": "Beckenham Hill Rd, Beckenham BR3 1SY",
                    "travel_mode": "bicycling",
                },
                {
                    "name": "Lord Sutton",
                    "start_point": "High St, Sutton SM1 1JA",
                    "end_point": "High St, Sutton SM1 1JA",
                    "travel_mode": "transit",
                },
            ],
            "search_region": "Wales",
            "search_subregion": "Cardiff",
            "meeting_datetime": "2022-07-25T19:00:00"
        },
    )

    return response.ok
