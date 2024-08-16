from flask import Flask, request, render_template, redirect, url_for, flash 
from flask_login import login_user, login_required, logout_user, current_user, LoginManager
from database import db, User, Burn
from datetime import datetime, date
from dotenv import load_dotenv
import csv
import os

# Load and check for all env variables we need
load_dotenv()
print(os.getenv('TBT_DB_URI'))
if not os.getenv('TBT_DB_URI'):
    raise RuntimeError('Missing environment variable: TBT_DB_URI')

# Configure the flask application object
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('TBT_DB_URI')

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
            print('parsing file')
            file = request.files['file']

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

@app.route('/spinner/<spinner_username>/stats.html')
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



    return render_template('spinner_stats.html', 
                           total_burns=total_burns,
                           prop_counts=props)

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

        


@app.route('/api/v1/burn/{burn_id}.json', methods=['DELETE'])
def burn_api(burn_id):
    if request.method=='DELETE':
        pass
    return 'oops'

