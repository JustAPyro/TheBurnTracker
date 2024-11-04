def test_get(client):
    response = client.get('/sign-in.html')
    assert(response.status_code == 200)


def test_wrong_password(auth_client):
    so = auth_client.get('/sign-out.html', follow_redirects=True)
    assert(so.status_code == 200)

    response = auth_client.post('/sign-in.html', follow_redirects=True, data={
        'email': auth_client.email,
        'password': 'WRONG'
    })

    assert(response.status_code == 401)
    assert(b'Incorrect password, try again' in response.data)
    assert(b'<div class="alert alert-danger alert-dismissable fade show"' in response.data)

def test_wrong_username(client):
    response = client.post('/sign-in.html', follow_redirects=True, data={
        'email': 'NOTREAL',
        'password': 'anything'
    })

    assert(b'Incorrect password, try again' in response.data)
    assert(b'<div class="alert alert-danger alert-dismissable fade show"' in response.data)
    assert(response.status_code == 401)

def test_correct_password(auth_client):
    so = auth_client.get('/sign-out.html', follow_redirects=True)
    assert(so.status_code == 200)

    response = auth_client.post('/sign-in.html', follow_redirects=True, data={
        'email': auth_client.email,
        'password': auth_client.password
    })

    assert(response.status_code == 200)
    assert(b'<title>The Burn Tracker</title>' in response.data)
    assert(f'Sign out ({auth_client.username})'.encode('utf-8') in response.data)
