from testutil import Actions
from datetime import date, timedelta
import pytest

# --- Test basic page loading as an authorized and unauthorized user
def test_get_unauthorized(client):
    response = client.get('/logger.html', follow_redirects=True)
    assert(response.status_code == 200)
    assert(b'<title>Sign in</title>' in response.data)

def test_get_clean(auth_client):
    response = auth_client.get('/logger.html', follow_redirects=True)
    assert(response.status_code == 200)
    assert(b'<title>Log Burn</title>' in response.data)
    assert(f'Sign out ({auth_client.username})'.encode('utf-8') in response.data)


# --- Test submitting valid burns
def test_log_burn(auth_client):

    # Execute - post a page with with a valid burn in it
    response = auth_client.post('/logger.html', follow_redirects=True, data={
        'burn_date': str(date.today()),
        'burn_location': 'Anywhere',
        'burn_prop': 'Poi',
        'burn_notes': None,
    })

    # Verify
    assert(response.status_code == 200)
    assert(b'Burn Logged' in response.data)
    assert(b'<div class="alert alert-success alert-dismissable fade show"' in response.data)


# --- Test submitting invalid burns
def test_fails_empty_location(auth_client):

    # Execute - Send request with invalid (empty) location
    response = auth_client.post('/logger.html', follow_redirects=True, data={
        'burn_date': str(date.today()),
        'burn_location': '',
        'burn_prop': 'Poi',
        'burn_notes': ''
    })
    
    # Verify - Fails with 400 and message
    assert(response.status_code == 400)
    assert(b'Invalid Location: Please enter a location' in response.data)
    assert(b'<div class="alert alert-danger alert-dismissable fade show"' in response.data)

def test_fails_whitespace_location(auth_client):

    # Execute - Send request with invalid (whitespace) location
    response = auth_client.post('/logger.html', follow_redirects=True, data={
        'burn_date': str(date.today()),
        'burn_location': '    ',
        'burn_prop': 'Poi',
        'burn_notes': ''
    })

    # Verify - Fails with 400 and message
    assert(response.status_code == 400)
    assert(b'Invalid Location: Please enter a location' in response.data)
    assert(b'<div class="alert alert-danger alert-dismissable fade show"' in response.data)
    
def test_fails_future_date(auth_client):

    # Set up - Find tomorrows date
    today = date.today()
    tomorrow = today + timedelta(days=1)

    # Execute, post a page with a future date
    response = auth_client.post('/logger.html', follow_redirects=True, data={
        'burn_date': str(tomorrow),
        'burn_location': 'Anywhere',
        'burn_prop': 'Poi',
        'burn_notes': ''
    })

    # Verify
    assert(response.status_code == 400)
    assert(b'Invalid Date: Please enter a date that is today or in the past' in response.data)
    assert(b'<div class="alert alert-danger alert-dismissable fade show"' in response.data)
    
def test_fails_empty_prop(auth_client):

    # Execute - Send request with invalid (empty) prop
    response = auth_client.post('/logger.html', follow_redirects=True, data={
        'burn_date': str(date.today()),
        'burn_location': 'Anywhere',
        'burn_prop': '',
        'burn_notes': ''
    })
    
    # Verify - Fails with 400 and message
    assert(response.status_code == 400)
    assert(b'Invalid Prop: Please enter a prop' in response.data)
    assert(b'<div class="alert alert-danger alert-dismissable fade show"' in response.data)

def test_fails_whitespace_prop(auth_client):

    # Execute - Send request with invalid (whitespace) prop
    response = auth_client.post('/logger.html', follow_redirects=True, data={
        'burn_date': str(date.today()),
        'burn_location': 'Anywhere',
        'burn_prop': '    ',
        'burn_notes': ''
    })

    # Verify - Fails with 400 and message
    assert(response.status_code == 400)
    assert(b'Invalid Prop: Please enter a prop' in response.data)
    assert(b'<div class="alert alert-danger alert-dismissable fade show"' in response.data)

