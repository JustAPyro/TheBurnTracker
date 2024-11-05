from testutil import Actions

def test_unauthenticated(client):
    response = client.get('/spinner/Tester.html', follow_redirects=True)
    assert(response.status_code == 200)
    

def test_get_authenticated(auth_client):
    response = auth_client.get(f'/spinner/{auth_client.username}.html')
    assert(response.status_code == 200)
