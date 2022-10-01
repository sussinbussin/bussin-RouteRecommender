from flask_restful import Resource
from flask import request
# from application import mysql
from datetime import datetime
from pytz import timezone

class RoutesRecommender(Resource):

    def post(self):
        request_data = request.get_json(force=True)
        origin_lat = request_data.get("Origin Latitude")
        origin_lng = request_data.get("Origin Longitude")
        dest_lat = request_data.get("Destination Latitude")
        dest_lng = request_data.get("Destination Longitude") 
        departure_time = datetime.now(timezone("Asia/Singapore")) if request_data.get("Departure Time") is None else request_data["Departure Time"]
        priority_type = "Arrival Time" if request_data.get("Priority Type") is None else request_data["Priority Type"]

        if origin_lat is None or origin_lng is None or dest_lat is None or dest_lng is None:
            return {"Message": "Please indicate start and end coordinates"}, 400

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
        
        # TODO Check if coordinates are valid, i.e. in Singapore

        # TODO Set SQL trigger to filter routes by priority type

        # TODO Get filtered planned routes from DB
        results = []

        print(results)
        return {"Message": "Sorry there are no available drivers for your journey at the specified time"}, 404

        return {"Recommended Driver Routes": results}, 200

        



