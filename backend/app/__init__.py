from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_cors import CORS
from backend.config.config import config
from datetime import timedelta

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
login_manager.login_message = 'Please log in to access this page.'
login_manager.session_protection = None

def create_app(config_name='default'):
    app = Flask(__name__,
                template_folder='../../frontend/templates',
                static_folder='../../frontend/static')
    
    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app) if hasattr(config[config_name], 'init_app') else None
    
    # Set secret key and session configuration
    app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production!
    app.config['USE_SESSION_FOR_NEXT'] = False
    app.config['SESSION_PROTECTION'] = None
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=30)
    app.config['REMEMBER_COOKIE_SECURE'] = True  # Enable for HTTPS
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    
    # Initialize CORS with more specific settings
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "https://patient-health-managementsystem.netlify.app",
                "http://localhost:3000",  # For local development
                "http://localhost:5000"
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Range", "X-Content-Range"],
            "supports_credentials": True
        }
    })
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Import and register blueprints
    from backend.app.routes.auth import auth_bp
    from backend.app.routes.main import main_bp
    from backend.app.routes.patient import patient_bp
    from backend.app.routes.doctor import doctor_bp
    from backend.app.routes.api import api_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Import models to ensure they are known to Flask-SQLAlchemy
    from backend.app.models import User, DoctorProfile, PatientProfile
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app 