from flask import Flask, request, render_template, redirect, url_for 
from database import db

app = Flask(__name__)

@app.route('/')
def home():
    return redirect(url_for('sign_in_page'))

@app.route('/sign-in.html')
def sign_in_page():
    return render_template('auth/sign_in.html')

@app.route('/sign-up.html', methods=['GET', 'POST'])
def sign_up_page():
    if request.method == 'POST':
        # Collect data from the input fields
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')

        if db.session.query(User).filter_by(email=email).first():
            print("ERROR: Tried to create user with existing email.")
        if password != password_confirm:
            print("ERROR: Tried to create account with mismatched password and password_confirm")
            # TODO: Throw error "Password doesn't match password confirmation"




        user.last_login = datetime.datetime.now().astimezone()
        db.session.commit()

    return render_template('auth/sign_up.html')
