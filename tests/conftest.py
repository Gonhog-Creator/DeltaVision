import pytest
import tempfile
import os
from pathlib import Path
import numpy as np
import cv2

@pytest.fixture
def temp_directory():
    """Create a temporary directory for tests"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def sample_video_file(temp_directory):
    """Create a sample video file for testing"""
    video_path = temp_directory / "test_video.mp4"
    
    # Create a simple test video
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(video_path), fourcc, 30.0, (640, 480))
    
    # Create 10 frames with some content
    for i in range(10):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        # Add some content to make it more realistic
        cv2.circle(frame, (320, 240), 50, (255, 255, 255), -1)
        cv2.putText(frame, f'Frame {i}', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        out.write(frame)
    
    out.release()
    yield str(video_path)
    
    # Cleanup
    if video_path.exists():
        video_path.unlink()

@pytest.fixture
def sample_frame():
    """Create a sample frame for testing"""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Add some content
    cv2.rectangle(frame, (100, 100), (200, 300), (255, 255, 255), -1)
    cv2.circle(frame, (400, 200), 30, (0, 255, 0), -1)
    cv2.putText(frame, 'Test Frame', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    return frame

@pytest.fixture
def mock_database_url():
    """Mock database URL for testing"""
    return "sqlite:///test.db"

@pytest.fixture
def zones_config():
    """Sample zones configuration for testing"""
    return {
        'A11': [
            {
                'name': 'material_rack',
                'description': 'Material storage area',
                'polygon': [[0, 0], [200, 0], [200, 200], [0, 200]],
                'type': 'storage',
                'expected_dwell_time': 30
            },
            {
                'name': 'cutting_table',
                'description': 'Cutting workstation',
                'polygon': [[250, 0], [450, 0], [450, 200], [250, 200]],
                'type': 'workstation',
                'expected_dwell_time': 300
            }
        ]
    }

@pytest.fixture
def camera_configs():
    """Sample camera configurations for testing"""
    return {
        'A11': {
            'id': 'A11',
            'name': 'Test Camera A11',
            'fps': 30,
            'resolution': {
                'width': 1920,
                'height': 1080
            },
            'detection': {
                'confidence_threshold': 0.5,
                'model_path': 'yolov8n.pt'
            },
            'tracking': {
                'track_buffer': 30,
                'match_thresh': 0.8
            }
        }
    }

@pytest.fixture(autouse=True)
def mock_environment_variables(monkeypatch):
    """Mock environment variables for testing"""
    monkeypatch.setenv("DATABASE_HOST", "localhost")
    monkeypatch.setenv("DATABASE_PORT", "5432")
    monkeypatch.setenv("DATABASE_NAME", "test_db")
    monkeypatch.setenv("DATABASE_USER", "test_user")
    monkeypatch.setenv("DATABASE_PASSWORD", "test_pass")
    monkeypatch.setenv("API_HOST", "0.0.0.0")
    monkeypatch.setenv("API_PORT", "8000")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

@pytest.fixture
def sample_detection_data():
    """Sample detection data for testing"""
    return [
        {
            'track_id': 1,
            'centroid': (100, 100),
            'timestamp': '2023-01-01T10:00:00',
            'bbox': [50, 50, 150, 150],
            'confidence': 0.9
        },
        {
            'track_id': 2,
            'centroid': (300, 200),
            'timestamp': '2023-01-01T10:00:01',
            'bbox': [250, 150, 350, 250],
            'confidence': 0.8
        }
    ]

@pytest.fixture
def sample_zone_visit_data():
    """Sample zone visit data for testing"""
    return [
        {
            'zone_name': 'material_rack',
            'track_id': 1,
            'entry_time': '2023-01-01T10:00:00',
            'exit_time': '2023-01-01T10:00:30',
            'dwell_time': 30
        },
        {
            'zone_name': 'cutting_table',
            'track_id': 1,
            'entry_time': '2023-01-01T10:01:00',
            'exit_time': '2023-01-01T10:06:00',
            'dwell_time': 300
        }
    ]
