import json
import os

# Defualt configuration structure
DEFAULT_CONFIG = {
    "API_KEYS": {
        "OPENWEATHER_API_KEY": "your_api_key_here"
    },
    "DATABASE": {
        "TYPE": "sqlite",
        "PATH": "heatshield.db"
    },
    "SERVER": {
        "HOST": "0.0.0.0",
        "PORT": 5000,
        "DEBUG": True
    },
    "ML_MODEL": {
        "USE_PRETRAINED": True,
        "MODEL_PATH": "models/risk_model.pkl"
    },
    "MOCK_DATA": {
        "ENABLED": True,
        "DEFAULT_LOCATION": "Rourkela, India"
    }
}

def load_config():
    """Load configuration from file and override with environment variables"""
    config = DEFAULT_CONFIG.copy()
    
    # 1. Try to load from config.json
    try:
        if os.path.exists('config.json'):
            with open('config.json', 'r') as f:
                file_config = json.load(f)
                # Deep merge or simple update? For now, simple update of top-level keys
                for key, value in file_config.items():
                    if key in config and isinstance(value, dict) and isinstance(config[key], dict):
                        config[key].update(value)
                    else:
                        config[key] = value
    except Exception as e:
        print(f"Warning: Could not load config.json: {e}")

    # 2. Override with Environment Variables (for Render/Deployment)
    
    # API Keys
    if os.environ.get('OPENWEATHER_API_KEY'):
        config['API_KEYS']['OPENWEATHER_API_KEY'] = os.environ.get('OPENWEATHER_API_KEY')
        
    # Database
    if os.environ.get('DATABASE_URL'):
        # If using a cloud DB (like Postgres on Render), we might want to switch TYPE
        # But for now, let's just allow overriding the path/url
        config['DATABASE']['PATH'] = os.environ.get('DATABASE_URL')
        if 'postgres' in config['DATABASE']['PATH']:
             config['DATABASE']['TYPE'] = 'postgresql'

    # Server
    if os.environ.get('PORT'):
        config['SERVER']['PORT'] = int(os.environ.get('PORT'))
    
    if os.environ.get('DEBUG'):
        config['SERVER']['DEBUG'] = os.environ.get('DEBUG').lower() == 'true'
        
    # ML Model
    if os.environ.get('ML_MODEL_PATH'):
        config['ML_MODEL']['MODEL_PATH'] = os.environ.get('ML_MODEL_PATH')

    # Mock Data
    if os.environ.get('MOCK_DATA_ENABLED'):
        config['MOCK_DATA']['ENABLED'] = os.environ.get('MOCK_DATA_ENABLED').lower() == 'true'

    return config

# Export the configuration object
config = load_config()
