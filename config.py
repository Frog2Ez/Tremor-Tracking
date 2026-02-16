"""
Configuration settings for Tremor Tracker Flask application
Supports different configurations for development, testing, and production
"""

import os
from datetime import timedelta


class Config:
    """
    Base configuration class
    Contains settings common to all environments
    """
    # Secret key for session management and CSRF protection
    # IMPORTANT: Change this to a random string in production!
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # SQLAlchemy settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Disable event system to save resources
    SQLALCHEMY_RECORD_QUERIES = True  # Enable query recording for debugging
    
    # JSON settings
    JSON_SORT_KEYS = False  # Don't sort JSON keys (preserve order)
    JSONIFY_PRETTYPRINT_REGULAR = True  # Pretty print JSON in responses
    
    # CORS settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # Pagination defaults
    DEFAULT_PAGE_SIZE = 100
    MAX_PAGE_SIZE = 1000
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # File upload settings (for future image/document uploads)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Sensor data settings
    MAX_BATCH_SIZE = 1000  # Maximum readings in a single batch upload
    SENSOR_DATA_RETENTION_DAYS = 90  # Days to keep detailed sensor data
    
    # Tremor detection thresholds
    TREMOR_DETECTION_THRESHOLD = 0.2  # Minimum magnitude to consider as tremor
    TREMOR_FREQUENCY_MIN = 4.0  # Hz - minimum tremor frequency
    TREMOR_FREQUENCY_MAX = 6.0  # Hz - maximum tremor frequency


class DevelopmentConfig(Config):
    """
    Development configuration
    Used for local development with debug mode enabled
    """
    DEBUG = True
    TESTING = False
    
    # Use SQLite for development
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///tremor_tracker_dev.db'
    
    # Enable detailed error messages
    PROPAGATE_EXCEPTIONS = True
    
    # CORS - allow all origins in development
    CORS_ORIGINS = ['*']


class TestingConfig(Config):
    """
    Testing configuration
    Used for running automated tests
    """
    DEBUG = False
    TESTING = True
    
    # Use in-memory SQLite for tests (fast and isolated)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable CSRF protection in tests
    WTF_CSRF_ENABLED = False
    
    # Use faster password hashing for tests
    BCRYPT_LOG_ROUNDS = 4


class ProductionConfig(Config):
    """
    Production configuration
    Used for deployed production environment
    
    IMPORTANT: Set environment variables for production:
    - SECRET_KEY: Random secret key
    - DATABASE_URL: Production database connection string
    - CORS_ORIGINS: Comma-separated list of allowed origins
    """
    DEBUG = False
    TESTING = False
    
    # Production database (PostgreSQL recommended)
    # Format: postgresql://user:password@host:port/database
    # Or MySQL: mysql+pymysql://user:password@host:port/database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        os.environ.get('PROD_DATABASE_URL')
    
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("Production database URL must be set in DATABASE_URL environment variable")
    
    # Strict CORS in production - must specify allowed origins
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',')
    if not CORS_ORIGINS or CORS_ORIGINS == ['']:
        raise ValueError("CORS_ORIGINS must be set in production")
    
    # Enhanced security settings
    SESSION_COOKIE_SECURE = True  # Only send cookies over HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to session cookie
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')


class StagingConfig(ProductionConfig):
    """
    Staging configuration
    Similar to production but with some debugging features enabled
    """
    DEBUG = False
    TESTING = False
    
    # Staging database
    SQLALCHEMY_DATABASE_URI = os.environ.get('STAGING_DATABASE_URL') or \
        'postgresql://user:password@staging-host/tremor_tracker_staging'
    
    # More lenient CORS for staging
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'staging': StagingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """
    Get configuration object based on environment
    
    Args:
        config_name: Name of configuration ('development', 'testing', 'production', 'staging')
                    If None, uses FLASK_ENV environment variable
    
    Returns:
        Configuration class
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    return config.get(config_name, DevelopmentConfig)
