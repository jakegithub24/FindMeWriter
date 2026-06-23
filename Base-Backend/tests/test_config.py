def test_development_config(app):
    assert app.config['JWT_ACCESS_TOKEN_EXPIRES'] == 3600
    assert app.config['JWT_REFRESH_TOKEN_EXPIRES'] == 604800
    assert app.config['ENCRYPTION_KEY'] is not None

def test_testing_config(app):
    assert app.config['TESTING'] is True
