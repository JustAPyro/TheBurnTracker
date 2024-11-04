def test_get(client):
    response = client.get('/', follow_redirects=True)
    assert(response.status_code == 200)
    assert(b'<title>Sign in</title' in response.data)

def test_get_authed(auth_client):
    response = auth_client.get('/', follow_redirects=True)
    assert(response.status_code == 200)
    assert(b'<title>The Burn Tracker</title>' in response.data)

