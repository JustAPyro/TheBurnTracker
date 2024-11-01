from testutil import Actions

def test_unauthenticated(client):
    response = client.get('/spinner/Tester.html', follow_redirects=True)
    assert(response.status_code == 200)
    

def test_get(client):
    Actions(client).create_user(username='Tester')
    response = client.get('/spinner/Tester.html', follow_redirects=True)
    assert(response.status_code == 200)
