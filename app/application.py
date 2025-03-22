import csv
import io
import json
import os
import random
import smtplib
import string
from collections import Counter
from datetime import date, datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import git
from dotenv import load_dotenv
from flasgger import Swagger, swag_from
from flask import (Blueprint, Flask, abort, flash, make_response, redirect,
                   render_template, request, url_for)
from flask_login import (LoginManager, current_user, login_required,
                         login_user, logout_user)
from flask_restful import Api, Resource
from sqlalchemy import asc, desc, func

from app import db
from app.communications import Email
from app.database import Burn, PasswordReset, User

app = Blueprint('main', __name__)

#-#-#-#-#-#-#-#-#-#- Middleware and request modifications -#-#-#-#-#-#-#-#-#-#

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_activity = datetime.utcnow()
        db.session.commit()

#-#-#-#-#-#-#-#-#-#- Application routes -#-#-#-#-#-#-#-#-#-#

# For now, no homepage so redirect to sign in
@app.route('/')
def home_page():
    if current_user.is_authenticated:
        return redirect(url_for('main.spinner_logger_page'))
    return redirect(url_for('main.sign_in_page'))

@app.route('/sign-in.html', methods=['GET', 'POST'])
def sign_in_page():
    if request.method == 'POST':
    
        # Collect the data from the form
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')

        # Try and find the user
        user = db.session.query(User).filter_by(email=email).first()
        
        # Get the remember me setting
        remember_me = True if request.form.get('rememberMe') == 'on' else False

        # Validate the user
        if not user or not user.check_pass(password):
            flash('Incorrect password, try again', category='error')
            return render_template('auth/sign_in.html', request=request), 401

        else:
            # log the user in and update their last login time
            login_user(user, remember=remember_me)
            user.last_login = datetime.now().astimezone()
            db.session.commit()

            # Send them to their spinner page
            return redirect(url_for('main.spinner_logger_page'))

    return render_template('auth/sign_in.html', request=request)


@app.route('/sign-up.html', methods=['GET', 'POST'])
def sign_up_page():
    if request.method == 'POST':
        # Collect data from the input fields
        username = request.form.get('username').strip()
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')

        # Check for registration issues
        if db.session.query(User).filter(User.username.ilike(username)).first():
            flash('Error: Tried to create user with existing username', category='error')
            return render_template('auth/sign_up.html'), 403
        if db.session.query(User).filter_by(email=email).first():
            flash('Error: Email already in use, please use a different email or use "Forgot Password"', category='error')
            return render_template('auth/sign_up.html'), 403
        if password != password_confirm:
            flash('Error: Password confirmation field does not match password')
            return render_template('auth/sign_up.html'), 403

        # Create a user and add to database
        user = User(username=username, email=email, password=User.hash_pass(password))
        db.session.add(user)
        db.session.commit()

        # Log in the user
        login_user(user)

        if request.args.get('next'):
            return redirect(request.args.get('next'))
        return redirect(url_for('main.spinner_logger_page'))

    return render_template('auth/sign_up.html')



@app.route('/logger.html', methods=['GET', 'POST'])
@login_required
def spinner_logger_page():

    prop_counter = Counter()
    burns = db.session.query(Burn).filter_by(user_id=current_user.id).order_by(Burn.time.asc()).all()
    for burn in burns: 
        prop_counter[burn.prop] += 1

    prop_counter = prop_counter.most_common(6)
    quick_props = [prop for prop, count in prop_counter]


    if request.method == 'POST':

        # Get the location and abort with 400 if it's empty or just whitespace
        burn_location = request.form.get('burn_location').strip()
        if burn_location == '':
            flash('Invalid Location: Please enter a location', category='error')
            return render_template('spinner/logger.html'), 400

        # Get the date and abort with 400 if it's a future date
        burn_date = datetime.strptime(request.form.get('burn_date'), "%Y-%m-%d").date()
        if burn_date > date.today():
            flash('Invalid Date: Please enter a date that is today or in the past', category='error')
            return render_template('spinner/logger.html'), 400
    
        # Get the prop and abort with 400 if it's empty or whitespace
        burn_prop = request.form.get('burn_prop').strip()
        if burn_prop == '':
            flash('Invalid Prop: Please enter a prop', category='error')
            return render_template('spinner/logger.html'), 400

        # Otherwise, we are good to go ahead and create the burn objects
        db.session.add(Burn(
            user_id=current_user.id, 
            location=burn_location,
            prop=burn_prop, 
            notes=request.form.get('burn_notes'), 
            time=burn_date))
        db.session.commit()
        flash('Burn Logged', category='success')

    return render_template('spinner/logger.html', quick_props=quick_props, burns=burns)

@app.route('/records.html')
@login_required
def spinner_record_page():
    return render_template('spinner/records.html')


