from models.db import get_db

def test_get_db(app):
    with app.app_context():
        db1 = get_db()
        db2 = get_db()
        assert db1 is db2
        
        # Verify schema tables are created
        cursor = db1.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        assert cursor.fetchone() is not None

def test_init_db_command(runner):
    result = runner.invoke(args=['init-db'])
    assert 'Initialized the database' in result.output
