from app import db, User
from flask_login import login_required, current_user
import os
import jwt
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
api = Blueprint('api', __name__)

@api.route('/auth/sign-in.json', methods=['GET', 'POST'])
def sign_in_api():

    problems = []
    for field in ('email', 'password'):
        if request.json.get(field) == None:
            problems.append({'Missing field': field})


    if problems:
        return jsonify(problems), 403
    
    user = db.session.query(User).filter_by(email=request.json.get('email')).first()
    if not user or not user.check_pass(request.json.get('password')):
        return jsonify({'Unknown': 'username'})

    user.last_login = datetime.now().astimezone()
    db.session.commit()

    token = jwt.encode({
            'sub': f'{user.id}+{user.username}+{user.email}',
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(minutes=30)
        }, 
        os.getenv('TBT_SECRET'), 
        algorithm='HS256')

    # login_user()
    return jsonify({'token': token}), 200

@api.route('/user.json', methods=['GET', 'POST'])
def user_api():
    if request.method == 'GET':
        output = []
        for user in db.session.query(User).all():
            output.append({
                'username': user.username,
                'email': user.email,
                'id': user.id
            }) 
        return jsonify(output) 

    if request.method == 'POST':

        problems = []
        for field in ('username', 'email', 'password'):
            if request.json.get(field) == None:
                problems.append({'Missing field': field})
                
        username = request.json.get('username')    
        email = request.json.get('email')
        password = request.json.get('password')
        
        if db.session.query(User).filter(User.username.ilike(username)).first():
            problems.append({'Not unique': 'username'})
        if db.session.query(User).filter_by(email=email).first():
            problems.append({'Not unique': 'email'})
                            
        if problems:
            return jsonify(problems), 403

        # Create a user and add to database
        user = User(username=username, email=email, password=User.hash_pass(password))
        db.session.add(user)
        db.session.commit()

        return jsonify({
            'id': user.id,
            'username': user.username,
            'email': user.email
        })

@api.route('/session.json')
@login_required
def session_api():
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
    })

