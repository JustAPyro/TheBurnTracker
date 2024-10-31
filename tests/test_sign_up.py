# Make sure the page can be returned
def test_get(client):
    response = client.get('/sign-up.html')
    assert(response.status_code == 200)
    
def test_mismatched_passwords(client):
    data={
        'username': 'test',
        'email': 'dev@test.com',
        'password': '1234567',
        'password_confirm': '7654321'
    }
    response = client.post('/sign-up.html', data=data, follow_redirects=True)
    assert(b'Error: Password confirmation field does not match password')
    assert(response.status_code == 403)

def test_existing_email(client):
    data={
        'username': 'test',
        'email': 'dev@test.com',
        'password': '1234567',
        'password_confirm': '1234567'
    }
    client.post('/sign-up.html', data=data, follow_redirects=True)
    
    data2={
        'username': 'test2',
        'email': 'dev@test.com',
        'password': '12345678',
        'password_confirm': '12345678'
    }
    response = client.post('/sign-up.html', data=data2, follow_redirects=True)

    assert(b'Error: Email already in use, please use a different email or use &#34;Forgot Password&#34;' in response.data)
    assert(response.status_code==403) 

def test_existing_username(client):
    data={
        'username': 'test',
        'email': 'dev@test.com',
        'password': '12345678',
        'password_confirm': '12345678'
    }
    client.post('/sign-up.html', data=data, follow_redirects=True)

    data2={
        'username': 'test',
        'email': 'dev2@test.com',
        'password': '12345678',
        'password_confirm': '12345678'
    }
    response = client.post('/sign-up.html', data=data2, follow_redirects=True)

    assert(b'Error: Tried to create user with existing username' in response.data)
    assert(response.status_code==403)

def test_bad_password(client):
    data={
        'username': 'test',
        'email': 'dev@test.com',
        'password': '123qwe',
        'password_confirm': '123qwe',
    }
    
    response = client.post('/sign-up.html', data=data, follow_redirects=True)

    

