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
