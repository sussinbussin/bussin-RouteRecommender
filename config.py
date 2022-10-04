import os

basedir = os.path.abspath(os.path.dirname(__file__))
# Google Maps Routes API Key
ROUTES_API_KEY = os.environ["ROUTES_API_KEY"]

# MySQL Connection Credentials
pymysql_connect_kwargs = {'user': os.environ["USER"],
                        'password': os.environ["PASSWORD"],
                        'host': os.environ["HOST"],
                        'database': os.environ["DATABASE"]}

# Deployment instructions
# https://dev.to/aws-builders/dockerize-an-api-based-flask-app-and-deploy-on-amazon-ecs-2pk0