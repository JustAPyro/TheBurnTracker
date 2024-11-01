def test_get(client):
    response = client.get('/sign-in.html')
    assert(response.status_code == 200)

def test_wrong_password(client):
    pass
