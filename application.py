from flask import Flask
from flask_cors import CORS
from flask_pymysql import MySQL

mysql = MySQL()
cogauth = CognitoAuth()

def create_app(config_filename):
    application = app = Flask(__name__, static_url_path='')
    application.config.from_object(config_filename)
    cors = CORS(application, resources={r"/*": {"origins": "*"}})
    
    from api_links import api_bp
    application.register_blueprint(api_bp, url_prefix='/v1')

    application.config["pymysql_kwargs"] = {
        'host': application.config["HOST"],
        'user': application.config["USER"],
        'password': application.config["PASSWORD"],
        'database': application.config["DATABASE"],
    }

    mysql = MySQL(app)
    cogauth = CognitoAuth(app)

    return application

application = app = create_app("config")

@application.route('/v1', methods=['GET'])
@application.route('/', methods=['GET'])

def index():
    return 'Route Recommender API Running...'

if __name__ == "__main__":
    application.run()