class Actions:
    def __init__(self, client):
        self.client = client

    def create_user(self, username: str = 'Tester', email: str = 'Testing@gmail.com', password: str = '12345678'):

        payload = {
            'username': username,
            'email': email,
            'password': password,
            'password_confirm': password
        }
        response_sign_up = self.client.post('/sign-up.html', data=payload, follow_redirects=True)
        
