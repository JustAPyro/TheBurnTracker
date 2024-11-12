url = 'http://127.0.0.1:5000/auth/sign-in.json'

def test_post_sign_in_missing(client):
    # Execute
    response = client.post(url, json={
        'email': 'Tester@gmail.com'
    })

    # Verify
    assert(response.status_code == 400)
    assert(response.json == [{'Missing': 'password'}])

def test_post_sign_in_missing_pass(client):
    # Execute
    response = client.post(url, json={
        'password': '12345678'
    })

    # Verify
    assert(response.status_code == 400)
    assert(response.json == [{'Missing': 'email'}])


def test_post_sign_in_extra_fields(client):
    # Execute
    response = client.post(url, json={
        'email': 'Tester@gmail.com',
        'password': 'Secret',
        'extra': '12345678'
    })

    # Verify
    assert(response.status_code == 400)
    assert(response.json == [{'Unexpected': 'extra'}])

def test_post_sign_in_successful(client):
    # Setup
    sur = client.post('/user.json', json={
        'email': 'Tester@gmail.com',
        'password': '12345678',
        'username': 'Tester'
    })

    # Execute
    response = client.post(url, json={
        'email': 'Tester@gmail.com',
        'password': '12345678'
    })

    # Verify
    assert(response.status_code == 200)
    assert('token' in response.json)

def test_post_sign_in_unsuccessful(client):
    # Execute
    response = client.post(url, json={
        'email': 'Tester@gmail.com',
        'password': 'WRONG'
    })

    # Verify
    assert(response.status_code == 403)
    assert(response.json == {'Unknown': 'username/password'})

def test_post_sign_in_unsuccessful_user(client):
    # Execute
    response = client.post(url, json={
        'email': 'Wrong@gmail.com',
        'password': 'Anything'
    })

    # Verify
    assert(response.status_code == 403)
    assert(response.json == {'Unknown': 'username/password'})
