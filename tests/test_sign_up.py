def test_sign_up(client):
    response = client.get('/sign-up.html')
    assert(response.status_code == 200)
    

