from testutil import Actions
import pytest

def test_get_unauthorized(client):

    response = client.get('/logger.html', follow_redirects=True)
    assert(response.status_code == 200)
    assert(b'<title>Sign in</title>' in response.data)

def test_get_clean(auth_client):
    response = auth_client.get('/logger.html', follow_redirects=True)
    assert(response.status_code == 200)
    assert(b'<title>Log Burn</title>' in response.data)
    assert(f'Sign out ({auth_client.username})'.encode('utf-8') in response.data)

def test_populates_date(auth_client):
    response = auth_client.get('/logger.html', follow_redirects=True)
    assert(response.status_code == 200)
    pytest.skip('Cannot test current implementation')

def test_fails_future_date(auth_client):
    pytest.skip('Unimplemented')
    
def test_populates_location(auth_client):
    pytest.skip('Unimplemented')
    response = auth_client.post('/logger.html', follow_redirects=True, data={
        burn_date: '2024-07-31',
        burn_location: "The Burn Circle",
        burn_prop: 'Poi'
    })




