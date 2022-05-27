from starlette.testclient import TestClient

from main import app

client = TestClient(app)


def test_get_spoons_listing():
    response = client.get("/get_spoons_listing")
    assert response.status_code == 200
