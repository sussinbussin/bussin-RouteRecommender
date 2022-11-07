import pytest
from application import create_app

@pytest.fixture()
def application():
    application = create_app("config")
    return application

@pytest.fixture()
def client(application):
    return application.test_client()

headers = {
    "Authorization": "Bearer eyJraWQiOiJGNFRkbzROUUQ4ZlFVeWd2bFB6b1Z3bU83YjdcL3RVT3JwZEJha3R0SjFDbz0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiI2NDc1YThlNi0wM2ZlLTQ2YjgtOTNlYi1kNTFiMTYyZmMwMGIiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiaXNzIjoiaHR0cHM6XC9cL2NvZ25pdG8taWRwLmFwLXNvdXRoZWFzdC0xLmFtYXpvbmF3cy5jb21cL2FwLXNvdXRoZWFzdC0xX2NBSjlFZ3FMMSIsImNvZ25pdG86dXNlcm5hbWUiOiJzcHJpbmdiYWNrdGVzdCIsIm9yaWdpbl9qdGkiOiIwMDcyZWExZS04NWI2LTQ3ZGYtOTNiNS1mNDYzZjM0MTNkZmQiLCJhdWQiOiI0cHY3cmFkNHZxamsxOWo1MGhscGc2amxlbyIsImV2ZW50X2lkIjoiODUxMzA4N2UtM2Q5Ny00OWYwLWI0MDEtNWFiN2JmZDA2YzkwIiwidG9rZW5fdXNlIjoiaWQiLCJhdXRoX3RpbWUiOjE2Njc4MzA4MzUsImV4cCI6MTY2NzkxNzIzNSwiaWF0IjoxNjY3ODMwODM1LCJqdGkiOiI4MzI2N2NjMS0yYTVhLTQ2YjUtODMwZi05MTgxNGEyNmRjMzEiLCJlbWFpbCI6InNwcmluZ2JhY2t0ZXN0QGdtYWlsLmNvbSJ9.thgZ7RxUXicKRitT0j6-SQvWVu1-pymeW0VTzTN1srtqqkctNjZGIABW9iVMo4sC8UNs0zSha7bzIH6SpDnuFj9uxVue0wdztcCOHa6UaDff_ib9pT_YbNhe3h1feqXIQ2Ykk_vlZb5hfxMNN6PjxKWgfs31JbvY1hSm_g_UH-hSIDVJCQzB3rXmRWsjwpI3N5l8TCbxF8mjb0CgD1AK61xwDd9xG_NRKNuXuEFuVb8odAUU9ps2PNTVMei-t9n-SrU9wTuUTOFL9hEyIJ7n9GSdOUMW4LaqDwHVSg_TEJW3iJOpNSzNI_qSrh-CU2ptVOxh7nHNFngbOD20EwwqYQ"
}

def test_missing_inputs(client):
    response = client.post("/v1/routes", headers=headers)
    assert response.status_code == 400
    assert response.json["Message"] == "Please indicate start and end coordinates"

def test_not_float(client):
    response = client.post("/v1/routes", data={
        "Origin Latitude": "origin",
        "Origin Longitude": "origin",
        "Destination Latitude": "destination",
        "Destination Longitude": "destination",
    }, headers=headers)
    assert response.status_code == 400
    assert response.json["Message"] == "Please input proper coordinates"

def test_invalid_lat_lng(client):
    response = client.post("/v1/routes", data={
        "Origin Latitude": 91.0000,
        "Origin Longitude": 181.0000,
        "Destination Latitude": 91.0000,
        "Destination Longitude": 180.0000,
    }, headers=headers)
    assert response.status_code == 400
    assert response.json["Message"] == "Please input proper coordinates"

def test_outside_singapore(client):
    response = client.post("/v1/routes", data={
        "Origin Latitude": 35.689653163130394,
        "Origin Longitude": 139.69973343000046,
        "Destination Latitude": 35.644475635831306,
        "Destination Longitude": 139.784349383573,
    })
    assert response.status_code == 400
    assert response.json["Message"] == "Please enter coordinates within Singapore"

def test_no_drivers(client):
    response = client.post("/v1/routes", data={
        "Origin Latitude": 1.2462887209225797,
        "Origin Longitude": 103.82543076084995,
        "Destination Latitude": 1.251762343020259,
        "Destination Longitude": 103.84801387644136,
    }, headers=headers)
    assert response.status_code == 200
    assert response.json["Message"] == "Sorry there are no available drivers for your journey at the specified time"

def test_no_public_transport(client):
    response = client.post("/v1/routes", data={
        "Origin Latitude": 1.3359366979407206,
        "Origin Longitude": 103.92330895306216,
        "Destination Latitude": 1.360953236234917,
        "Destination Longitude": 103.98966495344162,
    }, headers=headers)
    assert response.status_code == 200
    assert response.json["Message"] == "Sorry there are no available drivers for your journey at the specified time"

def test_golden_route(client):
    response = client.post("/v1/routes", data={
        "Origin Latitude": 1.29770,
        "Origin Longitude": 103.84912,
        "Destination Latitude": 1.44917,
        "Destination Longitude": 103.81990,
    }, headers=headers)
    assert response.status_code == 200
    assert response.json["Recommended Driver Routes"] is not None