from flask import Flask
from flask_cors import CORS
from flask_pymysql import MySQL

mysql = MySQL()

def create_app(config_filename):
    application = app = Flask(__name__, static_url_path='')
    application.config.from_object(config_filename)
    cors = CORS(application, resources={r"/*": {"origins": "*"}})
    
    from api_links import api_bp
    application.register_blueprint(api_bp, url_prefix='/v1')

    pymysql_connect_kwargs = {'user': 'root',
                          'password': 'Matcha8$',
                          'host': '127.0.0.1',
                          'database': 'gas_prices'}

    app.config['pymysql_kwargs'] = pymysql_connect_kwargs
    mysql = MySQL(app)

    return application

application = app = create_app("config")


@application.route('/v1', methods=['GET'])
@application.route('/', methods=['GET'])

def index():
    return 'Route Recommender API Running...'

if __name__ == "__main__":
    # application.debug = True
    application.run()