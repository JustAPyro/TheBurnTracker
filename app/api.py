from app import db, User, Burn
from flask_login import login_required, current_user
import os
import jwt
from datetime import date, datetime, timedelta, UTC
from flask import Blueprint, request, jsonify
api = Blueprint('api', __name__)

class Validator:
    def __init__(self, request):
        self.json = request.json
        self.may_contain = []
        self.problems = []

    def contains(self, field, oftype='any'):
        if self.json.get(field):
            try:
                method = getattr(Validator, f'_type_{oftype}')
                if not method(self, self.json.get(field)):
                    self.problems.append({'TypeError': field})
                else: 
                    self.json[field] = method(self, self.json.get(field))
            except:
                pass

            self.may_contain.append(field)
        else:
            self.problems.append({'Missing': field})
        
        return self

    def optional(self, field, oftype='any'):
        if self.json.get(field):
            try:
                method = getattr(Validator, f'_type_{oftype}')
                if not method(self, self.json.get(field)):
                    self.problems.append({'TypeError': field})
                else:
                    self.json[field] = method(self, self.json.get(field))
            except:
                pass

        self.may_contain.append(field)
        return self

    # Validate is called at the end of the pipeline
    # It will do any remaining validation and then return the list of problems
    def validate(self):
        for field in self.json.keys():
            if field not in self.may_contain:
                self.problems.append({'Unexpected': field})
        
        return self.problems

    # The following _type_ functions are used to validate type.
    # A _type_ function will cast and return the correct type from given string
    # or return None if it doesn't appear to be of that type
    def _type_any(self, any_str):
        return any_str

    def _type_date(self, date_str):
        try:
            return date.fromisoformat(date_str)
        except:
            return None

@api.route('/auth/sign-in.json', methods=['POST'])
def sign_in_api():
    problems = (Validator(request)
                .contains('email')
                .contains('password')
                .validate())

    if problems:
        return jsonify(problems), 400
    
    user = db.session.query(User).filter_by(email=request.json.get('email')).first()
    if not user or not user.check_pass(request.json.get('password')):
        return jsonify({'Unknown': 'username/password'}), 403

    user.last_login = datetime.now().astimezone()
    db.session.commit()

    token = jwt.encode({
            'sub': f'{user.id}+{user.username}+{user.email}',
            'iat': datetime.now(UTC),
            'exp': datetime.now(UTC) + timedelta(minutes=30)
        }, 
        os.getenv('TBT_SECRET'), 
        algorithm='HS256')

    # login_user()
    return jsonify({'token': token}), 200

@api.route('/session.json')
@login_required
def session_api():
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
    })

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
        
        if username and db.session.query(User).filter(User.username.ilike(username)).first():
            problems.append({'Not unique': 'username'})
        if email and db.session.query(User).filter_by(email=email).first():
            problems.append({'Not unique': 'email'})
                            
        if problems:
            return jsonify(problems), 400

        # Create a user and add to database
        user = User(username=username, email=email, password=User.hash_pass(password))
        db.session.add(user)
        db.session.commit()

        return jsonify({
            'id': user.id,
            'username': user.username,
            'email': user.email
        })

@api.route('/user/<user_id>.json', methods=['GET'])
def user_specified_api(user_id: int):
    user = db.session.query(User).filter_by(id=user_id).first()
    if not user:
        abort(404)

    return jsonify(user.as_dict())

@api.route('/user/<user_id>.json', methods=['PATCH'])
@login_required
def user_specified_api_auth(user_id: int):
    user = db.session.query(User).filter_by(id=user_id).first()
    if not user:
        abort(404)

    blocked_fields = [
        'password',
        'email',
        'created_on',
        'last_login',
    ]

    problems = []
    for field in request.json.keys():
        if field in blocked_fields: 
            problems.append({'Blocked': field})
        elif not hasattr(user, field):
            problems.append({'Unknown': field})

    if len(problems) > 0:
        return jsonify(problems), 403

    for field, value in request.json.items():
        setattr(user, field, value)

    return jsonify(user.as_dict())
        

@api.route('/user/<user_id>/burns.json')
def user_burns_api_noauth(user_id: int):
    user = db.session.query(User).filter_by(id=user_id).first()
    if not user:
        abort(404)

    return jsonify([burn.as_dict() for burn in user.burns])

@api.route('/user/<user_id>/burns.json', methods=['POST'])
def user_burns_api_auth(user_id: int):
    user = db.session.query(User).filter_by(id=user_id).first()
    #if not user or user_id != current_user.id:
    #    abort(404)

    problems = (Validator(request)
        .contains('location')
        .contains('time', oftype='date')
        .contains('prop')
        .optional('notes')
        .validate())

    if len(problems) > 0:
        return jsonify(problems), 403

    burn = Burn(
        user_id=user_id, 
        location=request.json.get('location'),
        prop=request.json.get('prop'), 
        notes=request.json.get('notes'), 
        time=request.json.get('time'))
    db.session.add(burn)
    db.session.commit()
    return jsonify(burn.as_dict())

@api.route('/user/<user_id>/burns/<burn_id>.json')
def user_burns_specific_api_noauth(user_id: int, burn_id: int):
    burn = db.session.query(Burn).filter_by(id=burn_id).first()
    return jsonify(burn.as_dict())

@api.route('/user/<user_id>/burns/<burn_id>.json', methods=['PATCH', 'DELETE'])
def user_burns_specific_api_auth(user_id: int, burn_id: int):
    if request.method == 'PATCH':
        burn = db.session.query(Burn).filter_by(id=burn_id).first()
        if not burn:
            abort(404)

        problems = (Validator(request)
                    .optional('location')
                    .optional('time', oftype='date')
                    .optional('prop')
                    .optional('notes')
                    .validate())
        if problems:
            return jsonify(problems), 403



        for field, value in request.json.items():
            setattr(burn, field, value)
        db.session.commit()
        return jsonify(burn.as_dict())

    if request.method == 'DELETE':
        burn = db.session.query(Burn).filter_by(id=burn_id).delete()
        db.session.commit()
        return jsonify([]), 200




    



    




