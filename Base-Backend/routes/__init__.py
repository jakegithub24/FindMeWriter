from flask import Blueprint

def register_blueprints(app):
    from .auth import auth_bp
    from .student import student_bp
    from .volunteer import volunteer_bp
    from .college import college_bp
    from .admin import admin_bp
    from .complaints import complaints_bp
    from .helpdesk import helpdesk_bp
    from .shared import shared_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(student_bp, url_prefix='/api/student')
    app.register_blueprint(volunteer_bp, url_prefix='/api/volunteer')
    app.register_blueprint(college_bp, url_prefix='/api/college')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(complaints_bp, url_prefix='/api/complaints')
    app.register_blueprint(helpdesk_bp, url_prefix='/api/helpdesk')
    app.register_blueprint(shared_bp, url_prefix='/api')
