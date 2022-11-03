# import pytest
# from application import application

# @pytest.fixture()
# def application():
#     app = application.create_app("config")
#     return app

# @pytest.fixture()
# def client(app):
#     return app.test_client()


# @pytest.fixture()
# def runner(app):
#     return app.test_cli_runner()

# def missing_inputs(client):
#     response = client.post("/v1/routes")
#     assert response.status_code == 400
#     assert response.json["Message"] == "Please indicate start and end coordinates"

# def not_float(client):
#     response = client.post("/v1/routes", data={
#         "Origin Latitude": "origin",
#         "Origin Longitude": "origin",
#         "Destination Latitude": "destination",
#         "Destination Longitude": "destination",
#     })
#     assert response.status_code == 400
#     assert response.json["Message"] == "Please input proper coordinates"

# def invalid_lat_lng(client):
#     response = client.post("/v1/routes", data={
#         "Origin Latitude": 91.0000,
#         "Origin Longitude": 181.0000,
#         "Destination Latitude": 91.0000,
#         "Destination Longitude": 180.0000,
#     })
#     assert response.status_code == 400
#     assert response.json["Message"] == "Please input proper coordinates"

# def outside_singapore(client):
#     response = client.post("/v1/routes", data={
#         "Origin Latitude": 35.689653163130394,
#         "Origin Longitude": 139.69973343000046,
#         "Destination Latitude": 35.644475635831306,
#         "Destination Longitude": 139.784349383573,
#     })
#     assert response.status_code == 400
#     assert response.json["Message"] == "Please enter coordinates within Singapore"

# def no_drivers(client):
#     response = client.post("/v1/routes", data={
#         "Origin Latitude": 1.2462887209225797,
#         "Origin Longitude": 103.82543076084995,
#         "Destination Latitude": 1.251762343020259,
#         "Destination Longitude": 103.84801387644136,
#     })
#     assert response.status_code == 200
#     assert response.json["Message"] == "Sorry there are no available drivers for your journey at the specified time"

# def no_public_transport(client):
#     response = client.post("/v1/routes", data={
#         "Origin Latitude": 1.3359366979407206,
#         "Origin Longitude": 103.92330895306216,
#         "Destination Latitude": 1.360953236234917,
#         "Destination Longitude": 103.98966495344162,
#     })
#     assert response.status_code == 200
#     assert response.json["Message"] == "Sorry there are no available drivers for your journey at the specified time"

# def golden_route(client):
#     response = client.post("/v1/routes", data={
#         "Origin Latitude": 1.29770,
#         "Origin Longitude": 103.84912,
#         "Destination Latitude": 1.44917,
#         "Destination Longitude": 103.81990,
#     })
#     assert response.status_code == 200
#     assert response.json["Recommended Driver Routes"] is not None