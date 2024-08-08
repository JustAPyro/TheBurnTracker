from flask import Flask, render_template, redirect, url_for 
from database import db

app = Flask(__name__)

@app.route('/')
def home():
    return redirect(url_for('sign_in_page'))

@app.route('/sign-in.html')
def sign_in_page():
    return render_template('auth/sign_in.html')
