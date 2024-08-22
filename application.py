from flask import Flask, abort, request, render_template, make_response, redirect, url_for, flash, Blueprint 
from flask_login import login_user, login_required, logout_user, current_user, LoginManager
from database import db, User, Burn
from datetime import datetime, date
from dotenv import load_dotenv
from flask_restful import Resource, Api
from flasgger import Swagger, swag_from
import json
import csv
import os
import io

# Load and check for all env variables we need
load_dotenv()
print(os.getenv('TBT_DB_URI'))
if not os.getenv('TBT_DB_URI'):
    raise RuntimeError('Missing environment variable: TBT_DB_URI')

# Configure the flask application object
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('TBT_DB_URI')
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 280}

# Initialize the swagger interface
app.config['SWAGGER'] = {
    'title': 'TheBurnTracker Public API'
}
swagger = Swagger(app)

# Initialize the database
db.init_app(app)
with app.app_context():
    db.create_all()

# Define a login manager for the website
login_manager = LoginManager()
login_manager.login_view = 'sign_in_page'
login_manager.init_app(app)
@login_manager.user_loader
def load_user(id):
    return db.session.query(User).filter_by(id=id).first()

# For now, no homepage so redirect to sign in
@app.route('/')
def home_page():
    return redirect(url_for('sign_in_page'))

@app.route('/sign-in.html', methods=['GET', 'POST'])
def sign_in_page():
    if request.method == 'POST':
    
        # Collect the data from the form
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')

        # Try and find the user
        user = db.session.query(User).filter_by(email=email).first()

        # Validate the user
        if not user or not user.check_pass(password):
            flash('Incorrect password, try again', category='error')

        else:
            # log the user in and update their last login time
            login_user(user)
            user.last_login = datetime.now().astimezone()
            db.session.commit()

            # Send them to their spinner page
            return redirect(url_for('spinner_page', spinner_username=user.username))

    return render_template('auth/sign_in.html', request=request)

@app.route('/sign-up.html', methods=['GET', 'POST'])
def sign_up_page():
    if request.method == 'POST':
        # Collect data from the input fields
        username = request.form.get('username').strip().lower()
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')

        # Check for registration issues
        if db.session.query(User).filter_by(username=username).first():
            print("ERROR: Tried to create user with existing username.")
        if db.session.query(User).filter_by(email=email).first():
            print("ERROR: Tried to create user with existing email.")
        if password != password_confirm:
            print("ERROR: Tried to create account with mismatched password and password_confirm")

        # Create a user and add to database
        user = User(username=username, email=email, password=User.hash_pass(password))
        db.session.add(user)
        db.session.commit()

        # Log in the user
        login_user(user)

        if request.args.get('next'):
            return redirect(request.args.get('next'))
        return redirect(url_for('spinner_page', spinner_username=username))

    return render_template('auth/sign_up.html')


@app.route('/sign-out.html')
def sign_out_page():
    logout_user()
    return redirect(url_for('home_page'))

@app.route('/spinner/<spinner_username>.html', methods=['GET', 'POST'])
@login_required
def spinner_page(spinner_username: str):

    spinner = db.session.query(User).filter_by(username=spinner_username).first()

    if request.method == 'POST':

        if spinner_username != current_user.username:
            return redirect(url_for('spinner_page', spinner_username=spinner_username))
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename.endswith('.csv'):
                file_content = file.stream.read().decode('utf-8')
                reader = csv.reader(io.StringIO(file_content))
                for location, time, prop, notes in reader:
                    db.session.add(Burn(
                        user_id=spinner.id,
                        location=location,
                        time=date.fromisoformat(time),
                        prop=prop,
                        notes=notes
                    ))
                    db.session.commit()

            return redirect(url_for('spinner_page', spinner_username=spinner_username))

        # Collect the data from the form
        location = request.form.get('location')
        burn_date = request.form.get('date_today').split('-')
        prop = request.form.get('prop')
        notes = request.form.get('notes')
   
        # Create the burn object
        db.session.add(Burn(user_id=spinner.id, location=location, prop=prop, notes=notes, time=date(int(burn_date[0]), int(burn_date[1]), int(burn_date[2]))))
        db.session.commit() 
        return redirect(url_for('spinner_page', spinner_username=spinner.username))

    burns = db.session.query(Burn).filter_by(user_id=spinner.id).all()
    return render_template('spinner.html', 
                           spinner=spinner,
                           last_location='' if len(spinner.burns) <= 0 else spinner.burns[-1].location,
                           date_today=datetime.now().strftime('%Y-%m-%d'),
                           current_user=current_user,
                           )
@app.route('/burn/<burn_id>/edit.html')
@login_required
def edit_burn_page(burn_id: int):


    burn = db.session.query(Burn).filter_by(id=burn_id).first()

    if not burn:
        abort(404)

    return render_template('edit_burn.html', burn=burn)

