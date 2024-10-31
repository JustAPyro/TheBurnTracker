# Make sure the page can be returned
def test_get(client):
    response = client.get('/sign-up.html')
    assert(response.status_code == 200)
    