# --- Test Populating fields
# - Date population
def test_populates_date(auth_client):
    response = auth_client.get('/logger.html', follow_redirects=True)
    pytest.skip('Cannot test current implementation')

# - Location population
def test_populates_location_none(auth_client):

    # Execute, get the page with no existing burns
    response = auth_client.get('/logger.html', follow_redirects=True)

    # Verify
    assert(response.status_code == 200)
    assert(b'<input type="text" class="form-control ms-1" id="burn_location" name="burn_location" value="">' in response.data)

def test_populates_location_burn(auth_client):
    # Set up - post a burn first
    sub_response = auth_client.post('/logger.html', follow_redirects=True, data={
        'burn_date': str(date.today()),
        'burn_location': 'Anywhere',
        'burn_prop': 'Poi',
        'burn_notes': '',
    })
    assert(sub_response.status_code == 200)
    
    # Execute - Load the new logger page
    response = auth_client.get('/logger.html', follow_redirects=True)

    # Verify that the new burn location has the same last location
    assert(response.status_code == 200)
    assert(b'<input type="text" class="form-control ms-1" id="burn_location" name="burn_location" value="Anywhere"' in response.data)

# - Quick prop population
def test_populates_quick_prop_none(auth_client):
    # Set up - None
    
    # Execute - Load the page which should have no quick props for fresh account
    response = auth_client.get('/logger.html', follow_redirects=True)

    # Verify
    assert(response.status_code == 200) # Page loads correctly
    assert(b'<div class="card-body border-top prop_quick_pick"' not in response.data)


def test_popultes_quick_prop_one(auth_client):
    # Set up - post a burn first
    sub_response = auth_client.post('/logger.html', follow_redirects=True, data={
        'burn_date': str(date.today()),
        'burn_location': 'Anywhere',
        'burn_prop': 'UniquePoi',
        'burn_notes': '',
    })
    assert(sub_response.status_code == 200)

    # Execute - Load page 
    response = auth_client.get('/logger.html', follow_redirects=True)

    # Verify
    assert(response.status_code == 200)
    assert(b'prop_quick_pick' in response.data)
    assert(b'UniquePoi' in response.data)

def test_populates_last_burn(auth_client):
    # Set up - post a burn first
    sub_response = auth_client.post('/logger.html', follow_redirects=True, data={
        'burn_date': str(date.today()),
        'burn_location': 'Anywhere',
        'burn_prop': 'UniquePoi',
        'burn_notes': '',
    })
    assert(sub_response.status_code == 200)

    # Execute - Load page 
    response = auth_client.get('/logger.html', follow_redirects=True)

    # Verify
    assert(response.status_code == 200)
    assert(f'<p>Last burn logged ({str(date.today())}):<br>UniquePoi at Anywhere</p>'.encode('utf-8') in response.data)

def test_populates_last_burn_retroactive(auth_client):
    # Set up - Post a more recent burn first - This should populate as most recent
    sub_response = auth_client.post('/logger.html', follow_redirects=True, data={
        'burn_date': '2024-10-02',
        'burn_location': 'Anywhere',
        'burn_prop': 'UniquePoi',
        'burn_notes': '',
    })
    assert(sub_response.status_code == 200)

    # Set up a second burn BEFORE the first (Which should still populate first as last burn)
    sub_response = auth_client.post('/logger.html', follow_redirects=True, data={
        'burn_date': '2023-10-02',
        'burn_location': 'AnywhereElse',
        'burn_prop': 'UniqueDragon',
        'burn_notes': '',
    })
    assert(sub_response.status_code == 200)

    # Execute - Load page 
    response = auth_client.get('/logger.html', follow_redirects=True)

    # Verify
    assert(response.status_code == 200)
    assert(f'<p>Last burn logged (2024-10-02):<br>UniquePoi at Anywhere</p>'.encode('utf-8') in response.data)
    
    

    
    
    
    



