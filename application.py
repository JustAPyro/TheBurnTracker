from flask import Flask, request, render_template, redirect, url_for 
from flask_login import login_user, login_required, logout_user, current_user, LoginManager
from database import db, User, Burn
from datetime import datetime, date

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'

db.init_app(app)
with app.app_context():
    db.create_all()

login_manager = LoginManager()
login_manager.login_view = 'sign_in_page'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(id):
    return db.session.query(User).filter_by(id=id).first()


@app.route('/')
def home():
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
        if not user:
            print('ERROR: Tried to log in an unfound user')
        if not user.check_pass(password):
            print('ERROR: Invalid password')

        login_user(user)
        user.last_login = datetime.now().astimezone()
        db.session.commit()

        return redirect(url_for('spinner_page', spinner_username=user.username))

    return render_template('auth/sign_in.html')

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

        # Add to the database and commit
        db.session.add(User(
            username=username,
            email=email,
            password=User.hash_pass(password)
        ))
        db.session.commit()

    return render_template('auth/sign_up.html')

@app.route('/spinner/<spinner_username>.html', methods=['GET', 'POST'])
@login_required
def spinner_page(spinner_username: str):

    if request.method == 'POST':
        # Collect the data from the form
        location = request.form.get('location')
        date = request.form.get('date_today')
        time = request.form.get('time_now')
        prop = request.form.get('prop')
   
        # Create the burn object
        db.session.add(Burn(user_id=current_user.id, location=location, prop=prop,
                            time=datetime(year=int(date[0:4]), month=int(date[5:7]), day=int(date[8:9]),
                                          hour=int(time[0:2]), minute=int(time[4:5]), second=int(time[6:7]))))
        db.session.commit() 
        return redirect(url_for('spinner_page', spinner_username=current_user.username))

        
    burns = db.session.query(Burn).filter_by(user_id=current_user.id).all()
    return render_template('spinner.html', 
                           last_location='' if len(current_user.burns) <= 0 else current_user.burns[-1].location,
                           date_today=datetime.now().strftime('%Y-%m-%d'),
                           time_now=datetime.now().strftime('%H:%M:%S'),
                           )

@app.route('/api/v1/burn.json')
def burn_api():
    return 'oops'

