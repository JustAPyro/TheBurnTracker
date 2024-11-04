import pytest

from app import create_app, db

@pytest.fixture()
def app():
    app = create_app(create_db=False)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
    with app.app_context():
        db.create_all()

        yield app

        db.drop_all()

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def auth_client(app):
    client = app.test_client()
    
    username = 'Tester'
    email = 'Tester@gmail.com'
    password = '12345678'
    client.post('/sign-up.html', data={
        'username': username,
        'email': email,
        'password': password,
        'password_confirm': password
    })

    client.username = username
    client.email = email
    client.password = password

    return client
