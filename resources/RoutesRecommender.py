from email.mime import application
from flask_restful import Resource
from flask import request
# from datetime import datetime
import datetime
from pytz import timezone
from geopy.geocoders import Nominatim
from application import mysql
import json

class RoutesRecommender(Resource):

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

        if origin_lat is None or origin_lng is None or dest_lat is None or dest_lng is None:
            return {"Message": "Please indicate start and end coordinates"}, 400
        elif not isinstance(origin_lat, float) or not isinstance(origin_lng, float) or not isinstance(dest_lat, float) or not isinstance(dest_lng, float):
            return {"Message": "Please input proper coordinates"}, 400
        elif abs(origin_lat) > 90 or abs(origin_lng) > 180 or abs(dest_lat) > 90 or abs(dest_lng) > 180:
            return {"Message": "Please input proper coordinates"}, 400

        # Checking if coordinates are within Singapore
        geolocator = Nominatim(user_agent="RoutesRecommender")
        originlocation = geolocator.reverse(str(origin_lat)+","+str(origin_lng))
        destlocation = geolocator.reverse(str(dest_lat)+","+str(dest_lng))
        if originlocation.raw['address'].get('country', '') != "Singapore" or destlocation.raw['address'].get('country', '') != "Singapore":
            return {"Message": "Please enter coordinates within Singapore"}, 400

        # Get filtered planned routes from DB
        # Filter conditions:
        # - Maximum of 15 minute minute delay between passenger journey start and driver drive start
        # - Maximum of 10 minute walking time from passenger start to driver start, i.e. 750m, 4.5km/h walking speed

        # Approximate error between Pythagoras and Havers
        # https://gis.stackexchange.com/questions/58653/what-is-approximate-error-of-pythagorean-theorem-vs-haversine-formula-in-measur

        #datetime_plus15 = datetime.datetime.strptime(departure_time.replace("-", "/"), '%Y/%d/%m').date() + datetime.timedelta(minutes=15)
        datetime_plus15 = departure_time + datetime.timedelta(minutes=15)

        cursor = mysql.connection.cursor()
        sql_statement = '''SELECT * FROM plannedRoute WHERE dateTime BETWEEN %s AND %s AND
                            SQRT(POW((originLatitude-%s),2) + POW((originLongitude-%s),2)) <= 0.066569613598277
                            ORDER BY (SQRT(POW((originLatitude-%s),2) + POW((originLongitude-%s),2)) 
                            + SQRT(POW((destLatitude-%s),2) + POW((destLongitude-%s),2))) LIMIT 5'''
        cursor.execute(sql_statement, (str(departure_time).split(".")[0], str(datetime_plus15.strftime('%Y/%m/%d %H:%M:%S')).split(".")[0], origin_lat, origin_lng, origin_lat, origin_lng, dest_lat, dest_lng))
        routes = cursor.fetchall()

        # TODO Call Routes API to get actual arrival time (departure + travel time) and rank based on that
        # Calls:
        # - Driving (B to C)
        # - Walking (C to D)

        # routes_request = {
        #     "origin":{
        #         "location":{
        #             "latLng":{
        #                 "latitude": origin_lat,
        #                 "longitude": origin_lng
        #             }
        #         }
        #     },
        #     "destination":{
        #         "location":{
        #             "latLng":{
        #                 "latitude": dest_lat,
        #                 "longitude": dest_lng
        #             }
        #         }
        #     },
        # }

        # TODO Rank routes based on Arrival Time

        results = []
        for route in routes:
            results.append({
                'id': route[0],
                'originLatitude': float(route[1]),
                'originLongitude': float(route[2]),
                'destLatitude': float(route[3]),
                'destLongitude': float(route[4]),
                'dateTime': str(route[5]),
                'capacity': route[6],
                'carPlate': route[7]
            })

        result = json.dumps(results, indent=2)

        if len(results) == 0:
            return {"Message": "Sorry there are no available drivers for your journey at the specified time"}, 404
        else:
            return {"Recommended Driver Routes": results}, 200

        



