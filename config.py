import os

basedir = os.path.abspath(os.path.dirname(__file__))
# Google Maps Routes API Key
ROUTES_API_KEY = os.environ["ROUTES_API_KEY"]

CITYMAPPER_API_KEY = os.environ["CITYMAPPER_API_KEY"]

USER = os.environ["USER"] 
PASSWORD =  os.environ["PASSWORD"]
HOST = os.environ["HOST"]
DATABASE = os.environ["DATABASE"]
COGNITO_REGION = os.environ["COGNITO_REGION"]
COGNITO_USERPOOL_ID = os.environ["COGNITO_USERPOOL_ID"]
COGNITO_APP_CLIENT_ID = os.environ["COGNITO_APP_CLIENT_ID"]

# Deployment instructions
# https://dev.to/aws-builders/dockerize-an-api-based-flask-app-and-deploy-on-amazon-ecs-2pk0

# ROUTES_API_KEY = ""

# CITYMAPPER_API_KEY = ""

# USER = 'root'
# # Please fill in your password
# PASSWORD = ''
# HOST = '127.0.0.1'
# DATABASE = 'hewwo'
# COGNITO_REGION = ""
# COGNITO_USERPOOL_ID =  ""
# COGNITO_APP_CLIENT_ID = ""
