import pytest
import numpy as np
import cv2
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.pipeline.detector import PersonDetector, MultiCameraDetector

class TestPersonDetector:
    """Test PersonDetector class"""
    
    @pytest.fixture
    def sample_frame(self):
        """Create a sample frame for testing"""
        # Create a simple test frame with a person-like shape
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Draw a rectangle to simulate a person
        cv2.rectangle(frame, (100, 100), (200, 300), (255, 255, 255), -1)
        
        return frame
    
    @pytest.fixture
    def mock_yolo_model(self):
        """Mock YOLO model"""
        mock_model = Mock()
        
        # Mock detection results
        mock_result = Mock()
        mock_result.boxes = Mock()
        mock_result.boxes.data = np.array([
            [100, 100, 200, 300, 0.9, 0]  # x1, y1, x2, y2, confidence, class_id
        ])
        
        mock_model.return_value = [mock_result]
        
        return mock_model
    
    @pytest.fixture
    def detector(self, mock_yolo_model):
        """Create detector with mocked YOLO model"""
        with patch('app.pipeline.detector.YOLO', return_value=mock_yolo_model):
            detector = PersonDetector(model_path="yolov8n.pt", device="cpu")
            return detector
    
    def test_detector_initialization(self):
        """Test detector initialization"""
        with patch('app.pipeline.detector.YOLO') as mock_yolo:
            mock_model = Mock()
            mock_yolo.return_value = mock_model
            
            detector = PersonDetector(model_path="yolov8n.pt", device="cpu")
            
            assert detector.model_path == "yolov8n.pt"
            assert detector.device == "cpu"
            assert detector.confidence_threshold == 0.5
            assert detector.person_class_id == 0
            mock_yolo.assert_called_once_with("yolov8n.pt")
    
    def test_detect_persons(self, detector, sample_frame):
        """Test person detection"""
        detections = detector.detect(sample_frame)
        
        assert detections is not None
        assert len(detections) == 1
        assert detections.confidence[0] == 0.9
    
    def test_detect_no_persons(self, detector):
        """Test detection with no persons"""
        # Create empty frame
        empty_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Mock empty detection results
        detector.model.return_value = [Mock()]
        detector.model.return_value[0].boxes.data = np.array([])
        
        detections = detector.detect(empty_frame)
        
        assert len(detections) == 0
    
    def test_detect_multiple_persons(self, detector, sample_frame):
        """Test detection with multiple persons"""
        # Mock multiple detections
        mock_result = Mock()
        mock_result.boxes.data = np.array([
            [100, 100, 200, 300, 0.9, 0],  # Person 1
            [300, 150, 400, 350, 0.8, 0],  # Person 2
            [500, 200, 600, 400, 0.7, 1]   # Non-person (class_id=1)
        ])
        
        detector.model.return_value = [mock_result]
        
        detections = detector.detect(sample_frame)
        
        # Should only detect persons (class_id=0)
        assert len(detections) == 2
        assert all(detections.class_id == 0)
    
    def test_detect_below_confidence_threshold(self, detector, sample_frame):
        """Test detection filtering by confidence threshold"""
        detector.confidence_threshold = 0.8
        
        # Mock detection with low confidence
        mock_result = Mock()
        mock_result.boxes.data = np.array([
            [100, 100, 200, 300, 0.7, 0]  # Below threshold
        ])
        
        detector.model.return_value = [mock_result]
        
        detections = detector.detect(sample_frame)
        
        assert len(detections) == 0
    
    def test_get_detection_stats(self, detector):
        """Test detection statistics calculation"""
        from supervision import Detections
        
        # Create mock detections
        detections = Detections(
            xyxy=np.array([[100, 100, 200, 300], [300, 150, 400, 350]]),
            confidence=np.array([0.9, 0.8]),
            class_id=np.array([0, 0])
        )
        
        stats = detector.get_detection_stats(detections)
        
        assert stats['num_detections'] == 2
        assert stats['avg_confidence'] == 0.85
        assert stats['min_confidence'] == 0.8
        assert stats['max_confidence'] == 0.9
    
    def test_get_detection_stats_empty(self, detector):
        """Test detection statistics with empty detections"""
        from supervision import Detections
        
        detections = Detections.empty()
        stats = detector.get_detection_stats(detections)
        
        assert stats['num_detections'] == 0
        assert stats['avg_confidence'] == 0.0
        assert stats['min_confidence'] == 0.0
        assert stats['max_confidence'] == 0.0
    
    def test_visualize_detections(self, detector, sample_frame):
        """Test detection visualization"""
        from supervision import Detections
        
        # Create mock detections
        detections = Detections(
            xyxy=np.array([[100, 100, 200, 300]]),
            confidence=np.array([0.9]),
            class_id=np.array([0])
        )
        
        annotated_frame = detector.visualize_detections(sample_frame, detections)
        
        assert annotated_frame is not None
        assert annotated_frame.shape == sample_frame.shape
        assert not np.array_equal(annotated_frame, sample_frame)  # Should be different
    
    def test_detect_batch(self, detector):
        """Test batch detection"""
        frames = [
            np.zeros((480, 640, 3), dtype=np.uint8),
            np.zeros((480, 640, 3), dtype=np.uint8)
        ]
        
        # Mock batch detection results
        mock_result1 = Mock()
        mock_result1.boxes.data = np.array([[100, 100, 200, 300, 0.9, 0]])
        
        mock_result2 = Mock()
        mock_result2.boxes.data = np.array([[150, 150, 250, 350, 0.8, 0]])
        
        detector.model.return_value = [mock_result1, mock_result2]
        
        batch_detections = detector.detect_batch(frames)
        
        assert len(batch_detections) == 2
        assert len(batch_detections[0]) == 1
        assert len(batch_detections[1]) == 1
    
    def test_detect_batch_error_handling(self, detector):
        """Test batch detection error handling"""
        frames = [np.zeros((480, 640, 3), dtype=np.uint8)]
        
        # Mock error in detection
        detector.model.side_effect = Exception("Detection error")
        
        batch_detections = detector.detect_batch(frames)
        
        assert len(batch_detections) == 1
        assert len(batch_detections[0]) == 0  # Should return empty detections

