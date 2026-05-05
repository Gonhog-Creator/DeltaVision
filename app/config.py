import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration management for DeltaVision"""
    
    def __init__(self, config_dir: str = "configs"):
        self.config_dir = Path(config_dir)
        self.settings = self._load_yaml("settings.yaml")
        self.cameras = self._load_yaml("cameras.yaml")
        self.zones = self._load_json("zones.json")
        
    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        """Load YAML configuration file"""
        file_path = self.config_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _load_json(self, filename: str) -> Dict[str, Any]:
        """Load JSON configuration file"""
        import json
        file_path = self.config_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        with open(file_path, 'r') as f:
            return json.load(f)
    
    @property
    def database_url(self) -> str:
        """Get database connection URL"""
        # Check if DATABASE_URL is set in environment (for SQLite)
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            return database_url
            
        # Fall back to PostgreSQL configuration
        db_config = self.settings['database']
        return (
            f"postgresql://{db_config['user']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}/{db_config['name']}"
        )
    
    @property
    def redis_url(self) -> Optional[str]:
        """Get Redis connection URL"""
        redis_config = self.settings.get('redis', {})
        if not redis_config.get('host'):
            return None
        
        password = f":{redis_config['password']}@" if redis_config.get('password') else ""
        return f"redis://{password}{redis_config['host']}:{redis_config['port']}/{redis_config['db']}"
    
    @property
    def video_data_path(self) -> str:
        """Get video data directory path"""
        return os.getenv('VIDEO_DATA_PATH', '../vids')
    
    @property
    def log_path(self) -> str:
        """Get log directory path"""
        return os.getenv('LOG_PATH', 'logs')
    
    def get_camera_config(self, camera_id: str) -> Dict[str, Any]:
        """Get configuration for specific camera"""
        return self.cameras['cameras'].get(camera_id, {})
    
    def get_zones_for_camera(self, camera_id: str) -> list:
        """Get zone definitions for specific camera"""
        return self.zones.get(camera_id, [])

# Global config instance
config = Config()