@app.route('/spinner/<spinner_username>/statistics.html')
@login_required
def spinner_stats_page(spinner_username):

    spinner = db.session.query(User).filter_by(username=spinner_username).first()
 
    props = {}
    total_burns = 0
    for burn in spinner.burns:
        total_burns += 1

        if burn.prop not in props:
            props[burn.prop] = 0
        props[burn.prop] += 1

    unique_props, prop_counts = zip(*props.items())        
    unique_props = str(unique_props).replace('(', '[').replace(')', ']').replace('\'', '"')
    prop_counts = str(prop_counts).replace('(', '[').replace(')', ']')
    return render_template('spinner_stats.html', 
                           total_burns=total_burns,
                           unique_props=unique_props,
                           prop_counts=prop_counts)

@app.route('/burns/<burn_id>.html', methods=['DELETE'])
@login_required
def burn_pages(burn_id):

    burn = db.session.query(Burn).filter_by(id=burn_id).first()

    if request.method=='DELETE':
        if current_user.id != burn.user_id:
            return '404'
        else:
            db.session.query(Burn).filter_by(id=burn.id).delete()
            db.session.commit()

@app.route('/api/v1/burn/<burn_id>.json', methods=['GET', 'POST', 'PATCH', 'DELETE'])
def burn_api(burn_id):

    burn = db.session.query(Burn).filter_by(id=burn_id).first()
    if not burn:
        abort(404)

    if request.method=='DELETE':
        pass

    if request.method == 'PATCH':
        body = request.get_json()
        for field in body.keys():
            setattr(burn, field, body[field])

    
    db.session.commit()
    return 'oops'

@app.route('/api/v1/spinner/<spinner_username>/burns.csv')
@login_required
def spinner_burns_csv(spinner_username):
    
    spinner = db.session.query(User).filter_by(username=spinner_username).first()

    # If the spinner can't be found throw a 404 or is not the logged in user
    if not spinner or spinner.username != current_user.username:
        abort(404) 

    # Write the header and then a line for each burn
    csv_data = 'Location,Date,Prop,Notes\n'
    for burn in spinner.burns:
        csv_data += f'{burn.location},{burn.time},{burn.prop},{burn.notes}\n'

    # Convert the data to a file-like object, set headers and return response
    csv_file = io.BytesIO(csv_data.encode())
    output = make_response(csv_file)
    output.headers['Content-Disposition'] = f'attachment; filename={spinner.username}_burns_{date.today()}.csv'
    output.headers['Content-type'] = 'text/csv'
    return output

@app.route('/api/v1/spinner/<spinner_username>/burns.json')
@login_required
def spinner_burns_json(spinner_username):

    spinner = db.session.query(User).filter_by(username=spinner_username).first()

    if not spinner or spinner.username != current_user.username:
        abort(404)

    burns_dict = {}
    for burn in spinner.burns:
        if burn.location not in burns_dict:
            burns_dict[burn.location] = {}
            
        if str(burn.time) not in burns_dict[burn.location]:
            burns_dict[burn.location][str(burn.time)] = []

        instance = {'prop': burn.prop}
        if burn.notes:
            instance['notes'] = burn.notes

        burns_dict[burn.location][str(burn.time)].append(instance)

    output = make_response(io.BytesIO(json.dumps(burns_dict, indent=4).encode()))
    output.headers['Content-Disposition'] = f'attachment; filename={spinner.username}_burns_{date.today()}.csv'
    output.headers['Content-type'] = 'text/json'
    return output
        

api = Api(app)

specs_dict = {
  "tags": ['Burn'],
  "parameters": [
    {
      "name": "burn_id",
      "in": "path",
      "type": "int",
      "required": "true",
      "description": 'The database ID number for the burn.',
    }
  ],
  "definitions": {
    "Burn": {
      "type": "object",
      "properties": {
        "id": {
          "type": "integer",
        },
        "time": {
            'type': 'string'
        },
        "location": {
            'type': 'string'
        },
        "prop": {
            'type': 'string'
        },
        "notes": {
                    "type": "string"
                }
      }
    },
  },
  "responses": {
    "200": {
      "description": "Information about the Burn.",
      "schema": {
        "$ref": "#/definitions/Burn"
      },
      "examples": {
        "rgb": [
          "red",
          "green",
          "blue"
        ]
      }
    },
    "404": {
        "description": "Burn not found in database.",
        "schema": {
                "name": "thing",
                "type": "string",
            }
    }
  }
}