@app.route('/statistics.html', methods=['GET'])
@login_required
def spinner_statistics_page():
    if not current_user.burns:
        return 'no burns'

    top_prop = db.session.query(
        Burn.prop,
        func.count(Burn.prop).label('count')
    ).filter(Burn.user_id == current_user.id
    ).group_by(Burn.prop
    ).order_by(func.count(Burn.prop).desc()
    ).first()[0]

    location_counts = db.session.query(
        Burn.location,
        func.count(Burn.location).label('count')
    ).filter(Burn.user_id == current_user.id).group_by(Burn.location).all()
    print(location_counts)

    total_burns = db.session.query(Burn).filter(Burn.user_id == current_user.id).count()

    newest_burn = db.session.query(Burn).filter(Burn.user_id == current_user.id).order_by(Burn.time.desc()).first().time.strftime("%b %d, %Y")

    unique_locations = [str(data[0]) for data in db.session.query(Burn.location.distinct().label('location')).filter(Burn.user_id==current_user.id).all()]


    locations = []

    return render_template('spinner/statistics.html',
                           oldest_date=db.session.query(Burn).order_by(Burn.time.asc()).first().time.strftime('%Y-%m-%d'),
                           today_date=datetime.today().strftime('%Y-%m-%d'),
                           top_prop=top_prop,
                           total_burns=total_burns,
                           newest_burn=newest_burn,
                           unique_locations=unique_locations,
                           burns=[burn.as_dict() for burn in current_user.burns],
                           last_burn=current_user.burns[-1]
                           )

@app.route('/import-data.html', methods=['GET', 'POST'])
@login_required
def import_data_page():

    if request.method == 'POST':
        # Guard against bad posts
        if not request.get_json() or 'importedData' not in request.get_json():
            return 'errorrrr'

        burns = []
        for burn in request.get_json().get('importedData', []):
            # Skip rows where the first column is "Location" (assuming it's the header)
            if burn[0].lower() == "location":
                continue

            # Validate the row length to prevent index errors
            if len(burn) < 3:  # Ensure at least location, date, and prop exist
                continue

            try:
                burns.append(Burn(
                    user_id=current_user.id,
                    location=burn[0],
                    time=datetime.strptime(burn[1], '%Y-%m-%d'),
                    prop=burn[2],
                    notes=burn[3] if len(burn) > 3 and burn[3] != '' else None
                ))
            except ValueError:
                # Skip rows with invalid date formats
                continue

        # Bulk insert ORM burn objects
        db.session.bulk_save_objects(burns)
        db.session.commit()
        return {'message': 'Import successful!', 'redirect_url': url_for('main.spinner_record_page', spinner_username=current_user.username)}
    return render_template('import_data.html')


@app.route('/sign-out.html')
def sign_out_page():
    logout_user()
    return redirect(url_for('main.home_page'))

@app.route('/forgot-password.html', methods=['GET', 'POST'])
def forgot_password_page():

    if request.method == 'POST':
        email = request.form.get('email').strip().lower()
        user = db.session.query(User).filter_by(email=email).first()

        # TODO: Consider if we should error for emails that don't exist
        if not user:
            flash('There is no user with this email in our database.', category='error')
        
        # Generate a code and url to reset this users password
        random_code = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(24))
        db.session.query(PasswordReset).filter_by(user_id=user.id).delete()
        db.session.add(PasswordReset(
            user_id=user.id,
            reset_code=random_code
        ))
        db.session.commit()
        user_reset_url = os.getenv('TBT_BASE_URL') + url_for('main.reset_password_page', reset_code=randome_code)

        # Send the reset password email along with the custom url
        Email.send_template('email_pwd_reset.html', email, {
            'username': user.username,
            'reset_url': user_reset_url
        })

        flash('We have emailed you a link to reset your password. This link is valid for 15 minutes.', category='success')


    return render_template('/auth/forgot.html')

@app.route('/reset-password.html', methods=['GET', 'POST'])
def reset_password_page():
    # Try to get the password reset object for this reset code
    pwdr = db.session.query(PasswordReset).filter_by(reset_code=request.args.get('reset_code')).first()
    
    if request.method == 'POST':
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')


        if password != password_confirm:
            flash('Password does not match confirmation, please re-enter password and try again.', category='error')
        elif not pwdr:
            flash('Password reset code is invalid. Please use the "forgot password" button again.', category='error')
        elif (datetime.utcnow() - pwdr.requested) > timedelta(minutes=15):
            print(pwdr.requested - datetime.utcnow())
            flash('Password reset code expired. Please use the "forgot password" button again.', category='error')
        else:
            user = db.session.query(User).filter_by(id=pwdr.user_id).first() 
            user.password = User.hash_pass(password)
            db.session.query(PasswordReset).filter_by(user_id=user.id).delete()
            db.session.commit()
            flash('Your password has been updated!', category='success')
    return render_template('/auth/reset_password.html')

