import os
from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from dotenv import load_dotenv

from config import DevelopmentConfig, TestingConfig, ProductionConfig
from routes import register_blueprints
from models.db import init_db
from middleware.error_handlers import register_error_handlers
from middleware.rate_limiter import limiter

load_dotenv()

socketio = SocketIO(cors_allowed_origins="*")

def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    if config_name == 'production':
        config_class = ProductionConfig
    elif config_name == 'testing':
        config_class = TestingConfig
    else:
        config_class = DevelopmentConfig

    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    CORS(app)  # adjust in production
    limiter.init_app(app)

    # Save existing server handlers to preserve them across multiple init_app calls (e.g. in tests)
    old_handlers = {}
    old_namespace_handlers = {}
    if hasattr(socketio, 'server') and socketio.server:
        old_handlers = getattr(socketio.server, 'handlers', {})
        old_namespace_handlers = getattr(socketio.server, 'namespace_handlers', {})

    if app.config.get('TESTING'):
        socketio.init_app(app)
    else:
        socketio.init_app(app, async_mode='eventlet')

    if old_handlers:
        socketio.server.handlers.update(old_handlers)
    if old_namespace_handlers:
        socketio.server.namespace_handlers.update(old_namespace_handlers)

    # Database
    init_db(app)

    # Register blueprints
    register_blueprints(app)

    # Error handlers
    register_error_handlers(app)

    return app
