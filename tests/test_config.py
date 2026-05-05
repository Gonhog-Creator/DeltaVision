import pytest
import tempfile
import os
from pathlib import Path
import json
import yaml

from app.config import Config

class TestConfig:
    """Test configuration management"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            
            # Create test configuration files
            settings = {
                'database': {
                    'host': 'localhost',
                    'port': 5432,
                    'name': 'test_db',
                    'user': 'test_user',
                    'password': 'test_pass'
                },
                'api': {
                    'host': '0.0.0.0',
                    'port': 8000,
                    'debug': False
                }
            }
            
            cameras = {
                'cameras': {
                    'A11': {
                        'id': 'A11',
                        'name': 'Test Camera A11',
                        'fps': 30,
                        'detection_threshold': 0.5
                    }
                }
            }
            
            zones = {
                'A11': [
                    {
                        'name': 'test_zone',
                        'description': 'Test zone',
                        'polygon': [[0, 0], [100, 0], [100, 100], [0, 100]],
                        'type': 'workstation',
                        'expected_dwell_time': 300
                    }
                ]
            }
            
            # Write configuration files
            with open(config_dir / 'settings.yaml', 'w') as f:
                yaml.dump(settings, f)
            
            with open(config_dir / 'cameras.yaml', 'w') as f:
                yaml.dump(cameras, f)
            
            with open(config_dir / 'zones.json', 'w') as f:
                json.dump(zones, f)
            
            yield str(config_dir)
    
    def test_load_config(self, temp_config_dir):
        """Test loading configuration"""
        config = Config(temp_config_dir)
        
        assert config.settings is not None
        assert config.cameras is not None
        assert config.zones is not None
        
        # Test database configuration
        assert 'database' in config.settings
        assert config.settings['database']['host'] == 'localhost'
        assert config.settings['database']['port'] == 5432
    
    def test_database_url(self, temp_config_dir):
        """Test database URL generation"""
        config = Config(temp_config_dir)
        db_url = config.database_url
        
        assert 'postgresql://' in db_url
        assert 'test_user' in db_url
        assert 'test_pass' in db_url
        assert 'test_db' in db_url
    
    def test_get_camera_config(self, temp_config_dir):
        """Test getting camera configuration"""
        config = Config(temp_config_dir)
        camera_config = config.get_camera_config('A11')
        
        assert camera_config is not None
        assert camera_config['id'] == 'A11'
        assert camera_config['name'] == 'Test Camera A11'
        assert camera_config['fps'] == 30
    
    def test_get_camera_config_not_found(self, temp_config_dir):
        """Test getting non-existent camera configuration"""
        config = Config(temp_config_dir)
        camera_config = config.get_camera_config('NONEXISTENT')
        
        assert camera_config == {}
    
    def test_get_zones_for_camera(self, temp_config_dir):
        """Test getting zones for camera"""
        config = Config(temp_config_dir)
        zones = config.get_zones_for_camera('A11')
        
        assert len(zones) == 1
        assert zones[0]['name'] == 'test_zone'
        assert zones[0]['type'] == 'workstation'
    
    def test_get_zones_for_camera_not_found(self, temp_config_dir):
        """Test getting zones for non-existent camera"""
        config = Config(temp_config_dir)
        zones = config.get_zones_for_camera('NONEXISTENT')
        
        assert zones == []
    
    def test_missing_config_file(self):
        """Test handling of missing configuration file"""
        with pytest.raises(FileNotFoundError):
            Config('/nonexistent/path')
    
    def test_invalid_yaml_file(self):
        """Test handling of invalid YAML file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            
            # Create invalid YAML file
            with open(config_dir / 'settings.yaml', 'w') as f:
                f.write('invalid: yaml: content: [')
            
            with pytest.raises(yaml.YAMLError):
                Config(str(config_dir))
    
    def test_invalid_json_file(self):
        """Test handling of invalid JSON file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            
            # Create valid settings.yaml
            settings = {'database': {'host': 'localhost'}}
            with open(config_dir / 'settings.yaml', 'w') as f:
                yaml.dump(settings, f)
            
            # Create invalid zones.json
            with open(config_dir / 'zones.json', 'w') as f:
                f.write('{"invalid": json content}')
            
            with pytest.raises(json.JSONDecodeError):
                Config(str(config_dir))
