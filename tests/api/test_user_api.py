from testutil import Actions
from datetime import date, timedelta
import requests
import pytest


url = 'http://127.0.0.1:5000/users.json'
tester_json = {
    'email': 'Tester@gmail.com',
    'username': 'Tester',
    'password': '12345678'
}

def test_get_user_none(client):
    # Execute
    response = client.get(url)

    # Assert
    assert(response.status_code == 200)
    assert(response.json == [])


def test_get_user_one(client):
    # Set-up
    data = {
        'username': 'Tester',
        'email': 'Tester@gmail.com',
        'password': 'Secret',
    }
    sur = client.post(url, json=data)
    assert(sur.status_code == 200)

    # Execute
    response = client.get(url)

    assert(response.status_code == 200)
    assert(response.json == [{
        'username': 'Tester',
        'email': 'Tester@gmail.com',
        'id': 1
    }])

def test_get_user_multiple(client):
    # Set-up
    for i in range(5):
        data = {
            'username': f'Tester{i}',
            'email': f'Tester{i}@gmail.com',
            'password': '12345678'
        }
        sur = client.post(url, json=data)
        assert(sur.status_code == 200)

    # Execute
    response = client.get(url)

    # Verify
    assert(response.status_code == 200)
    assert(len(response.json) == 5)

def test_post_user(client):
    # Set up
    data = {
        'username': 'Tester',
        'email': 'Tester@gmail.com',
        'password': 'Secret'
    }

    # Execute
    response = client.post(url, json=data)

    # Verify
    assert(response.status_code == 200)
    assert(response.json == {'username': 'Tester', 'email': 'Tester@gmail.com', 'id': 1})

def test_post_user_missing_fields_empty(client):
    # Execute
    response = client.post(url, json={'email': 'Tester@gmail.com', 'password': '12345678'})

    # Verify
    assert(response.status_code == 400)
    assert(response.json == [{'Missing field': 'username'}])


def test_post_user_email_collision(client):
    # Set up
    data = {
        'username': 'Tester',
        'email': 'Tester@gmail.com',
        'password': 'Secret'
    }
    setup_request = client.post(url, json=data)
    assert(setup_request.status_code == 200)
    data['username'] = 'Tester2'

    # Execute
    response = client.post(url, json=data)

    # Verify
    assert(response.json == [{'Not unique': 'email'}])
    assert(response.status_code == 400)

def test_post_user_username_collision(client):
    # Set up
    data = {
        'username': 'Tester',
        'email': 'Tester@gmail.com',
        'password': 'Secret'
    }
    setup_request = client.post(url, json=data)
    assert(setup_request.status_code == 200)
    data['email'] = 'Tester2@yahoo.com'

    # Execute
    response = client.post(url, json=data)

    # Verify
    assert(response.json == [{'Not unique': 'username'}])
    assert(response.status_code == 400)


def test_post_user_missing_fields(client):
    # Set up
    data = {'username': 'thing', 'password': '12345678'}
    
    # Execute
    response = client.post(url, json=data)
    
    # Verify
    assert(response.status_code == 400)
    assert(response.json == [{'Missing field': 'email'}])

def test_get_user_specific(client):
    # Set up
    sur = client.post('/users.json', json=tester_json)
    assert(sur.status_code == 200)

    # Execute
    response = client.get('/users/1.json')

    # Verify
    assert(response.status_code == 200)
    # "Public" fields
    for field in ('username', 'created_on', 'last_login'):
        assert(field in response.json)

    # "Private fields"
    for field in ('email', 'password'):
        assert(field not in response.json)

def test_get_user_specific_missing(client):
    # Execute
    response = client.get('/users/200.json')

    # Verify
    assert(response.status_code == 404)
    assert('message' in response.json)
    assert('path' in response.json)

def test_patch_user_noauth(client):
    # Setup
    r = client.post('/users.json', json=tester_json)
    assert(r.status_code == 200)

    
def test_patch_user_missing(client):
    # Execute
    response = client.patch('/users/200.json')

    # Verify
    assert(response.status_code == 404)
    assert('message' in response.json)
    assert('path' in response.json)



