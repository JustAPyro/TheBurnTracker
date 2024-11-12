from testutil import Actions
from datetime import date, timedelta
import requests
import pytest


url = 'http://127.0.0.1:5000/user.json'

# --- Test basic page loading as an authorized and unauthorized user
def test_post_user(client):
    # Set up
    data = {'username': 'thing'}
    
    # Execute
    response = client.post(/user, json=data)
    
    # Verify
    assert(response.status_code == 403)



