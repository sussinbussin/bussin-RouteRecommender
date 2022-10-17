from config import ROUTES_API_KEY
from flask_restful import Resource
from flask import request
# from datetime import datetime
import datetime
from pytz import timezone
from geopy.geocoders import Nominatim
from application import mysql
import googlemaps
import math

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

        {
            "92": gas_prices[0][1],
            "95": gas_prices[1][1],
            "98": gas_prices[2][1],
            "Diesel": gas_prices[3][1],
            "Premium": gas_prices[4][1]
        }

        average_fuel_consumption_per_litre = 15.4

        for i in range(len(distance)):
            costs.append(distance[i] / average_fuel_consumption_per_litre * gas_prices[gas_type[i]])

        return costs

    def post(self):

        # Input Validation
        request_data = request.get_json(force=True)
        origin_lat = request_data.get("Origin Latitude")
        origin_lng = request_data.get("Origin Longitude")
        dest_lat = request_data.get("Destination Latitude")
        dest_lng = request_data.get("Destination Longitude") 
        departure_time = datetime.datetime.now(timezone("Asia/Singapore")) if request_data.get("Departure Time") is None else datetime.datetime.strptime(request_data["Departure Time"], '%Y/%m/%d %H:%M:%S')
        #departure_time = datetime.date.today().strftime('%Y-%d-%m') if request_data.get("Departure Time") is None else request_data["Departure Time"]
        priority_type = "Arrival Time" if request_data.get("Priority Type") is None else request_data["Priority Type"]

        print([origin_lat, origin_lng, dest_lat, dest_lng])

        if self.validate_input(origin_lat, origin_lng, dest_lat, dest_lng) != "Ok":
            return {"Message": self.validate_input(origin_lat, origin_lng, dest_lat, dest_lng)}, 400

        # Get filtered planned routes from DB
        # Filter conditions:
        # - Maximum of 15 minute minute delay between passenger journey start and driver drive start
        # - Maximum of 10 minute walking time from passenger start to driver start, i.e. 750m, 4.5km/h walking speed

        # Approximate error between Pythagoras and Havers
        # https://gis.stackexchange.com/questions/58653/what-is-approximate-error-of-pythagorean-theorem-vs-haversine-formula-in-measur

        #datetime_plus15 = datetime.datetime.strptime(departure_time.replace("-", "/"), '%Y/%d/%m').date() + datetime.timedelta(minutes=15)
        datetime_plus15 = departure_time + datetime.timedelta(minutes=15)

        cursor = mysql.connection.cursor()

        sql_statement = '''SELECT temp2.*, bussinuser.name FROM (SELECT temp.*, driver.fuel_type, driver.model_and_color, driver.id as driver_id FROM (SELECT * FROM planned_route WHERE
                            SQRT(POW((originLatitude-%s),2) + POW((originLongitude-%s),2)) <= 0.066569613598277
                            ORDER BY (SQRT(POW((originLatitude-%s),2) + POW((originLongitude-%s),2)) 
                            + SQRT(POW((destLatitude-%s),2) + POW((destLongitude-%s),2))) LIMIT 5) temp 
                            JOIN driver ON temp.car_plate = driver.car_plate) temp2
                            JOIN bussinuser ON temp2.driver_id = bussinuser.id'''
        # sql_statement = '''SELECT * FROM planned_route WHERE dateTime BETWEEN %s AND %s AND
        #                     SQRT(POW((originLatitude-%s),2) + POW((originLongitude-%s),2)) <= 0.066569613598277
        #                     ORDER BY (SQRT(POW((originLatitude-%s),2) + POW((originLongitude-%s),2)) 
        #                     + SQRT(POW((destLatitude-%s),2) + POW((destLongitude-%s),2))) LIMIT 5'''
        # cursor.execute(sql_statement, (str(departure_time).split(".")[0], str(datetime_plus15.strftime('%Y/%m/%d %H:%M:%S')).split(".")[0], origin_lat, origin_lng, origin_lat, origin_lng, dest_lat, dest_lng))

        cursor.execute(sql_statement, (origin_lat, origin_lng, origin_lat, origin_lng, dest_lat, dest_lng))
        routes = cursor.fetchall()

        # Call Routes API to get actual arrival time (departure + travel time) and rank based on that
        # Calls:
        # - Driving (B to C)
        # - Walking (C to D)

        gmaps = googlemaps.Client(key=ROUTES_API_KEY)
        
        # if using directions, takes 2.86s
        # dm_result = []
        # for route in routes:
        #     dm_result.append(gmaps.directions(origin=(route[1], route[2]), destination=(route[3], route[4]), departure_time=departure_time))

        # using distance_matrix returns a matrix of distances; will have to take the diagonal elements
        origins = []
        destinations = []
        for route in routes:
            origins.append((route[1], route[2]))
            destinations.append((route[3], route[4]))
        dm_result = gmaps.distance_matrix(origins=origins, destinations=destinations, departure_time=departure_time)["rows"]

        timed_result = []
        for i in range(len(dm_result)):
            timed_result.append(dm_result[i]["elements"][i])

        # Rank routes based on Arrival Time

        travel_time = list(map(lambda x: int(timed_result[routes.index(x)]["duration"]["text"].replace(" mins", "")) + math.ceil(1482.59902 * math.sqrt((float(x[3]) - dest_lat) ** 2 + (float(x[4]) - dest_lng) ** 2)), routes))
        distance = travel_time = list(map(lambda x: float(timed_result[routes.index(x)]["distance"]["text"].replace(" km", "")), routes))
        cost = self.find_ride_price(distance, [routes[i][8] for i in range(len(routes))])

        results = []
        for i in range(len(routes)):
            results.append({
                'id': routes[i][0],
                'originLatitude': float(routes[i][1]),
                'originLongitude': float(routes[i][2]),
                'destLatitude': float(routes[i][3]),
                'destLongitude': float(routes[i][4]),
                'dateTime': str(routes[i][5]),
                'capacity': routes[i][6],
                'carPlate': routes[i][7],
                'carModel': routes[i][9],
                'driver': routes[i][13],
                'duration': travel_time[i],
                'cost': cost[i]
            })
    
        results.sort(key=lambda x: x["duration"])

        if len(results) == 0:
            return {"Message": "Sorry there are no available drivers for your journey at the specified time"}, 200
        else:
            return {"Recommended Driver Routes": results}, 200

        