class TestMultiCameraDetector:
    """Test MultiCameraDetector class"""
    
    @pytest.fixture
    def camera_configs(self):
        """Sample camera configurations"""
        return {
            'A11': {
                'id': 'A11',
                'detection': {
                    'model_path': 'yolov8n.pt',
                    'device': 'cpu',
                    'confidence_threshold': 0.5
                }
            },
            'A12': {
                'id': 'A12',
                'detection': {
                    'model_path': 'yolov8s.pt',
                    'device': 'cpu',
                    'confidence_threshold': 0.6
                }
            }
        }
    
    @pytest.fixture
    def multi_detector(self, camera_configs):
        """Create multi-camera detector with mocked YOLO"""
        with patch('app.pipeline.detector.PersonDetector') as mock_detector_class:
            mock_detector = Mock()
            mock_detector_class.return_value = mock_detector
            
            detector = MultiCameraDetector(camera_configs)
            return detector
    
    def test_multi_detector_initialization(self, camera_configs):
        """Test multi-camera detector initialization"""
        with patch('app.pipeline.detector.PersonDetector') as mock_detector_class:
            MultiCameraDetector(camera_configs)
            
            # Should create detectors for each camera
            assert mock_detector_class.call_count == 2
            
            # Check first camera config
            call_args = mock_detector_class.call_args_list[0]
            assert call_args[1]['model_path'] == 'yolov8n.pt'
            assert call_args[1]['confidence_threshold'] == 0.5
    
    def test_detect_for_camera(self, multi_detector, camera_configs):
        """Test detection for specific camera"""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Mock detection result
        mock_detections = Mock()
        multi_detector.detectors['A11'].detect.return_value = mock_detections
        
        detections = multi_detector.detect_for_camera('A11', frame)
        
        assert detections == mock_detections
        multi_detector.detectors['A11'].detect.assert_called_once_with(frame)
    
    def test_detect_for_camera_not_found(self, multi_detector):
        """Test detection for non-existent camera"""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        detections = multi_detector.detect_for_camera('NONEXISTENT', frame)
        
        assert len(detections) == 0
    
    def test_get_detector(self, multi_detector, camera_configs):
        """Test getting detector for camera"""
        detector = multi_detector.get_detector('A11')
        
        assert detector is not None
        assert detector == multi_detector.detectors['A11']
    
    def test_get_detector_not_found(self, multi_detector):
        """Test getting detector for non-existent camera"""
        detector = multi_detector.get_detector('NONEXISTENT')
        
        assert detector is None
