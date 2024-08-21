from flask import Flask, abort, request, render_template, make_response, redirect, url_for, flash, Blueprint 
from flask_login import login_user, login_required, logout_user, current_user, LoginManager
from database import db, User, Burn
from datetime import datetime, date
from dotenv import load_dotenv
from flasgger import Swagger
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
        

@app.route('/api/v1/burn/<burn_id>.json', methods=['PATCH', 'DELETE'])
def burn_api(burn_id):
    """Example endpoint returning a list of colors by palette
    This is using docstrings for specifications.
    ---
    parameters:
      - name: palette
        in: path
        type: string
        enum: ['all', 'rgb', 'cmyk']
        required: true
        default: all
    definitions:
      Palette:
        type: object
        properties:
          palette_name:
            type: array
            items:
              $ref: '#/definitions/Color'
      Color:
        type: string
    responses:
      200:
        description: A list of colors (may be filtered by palette)
        schema:
          $ref: '#/definitions/Palette'
        examples:
          rgb: ['red', 'green', 'blue']
    """ 

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
        
