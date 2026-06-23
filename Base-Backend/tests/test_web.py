def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"FindMeWriter" in response.data
    # Check that skip link exists
    assert b"Skip to main content" in response.data
    # Check accessibility contrast and text size buttons exist
    assert b"toggle-contrast" in response.data
    assert b"toggle-size" in response.data

def test_login_page(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert b"Log In to Your Account" in response.data

def test_register_page(client):
    response = client.get('/register')
    assert response.status_code == 200
    assert b"Create an Account" in response.data

def test_dashboard_redirects_for_anonymous(client):
    response = client.get('/dashboard')
    assert response.status_code == 302
    assert response.headers['Location'] == '/login'

def test_terms_and_privacy_pages(client):
    response = client.get('/terms')
    assert response.status_code == 200
    assert b"Terms of Service" in response.data

    response = client.get('/privacy')
    assert response.status_code == 200
    assert b"Privacy Policy" in response.data

def test_profile_redirects_for_anonymous(client):
    response = client.get('/profile')
    assert response.status_code == 302
    assert response.headers['Location'] == '/login'

