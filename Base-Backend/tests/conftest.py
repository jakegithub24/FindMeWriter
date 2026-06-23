import os
import tempfile
import pytest
from app import create_app
from models.db import get_db, close_connection

@pytest.fixture
def app():
    # Create a temporary file for the database
    db_fd, db_path = tempfile.mkstemp()
    
    # We must set ENCRYPTION_KEY and a valid base32 ADMIN_TOTP_SECRET in env for testing
    if 'ENCRYPTION_KEY' not in os.environ:
        os.environ['ENCRYPTION_KEY'] = 'elhXbcx515t3rlDeBZdVTyd7qUoc8fmMjBm6cvn4I-M='
    os.environ['ADMIN_TOTP_SECRET'] = 'KVKVEVCSK5JVETKB'
        
    app = create_app('testing')
    app.config.update({
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'TESTING': True
    })

    with app.app_context():
        # Force initialization of the database tables
        db = get_db()
        with app.open_resource('models/schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

    yield app

    # Cleanup database file
    with app.app_context():
        close_connection()
    os.close(db_fd)
    try:
        os.unlink(db_path)
    except OSError:
        pass

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()
