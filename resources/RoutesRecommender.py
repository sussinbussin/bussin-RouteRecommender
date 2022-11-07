from email.mime import application
from config import ROUTES_API_KEY, CITYMAPPER_API_KEY
from flask_restful import Resource
from flask import request
from datetime import datetime, timedelta
from pytz import timezone
from geopy.geocoders import Nominatim
from application import mysql
import googlemaps
import math
import requests
from flask_cognito import cognito_auth_required

class RoutesRecommender(Resource):

    def validate_input(self, origin_lat, origin_lng, dest_lat, dest_lng):
        if origin_lat is None or origin_lng is None or dest_lat is None or dest_lng is None:
            return "Please indicate start and end coordinates"
        elif not isinstance(origin_lat, float) or not isinstance(origin_lng, float) or not isinstance(dest_lat, float) or not isinstance(dest_lng, float):
            return "Please input proper coordinates"
        elif abs(origin_lat) > 90 or abs(origin_lng) > 180 or abs(dest_lat) > 90 or abs(dest_lng) > 180:
            return "Please input proper coordinates"

        # Checking if coordinates are within Singapore
        geolocator = Nominatim(user_agent="RoutesRecommender")
        originlocation = geolocator.reverse(str(origin_lat)+","+str(origin_lng))
        destlocation = geolocator.reverse(str(dest_lat)+","+str(dest_lng))
        if originlocation.raw['address'].get('country', '') != "Singapore" or destlocation.raw['address'].get('country', '') != "Singapore":
            return "Please enter coordinates within Singapore"
        
        return "Ok"

    def find_ride_price(self, distance, gas_type):

        costs = []
        cursor = mysql.connection.cursor()
        sql_statement = '''select gas_type, max(price) from (select * from gas_price order by date_time desc limit 25) temp group by gas_type order by gas_type'''
        cursor.execute(sql_statement)
        gas_prices = cursor.fetchall()

        prices = {
            "92": gas_prices[0][1],
            "95": gas_prices[1][1],
            "98": gas_prices[2][1],
            "Diesel": gas_prices[3][1],
            "Premium": gas_prices[4][1]
        }

        average_fuel_consumption_per_litre = 15.4

        for i in range(len(distance)):
            costs.append(distance[i] / average_fuel_consumption_per_litre * float(prices[gas_type[i]]))

        return costs

    def find_public_transport_routes(self, origin_lat, origin_lng, dest_lat, dest_lng, departure_time):
        base_url = "https://api.external.citymapper.com/api/1/directions/transit"
        payload = {
            "start": str(origin_lat)+","+str(origin_lng), 
            "end":str(dest_lat)+","+str(dest_lng),
            "time": departure_time
        }
        headers = {
            "Citymapper-Partner-Key": CITYMAPPER_API_KEY
        }
        routes = requests.get(base_url, params=payload, headers=headers).json()
        
        # Check if there are any suggested public transport routes
        if routes.get("routes") is None:
            return []
        else:
            routes = routes["routes"]

        formatted_routes = []

        for route in routes:
            current_route = {
                "route": [],
                "duration": math.ceil(route["duration_seconds"] / 60),
                "cost": route["price"]["amount"]
            }
            for leg in route["legs"]:
                transport_mode = {}
                if leg["travel_mode"] == "walk":
                    transport_mode["transportMode"] = "walking"
                    # Case 1: Origin and Dest
                    if len(route["legs"]) == 1:
                        transport_mode["originLatitude"] = route["start"]["coordinates"]["lat"]
                        transport_mode["originLongitude"] = route["start"]["coordinates"]["lon"]
                        transport_mode["destLatitude"] = route["end"]["coordinates"]["lat"]
                        transport_mode["destLongitude"] = route["end"]["coordinates"]["lon"]
                    # Case 2: Origin
                    elif route["legs"].index(leg) == 0:
                        transport_mode["originLatitude"] = route["start"]["coordinates"]["lat"]
                        transport_mode["originLongitude"] = route["start"]["coordinates"]["lon"]
                        transport_mode["destLatitude"] = route["legs"][route["legs"].index(leg) + 1]["stops"][0]["coordinates"]["lat"]
                        transport_mode["destLongitude"] = route["legs"][route["legs"].index(leg) + 1]["stops"][0]["coordinates"]["lon"]
                    # Case 3: Dest
                    elif route["legs"].index(leg) == len(route["legs"]) - 1:
                        transport_mode["originLatitude"] = current_route["route"][-1]["destLatitude"]
                        transport_mode["originLongitude"] = current_route["route"][-1]["destLongitude"]
                        transport_mode["destLatitude"] = route["end"]["coordinates"]["lat"]
                        transport_mode["destLongitude"] = route["end"]["coordinates"]["lon"]
                    # Case 4: Not Origin, Not Dest
                    else:
                        transport_mode["originLatitude"] = current_route["route"][-1]["destLatitude"]
                        transport_mode["originLongitude"] = current_route["route"][-1]["destLongitude"]
                        transport_mode["destLatitude"] = route["legs"][route["legs"].index(leg) + 1]["stops"][0]["coordinates"]["lat"]
                        transport_mode["destLongitude"] = route["legs"][route["legs"].index(leg) + 1]["stops"][0]["coordinates"]["lon"]
                else:
                    if leg["vehicle_types"][0] == "metro":
                        transport_mode["transportMode"] = "mrt"
                        transport_mode["service"] = leg["services"][0]["name"]
                        transport_mode["origin"] = leg["stops"][0]["name"]
                        transport_mode["dest"] = leg["stops"][-1]["name"]
                        transport_mode["originLatitude"] = leg["stops"][0]["coordinates"]["lat"]
                        transport_mode["originLongitude"] = leg["stops"][0]["coordinates"]["lon"]
                        transport_mode["destLatitude"] = leg["stops"][-1]["coordinates"]["lat"]
                        transport_mode["destLongitude"] = leg["stops"][-1]["coordinates"]["lon"]
                    else:
                        transport_mode["transportMode"] = "bus"
                        transport_mode["service"] = leg["services"][0]["name"]
                        transport_mode["origin"] = leg["stops"][0]["name"]
                        transport_mode["dest"] = leg["stops"][-1]["name"]
                        transport_mode["originLatitude"] = leg["stops"][0]["coordinates"]["lat"]
                        transport_mode["originLongitude"] = leg["stops"][0]["coordinates"]["lon"]
                        transport_mode["destLatitude"] = leg["stops"][-1]["coordinates"]["lat"]
                        transport_mode["destLongitude"] = leg["stops"][-1]["coordinates"]["lon"]

                current_route["route"].append(transport_mode)
            formatted_routes.append(current_route)
        return formatted_routes

    @cognito_auth_required
    def post(self):

        # Input Validation
        request_data = request.get_json(force=True)
        origin_lat = request_data.get("Origin Latitude")
        origin_lng = request_data.get("Origin Longitude")
        dest_lat = request_data.get("Destination Latitude")
        dest_lng = request_data.get("Destination Longitude") 
        departure_time = datetime.now(tz=timezone("Asia/Singapore")) if request_data.get("Departure Time") is None else datetime.strptime(request_data["Departure Time"] + " +0800", '%Y-%m-%d %H:%M:%S %z')
        #departure_time = datetime.date.today().strftime('%Y-%d-%m') if request_data.get("Departure Time") is None else request_data["Departure Time"]
        priority_type = "Arrival Time" if request_data.get("Priority Type") is None else request_data["Priority Type"]

        if self.validate_input(origin_lat, origin_lng, dest_lat, dest_lng) != "Ok":
            return {"message": self.validate_input(origin_lat, origin_lng, dest_lat, dest_lng)}, 400

        # Get filtered planned routes from DB
        # Filter conditions:
        # - Maximum of 15 minute minute delay between passenger journey start and driver drive start
        # - Maximum of 10 minute walking time from passenger start to driver start, i.e. 750m, 4.5km/h walking speed

        # Approximate error between Pythagoras and Havers
        # https://gis.stackexchange.com/questions/58653/what-is-approximate-error-of-pythagorean-theorem-vs-haversine-formula-in-measur

        #datetime_plus15 = datetime.datetime.strptime(departure_time.replace("-", "/"), '%Y/%d/%m').date() + datetime.timedelta(minutes=15)
        datetime_plus15 = departure_time + timedelta(minutes=15)

        cursor = mysql.connection.cursor()

        sql_statement = '''SELECT temp2.*, bussinuser.name FROM (SELECT temp.*, driver.fuel_type, driver.model_and_colour, driver.user_id as driver_id FROM (SELECT * FROM planned_route WHERE
                            SQRT(POW((origin_latitude-%s),2) + POW((origin_longitude-%s),2)) <= 0.066569613598277
                            ORDER BY (SQRT(POW((origin_latitude-%s),2) + POW((origin_longitude-%s),2)) 
                            + SQRT(POW((dest_latitude-%s),2) + POW((dest_longitude-%s),2))) LIMIT 5) temp 
                            JOIN driver ON temp.car_plate = driver.car_plate) temp2
                            JOIN bussinuser ON temp2.driver_id = bussinuser.id'''
        # sql_statement = '''SELECT * FROM planned_route WHERE dateTime BETWEEN %s AND %s AND
        #                     SQRT(POW((originLatitude-%s),2) + POW((originLongitude-%s),2)) <= 0.066569613598277
        #                     ORDER BY (SQRT(POW((originLatitude-%s),2) + POW((originLongitude-%s),2)) 
        #                     + SQRT(POW((destLatitude-%s),2) + POW((destLongitude-%s),2))) LIMIT 5'''
        # cursor.execute(sql_statement, (str(departure_time).split(".")[0], str(datetime_plus15.strftime('%Y/%m/%d %H:%M:%S')).split(".")[0], origin_lat, origin_lng, origin_lat, origin_lng, dest_lat, dest_lng))

        cursor.execute(sql_statement, (origin_lat, origin_lng, origin_lat, origin_lng, dest_lat, dest_lng))
        routes = cursor.fetchall()

        results = []
        if len(routes) != 0:
            gmaps = googlemaps.Client(key=ROUTES_API_KEY)
        # Call Routes API to get actual arrival time (departure + travel time) and rank based on that
        # Calls:
        # - Driving (B to C)
        # - Walking (C to D)
        
        # if using directions, takes 2.86s
        # dm_result = []
        # for route in routes:
        #     dm_result.append(gmaps.directions(origin=(route[1], route[2]), destination=(route[3], route[4]), departure_time=departure_time))

        # using distance_matrix returns a matrix of distances; will have to take the diagonal elements
            origins = []
            destinations = []
            for route in routes:
                origins.append((route[8], route[9]))
                destinations.append((route[6], route[7]))
            dm_result = gmaps.distance_matrix(origins=origins, destinations=destinations, departure_time=departure_time)["rows"]

            timed_result = []
            for i in range(len(dm_result)):
                timed_result.append(dm_result[i]["elements"][i])

        # Rank routes based on Arrival Time

            travel_time = list(map(lambda x: int(timed_result[routes.index(x)]["duration"]["text"].replace(" mins", "")) + math.ceil(1482.59902 * math.sqrt((float(x[6]) - dest_lat) ** 2 + (float(x[7]) - dest_lng) ** 2)), routes))
            distance = travel_time = list(map(lambda x: float(timed_result[routes.index(x)]["distance"]["text"].replace(" km", "")), routes))
            cost = self.find_ride_price(distance, [routes[i][10] for i in range(len(routes))])

            for i in range(len(routes)):
                results.append({
                    'id': routes[i][0],
                    'originLatitude': float(routes[i][8]),
                    'originLongitude': float(routes[i][9]),
                    'destLatitude': float(routes[i][6]),
                    'destLongitude': float(routes[i][7]),
                    'dateTime': str(routes[i][2]),
                    'capacity': routes[i][1],
                    'carPlate': routes[i][5],
                    'carModel': routes[i][11],
                    'driver': routes[i][13],
                    'duration': travel_time[i],
                    'cost': cost[i]
                })
    
            results.sort(key=lambda x: x["duration"])

        # Adding public transport options
        public_transport_routes = self.find_public_transport_routes(origin_lat, origin_lng, dest_lat, dest_lng, departure_time)
        if len(results) == 0:
            results = public_transport_routes
        else:
            results.extend(public_transport_routes)

        if len(results) == 0:
            return {"message": "Sorry there are no available drivers or public transport for your journey at the specified time"}, 200
        else:
            return {"Recommended Driver Routes": results}, 200