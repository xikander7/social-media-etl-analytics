"""
Configuration management for Social Media ETL Analytics
"""

import os
import yaml
from pathlib import Path
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for managing environment variables and settings"""
    
    # Base paths
    BASE_DIR = Path(__file__).parent.parent.parent
    DATA_DIR = BASE_DIR / "data"
    RAW_DATA_DIR = DATA_DIR / "raw"
    PROCESSED_DATA_DIR = DATA_DIR / "processed"
    STAGING_DATA_DIR = DATA_DIR / "staging"
    CONFIG_DIR = BASE_DIR / "config"
    MODELS_DIR = BASE_DIR / "models"
    REPORTS_DIR = BASE_DIR / "reports"
    
    # Social Media API Configuration
    TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
    TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')
    TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
    TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
    TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')
    
    FACEBOOK_APP_ID = os.getenv('FACEBOOK_APP_ID')
    FACEBOOK_APP_SECRET = os.getenv('FACEBOOK_APP_SECRET')
    FACEBOOK_ACCESS_TOKEN = os.getenv('FACEBOOK_ACCESS_TOKEN')
    
    INSTAGRAM_CLIENT_ID = os.getenv('INSTAGRAM_CLIENT_ID')
    INSTAGRAM_CLIENT_SECRET = os.getenv('INSTAGRAM_CLIENT_SECRET')
    INSTAGRAM_ACCESS_TOKEN = os.getenv('INSTAGRAM_ACCESS_TOKEN')
    
    # AWS Configuration
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    AWS_S3_BUCKET = os.getenv('AWS_S3_BUCKET')
    
    # Redshift Configuration
    REDSHIFT_HOST = os.getenv('REDSHIFT_HOST')
    REDSHIFT_PORT = int(os.getenv('REDSHIFT_PORT', 5439))
    REDSHIFT_DATABASE = os.getenv('REDSHIFT_DATABASE')
    REDSHIFT_USER = os.getenv('REDSHIFT_USER')
    REDSHIFT_PASSWORD = os.getenv('REDSHIFT_PASSWORD')
    
    # IICS Configuration
    IICS_USERNAME = os.getenv('IICS_USERNAME')
    IICS_PASSWORD = os.getenv('IICS_PASSWORD')
    IICS_BASE_URL = os.getenv('IICS_BASE_URL')
    
    # Notification Configuration
    NOTIFICATION_EMAIL = os.getenv('NOTIFICATION_EMAIL')
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Data Processing Settings
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', 1000))
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))
    
    @classmethod
    def validate_required_configs(cls):
        """Validate that required configuration variables are set"""
        required_configs = [
            'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_S3_BUCKET',
            'REDSHIFT_HOST', 'REDSHIFT_DATABASE', 'REDSHIFT_USER', 'REDSHIFT_PASSWORD'
        ]
        
        missing_configs = []
        for config in required_configs:
            if not getattr(cls, config):
                missing_configs.append(config)
        
        if missing_configs:
            raise ValueError(f"Missing required configuration: {', '.join(missing_configs)}")
        
        return True
    
    @classmethod
    def get_redshift_connection_string(cls):
        """Get Redshift connection string for SQLAlchemy"""
        return (f"postgresql://{cls.REDSHIFT_USER}:{cls.REDSHIFT_PASSWORD}@"
                f"{cls.REDSHIFT_HOST}:{cls.REDSHIFT_PORT}/{cls.REDSHIFT_DATABASE}")

def setup_logging():
    """Setup logging configuration"""
    log_level = getattr(logging, Config.LOG_LEVEL.upper())
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/etl_pipeline.log'),
            logging.StreamHandler()
        ]
    )

def load_yaml_config(config_file):
    """Load configuration from YAML file"""
    config_path = Config.CONFIG_DIR / config_file
    if config_path.exists():
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    return {}