class UserResource(Resource):
    def get(self, user_id: int):
        """
          Allows access to user information.
          Returns a representation of user.
          ---
        tags:
          - User Resources
        parameters:
          - in: path
            name: user_id
            type: integer
            required: true
        responses:
          200:
            description: A single user item
            schema:
              id: User
              properties:
                id:
                  type: integer
                  description: The database ID of the user
                  default: 1
                username:
                  type: string
                  description: The display name of the user
                  default: John Doe
                email:
                  type: string
                  description: The email the user has signed up under
                  default: jDoe@gmail.com
                created_on:
                  type: string
                  description: The date the user signed up
                  default: "10/10/1000"
                last_login:
                  type: string
                  description: The last date the user logged in
                  default: "10/20/2000"
          404:
            description: Could not find user with this id
        """
        users = db.session.query(User).filter_by(id=user_id).all()

        if len(users) == 0:
            abort(404)

        user = users[0]

        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'created_on': str(user.created_on),
            'last_login': str(user.last_login)
        }



api.add_resource(UserResource, '/api/v2/user/<int:user_id>.json') 

class BurnResource(Resource):
    def get(self, burn_id: int):
        """
          Allows access to a user's burn information.
          Returns a representation of a burn.
          ---
        tags:
          - Burn Resources
        parameters:
          - in: path
            name: burn_id
            type: integer
            required: true
        responses:
          200:
            description: A single burn instance
            schema:
              id: Burn
              properties:
                id:
                  type: integer
                  description: The database ID of the burn
                  default: 1
                location:
                  type: string
                  description: The location the burn took place
                  default: Albany Spinjam <3
                time:
                  type: string
                  description: The date the burn occured
                  default: 2024-08-22
                prop:
                  type: string
                  description: The prop used
                  default: "10/10/1000"
                notes:
                  type: string
                  description: The last date the user logged in
                  default: "10/20/2000"
          404:
            description: Could not find user with this id
        """
        burns = db.session.query(Burn).filter_by(id=burn_id).all()

        if len(burns) != 1:
            abort(404)

        burn = burns[0]

        return {
            'location': burn.location,
            'date': str(burn.time),
            'prop': burn.prop,
            'notes': burn.notes
        }

    def patch(self, burn_id: int):
        """
          Patch a specific burn 
          This endpoint allows you to edit burns (modify in place)
          ---
        tags:
          - Burn Resources
        parameters:
          - in: path
            name: burn_id
            type: integer
            required: true
        responses:
          200:
            description: The patched burn information
            schema:
              id: Burn
              properties:
                id:
                  type: integer
                  description: The database ID of the burn
                  default: 1
                location:
                  type: string
                  description: The location the burn took place
                  default: Albany Spinjam <3
                time:
                  type: string
                  description: The date the burn occured
                  default: 2024-08-22
                prop:
                  type: string
                  description: The prop used
                  default: "10/10/1000"
                notes:
                  type: string
                  description: The last date the user logged in
                  default: "10/20/2000"
          404:
            description: Could not find user with this id
        """
        pass
        

    def delete(self, burn_id: int):
        """
          Delete a burn.
          Allows you to remove burns from the database. This is permanant and CANNOT be undone without rolling back the database.
          ---
        tags:
          - Burn Resources
        parameters:
          - in: path
            name: burn_id
            type: integer
            required: true
        responses:
          200:
            description: The deleted burn instance
            schema:
              id: Burn
              properties:
                id:
                  type: integer
                  description: The database ID of the burn
                  default: 1
                location:
                  type: string
                  description: The location the burn took place
                  default: Albany Spinjam <3
                time:
                  type: string
                  description: The date the burn occured
                  default: 2024-08-22
                prop:
                  type: string
                  description: The prop used
                  default: "10/10/1000"
                notes:
                  type: string
                  description: The last date the user logged in
                  default: "10/20/2000"
          404:
            description: Could not find user with this id
        """
        pass

class UnidentifiedBurnResource(Resource):
    def post(self):
        """
          Allows you to create new burn instances.
          Create a new burn.
          ---
        tags:
          - Burn Resources
        parameters:
          - in: body
            name: location
            type: string
            required: true
            example: Albany Spinjam <3 
          - in: body
            name: prop
            type: string
            required: true
            example: 4 Poi
          - in: body
            name: time
            type: string
            required: true
            example: 2024-01-15
          - in: body
            name: notes 
            type: string
            required: false
            example: "Spun with friends"
        responses:
          200:
            description: A single burn instance
            schema:
              id: Burn
              properties:
                id:
                  type: integer
                  description: The database ID of the burn
                  default: 1
                location:
                  type: string
                  description: The location the burn took place
                  default: Albany Spinjam <3
                time:
                  type: string
                  description: The date the burn occured
                  default: 2024-08-22
                prop:
                  type: string
                  description: The prop used
                  default: "10/10/1000"
                notes:
                  type: string
                  description: The last date the user logged in
                  default: "10/20/2000"
          404:
            description: Could not find user with this id
        """
    


api.add_resource(UnidentifiedBurnResource, '/api/v2/burn.json') 
api.add_resource(BurnResource, '/api/v2/burn/<int:burn_id>.json') 


