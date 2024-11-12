from flask import Flask
import jwt
from flask_sqlalchemy import SQLAlchemy 
from flask_login import LoginManager
from dotenv import load_dotenv 
from flasgger import Swagger, swag_from
from app.database import Base, User
import os

# Required environment variables to launch
required_evars_and_descriptions = {
    'TBT_SECRET': 'Application secret- This can be anything and goes into the flask secret key',
    'TBT_DB_URI': 'The database uri- use sqlite:///filename for local',
    'TBT_BASE_URL': 'The base URL that it is being hosted on. For local this is ip:port',
    'TBT_EMAIL_ADDRESS': 'Google gmail address for emailing things',
    'TBT_EMAIL_PASSWORD': 'Google gmail password token',
}

# Load and check for all env variables we need
load_dotenv()
missing = []
for env, desc in required_evars_and_descriptions.items():
    if not os.getenv(env):
        missing.append(env)

if len(missing) != 0:
    print(f'Aborting startup... Missing the following required environment variable{"s" if len(missing) > 1 else ""}:')
    for env in missing:
        print(f'{env}: {required_evars_and_descriptions.get(env)}')
    exit()

# Create helper objects
db = SQLAlchemy(model_class=Base)
swagger = Swagger()
login_manager = LoginManager()
login_manager.login_view = 'main.sign_in_page'

# Define a login manager for the website
@login_manager.user_loader
def load_user(id):
    return db.session.query(User).filter_by(id=id).first()

# Define a request loader to check for header auth
@login_manager.request_loader
def load_user_from_request(request):
    auth_headers = request.headers.get('Authorization', '').split()
    if len(auth_headers) != 2:
        return None
    try:
        token = auth_headers[1]

        data = jwt.decode(token, os.getenv('TBT_SECRET'), algorithms='HS256')
        print('test')
        print(data)
        user_id = data['sub'].split('+')[0]
        user = db.session.query(User).filter_by(id=user_id).first()
        if user:
            return user
    except jwt.ExpiredSignatureError:
        print('expired')
        return None
    except (jwt.InvalidTokenError, Exception) as e:
        print(e)
        print('invalid')
        return None
    return None



def create_app(create_db=True):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('TBT_SECRET')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('TBT_DB_URI')
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 280}
    app.config['SWAGGER'] = {
        'title': 'TheBurnTracker Public API'
    }

    # Attach the helper objects to application
    swagger.init_app(app) 
    login_manager.init_app(app)
    db.init_app(app)

    if create_db:
        with app.app_context():
            db.create_all()

    from app.application import app as app_routes
    app.register_blueprint(app_routes)

    from app.api import api
    app.register_blueprint(api)


    return app

