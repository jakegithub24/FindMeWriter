import sqlite3
import os
import click
from flask import g, current_app
from flask.cli import with_appcontext

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///findmewriter.db')
        db_path = db_uri.replace('sqlite:///', '')
        
        # Ensure the directory containing the database file exists
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            
        db = g._database = sqlite3.connect(
            db_path,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        db.row_factory = sqlite3.Row
    return db

def close_connection(exception=None):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db_cli():
    db = get_db()
    with current_app.open_resource('models/schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db_cli()
    click.echo('Initialized the database.')

def init_db(app):
    app.teardown_appcontext(close_connection)
    app.cli.add_command(init_db_command)
    
    # Initialize the database file and tables on startup if they don't exist
    with app.app_context():
        init_db_cli()