@app.route('/pull_and_update', methods=['POST'])
def github_webhook():
    if request.method == 'POST':
        repo = git.Repo('tbt')
        origin = repo.remotes.origin
        origin.pull()
        return 'Update PythonAnywhere server succesfully', 200

@app.route('/settings.html')
@login_required
def settings_page():
    return render_template('settings.html', current_user=current_user)

@app.route('/burn/<burn_id>/edit.html')
@login_required
def edit_burn_page(burn_id: int):


    burn = db.session.query(Burn).filter_by(id=burn_id).first()

    if not burn:
        abort(404)

    return render_template('edit_burn.html', burn=burn)


@app.route('/spinner/<spinner_username>/profile.html')
def spinner_profile_page(spinner_username: str):
    spinner = db.session.query(User).filter_by(username=spinner_username).first()

    if not spinner:
        abort(404)

    props = [burn.prop for burn in spinner.burns]
    most_common = Counter(props).most_common(1)
    
    if len(spinner.burns) > 0:
        last_burn = spinner.burns[-1]
        last_time = last_burn.time.strftime('%b %-d')
    else:
        last_time = 'N/A'
    activity_data = [burn.time.strftime("%Y-%m-%d") for burn in spinner.burns] 

    about = """
    Lorem ipsum dolor sit amet, consectetur adipiscing elit. Quisque volutpat orci non ullamcorper sodales. Sed elementum metus vitae aliquam faucibus. Nullam ac diam risus. Nunc feugiat, turpis id rutrum consequat, ex erat lobortis leo, in fermentum purus mi eu nulla. Nulla et laoreet dui. Nullam pharetra odio sed odio varius, sed lobortis nisl congue. 
    """

    return render_template('profile.html', 
                           spinner=spinner,
                           about=about,
                           total_burns=len(spinner.burns),
                           last_time=last_time,
                           top_prop=most_common[0][0] if most_common else 'None',
                           activity_data=activity_data,
                           )

@app.route('/spinner/<spinner_username>/statistics.html')
@login_required
def spinner_stats_page(spinner_username):

    spinner = db.session.query(User).filter_by(username=spinner_username).first()
 
    props = {}
    locations = {}
    total_burns = 0
    date_list = {}
    for burn in spinner.burns:
        total_burns += 1

        if burn.time not in date_list:
            date_list[burn.time] = {}
        if burn.prop not in date_list[burn.time]:
            date_list[burn.time][burn.prop] = 0
        date_list[burn.time][burn.prop] += 1

        if burn.location not in locations:
            locations[burn.location] = 0
        locations[burn.location] += 1

        if burn.prop not in props:
            props[burn.prop] = 0
        props[burn.prop] += 1

    burns = db.session.query(Burn).filter_by(user_id=spinner.id).order_by(asc(Burn.time)).all()
    counts = 0

    dates = [x for x in date_list.keys()]

    unique_props = []
    prop_counts = []
    unique_locations = []
    location_counts = []

    if locations and props:
        unique_locations, location_counts = zip(*locations.items())
        unique_locations = str(unique_locations).replace('(','[').replace(')', ']')
        location_counts = str(location_counts).replace('(', '[').replace(')', ']')

        unique_props, prop_counts = zip(*props.items())        
        unique_props = str(unique_props).replace('(', '[').replace(')', ']').replace('\'', '"')
        prop_counts = str(prop_counts).replace('(', '[').replace(')', ']')
    




    prop_counts_over_time = {prop: [0] for prop in props.keys()}
    for day in dates:
        for prop in props.keys():
            if prop in date_list[day]:
                prop_counts_over_time[prop].append(prop_counts_over_time[prop][-1]+date_list[day][prop])
            else:
                prop_counts_over_time[prop].append(prop_counts_over_time[prop][-1])

    dates = [str(x) for x in dates]

    return render_template('spinner_stats.html', 
                           total_burns=total_burns,
                           last_burn=str(burns[-1].time) if burns else [],
                           unique_props=unique_props,
                           true_unique_props=props.keys(),
                           prop_counts=prop_counts,
                           unique_locations=unique_locations,
                           location_counts=location_counts,
                           prop_counts_over_time=prop_counts_over_time,
                           all_dates=dates)

@app.route('/simulate')
def simulate_page():
    return render_template('simulate.html')

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
            if field == 'time':
                burn.time = date(*[int(x) for x in body.get('time').split('-')])
                continue
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



#-#-#-#-#-#-#-#-#-#- Trainer Endpoints -#-#-#-#-#-#-#-#-#-#
@app.route('/trainers/poi/stalls')
def trainer_poi_stalls():
    faces = ('U', 'R', 'L', 'D', 'F', 'B')
    left = random.sample(faces, 2)
    right = random.sample(faces, 2)
    drill = left[0] + right[0] + '<->' + left[1] + right[1]
    return render_template('/trainers/poi/stalls.html', drill=drill)
