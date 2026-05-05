import pytest
import numpy as np
from datetime import datetime
from shapely.geometry import Point, Polygon

from app.pipeline.zones import Zone, ZoneManager

class TestZone:
    """Test Zone class"""
    
    @pytest.fixture
    def sample_zone(self):
        """Create a sample zone"""
        polygon = Polygon([[0, 0], [100, 0], [100, 100], [0, 100]])
        return Zone(
            name="test_zone",
            description="Test zone for unit testing",
            polygon=polygon,
            zone_type="workstation",
            expected_dwell_time=300,
            camera_id="A11"
        )
    
    def test_zone_creation(self, sample_zone):
        """Test zone creation"""
        assert sample_zone.name == "test_zone"
        assert sample_zone.zone_type == "workstation"
        assert sample_zone.expected_dwell_time == 300
        assert sample_zone.camera_id == "A11"
    
    def test_contains_point_inside(self, sample_zone):
        """Test point inside zone"""
        point = (50, 50)
        assert sample_zone.contains_point(point) == True
    
    def test_contains_point_outside(self, sample_zone):
        """Test point outside zone"""
        point = (150, 150)
        assert sample_zone.contains_point(point) == False
    
    def test_contains_point_on_boundary(self, sample_zone):
        """Test point on zone boundary"""
        point = (0, 50)  # On left edge
        assert sample_zone.contains_point(point) == True
    
    def test_get_area(self, sample_zone):
        """Test zone area calculation"""
        area = sample_zone.get_area()
        assert area == 10000  # 100x100 square
    
    def test_get_centroid(self, sample_zone):
        """Test zone centroid calculation"""
        centroid = sample_zone.get_centroid()
        assert centroid[0] == 50  # Center of 0-100 range
        assert centroid[1] == 50

class TestZoneManager:
    """Test ZoneManager class"""
    
    @pytest.fixture
    def zones_config(self):
        """Sample zones configuration"""
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
            ],
            'A12': [
                {
                    'name': 'inspection',
                    'description': 'Quality inspection area',
                    'polygon': [[0, 0], [150, 0], [150, 150], [0, 150]],
                    'type': 'quality_control',
                    'expected_dwell_time': 180
                }
            ]
        }
    
    @pytest.fixture
    def zone_manager(self, zones_config):
        """Create zone manager with test configuration"""
        return ZoneManager(zones_config)
    
    def test_zone_manager_initialization(self, zone_manager):
        """Test zone manager initialization"""
        assert len(zone_manager.zones) == 3
        assert len(zone_manager.zones_by_camera) == 2
        assert 'A11' in zone_manager.zones_by_camera
        assert 'A12' in zone_manager.zones_by_camera
        assert len(zone_manager.zones_by_camera['A11']) == 2
        assert len(zone_manager.zones_by_camera['A12']) == 1
    
    def test_get_zone_for_point(self, zone_manager):
        """Test getting zone for point"""
        # Point in material_rack
        point_in_rack = (100, 100)
        zone = zone_manager.get_zone_for_point(point_in_rack, 'A11')
        assert zone is not None
        assert zone.name == 'material_rack'
        
        # Point in cutting_table
        point_in_cutting = (350, 100)
        zone = zone_manager.get_zone_for_point(point_in_cutting, 'A11')
        assert zone is not None
        assert zone.name == 'cutting_table'
        
        # Point not in any zone
        point_outside = (500, 500)
        zone = zone_manager.get_zone_for_point(point_outside, 'A11')
        assert zone is None
    
    def test_get_zone_for_point_wrong_camera(self, zone_manager):
        """Test getting zone for point with wrong camera"""
        point = (100, 100)  # This is in A11's material_rack
        zone = zone_manager.get_zone_for_point(point, 'A12')
        assert zone is None
    
    def test_get_zones_for_camera(self, zone_manager):
        """Test getting zones for camera"""
        zones_a11 = zone_manager.get_zones_for_camera('A11')
        assert len(zones_a11) == 2
        zone_names = [z.name for z in zones_a11]
        assert 'material_rack' in zone_names
        assert 'cutting_table' in zone_names
        
        zones_a12 = zone_manager.get_zones_for_camera('A12')
        assert len(zones_a12) == 1
        assert zones_a12[0].name == 'inspection'
        
        zones_nonexistent = zone_manager.get_zones_for_camera('NONEXISTENT')
        assert zones_nonexistent == []
    
    def test_get_zone_by_name(self, zone_manager):
        """Test getting zone by name"""
        zone = zone_manager.get_zone_by_name('material_rack')
        assert zone is not None
        assert zone.zone_type == 'storage'
        assert zone.expected_dwell_time == 30
        
        zone = zone_manager.get_zone_by_name('NONEXISTENT')
        assert zone is None
    
    def test_get_zones_by_type(self, zone_manager):
        """Test getting zones by type"""
        storage_zones = zone_manager.get_zones_by_type('storage')
        assert len(storage_zones) == 1
        assert storage_zones[0].name == 'material_rack'
        
        workstation_zones = zone_manager.get_zones_by_type('workstation')
        assert len(workstation_zones) == 1
        assert workstation_zones[0].name == 'cutting_table'
        
        quality_zones = zone_manager.get_zones_by_type('quality_control')
        assert len(quality_zones) == 1
        assert quality_zones[0].name == 'inspection'
        
        nonexistent_zones = zone_manager.get_zones_by_type('NONEXISTENT')
        assert len(nonexistent_zones) == 0
    
    def test_calculate_zone_occupancy(self, zone_manager):
        """Test zone occupancy calculation"""
        tracks = [
            {'track_id': 1, 'centroid': (100, 100)},  # material_rack
            {'track_id': 2, 'centroid': (350, 100)},  # cutting_table
            {'track_id': 3, 'centroid': (75, 75)},   # material_rack
            {'track_id': 4, 'centroid': (500, 500)}   # not in any zone
        ]
        
        occupancy = zone_manager.calculate_zone_occupancy(tracks, 'A11')
        
        assert occupancy['material_rack'] == 2
        assert occupancy['cutting_table'] == 1
        assert len(occupancy) == 2  # Only zones with occupants
    
    def test_calculate_dwell_times(self, zone_manager):
        """Test dwell time calculation"""
        track_history = [
            {'timestamp': datetime(2023, 1, 1, 10, 0, 0), 'centroid': (100, 100)},  # material_rack
            {'timestamp': datetime(2023, 1, 1, 10, 1, 0), 'centroid': (100, 100)},  # material_rack
            {'timestamp': datetime(2023, 1, 1, 10, 2, 0), 'centroid': (350, 100)},  # cutting_table
            {'timestamp': datetime(2023, 1, 1, 10, 3, 0), 'centroid': (350, 100)},  # cutting_table
        ]
        
        dwell_times = zone_manager.calculate_dwell_times(track_history, 'A11')
        
        assert 'material_rack' in dwell_times
        assert 'cutting_table' in dwell_times
        assert dwell_times['material_rack'] == 120  # 2 minutes
        assert dwell_times['cutting_table'] == 120   # 2 minutes
    
    def test_detect_bottlenecks(self, zone_manager):
        """Test bottleneck detection"""
        occupancy_data = {
            'material_rack': [1, 2, 1, 3, 2],  # Expected capacity ~2
            'cutting_table': [4, 5, 6, 4, 5]   # Expected capacity ~3
        }
        
        bottlenecks = zone_manager.detect_bottlenecks(occupancy_data, threshold_multiplier=1.5)
        
        # cutting_table should be detected as bottleneck (avg 4.8 > 3 * 1.5 = 4.5)
        bottleneck_zones = [b['zone_name'] for b in bottlenecks]
        assert 'cutting_table' in bottleneck_zones
    
    def test_calculate_flow_metrics(self, zone_manager):
        """Test flow metrics calculation"""
        transitions = [
            {'from_zone': 'material_rack', 'to_zone': 'cutting_table', 'transition_time': 30},
            {'from_zone': 'material_rack', 'to_zone': 'cutting_table', 'transition_time': 45},
            {'from_zone': 'cutting_table', 'to_zone': 'inspection', 'transition_time': 60}
        ]
        
        flow_metrics = zone_manager.calculate_flow_metrics(transitions)
        
        assert 'material_rack->cutting_table' in flow_metrics
        assert 'cutting_table->inspection' in flow_metrics
        
        material_to_cutting = flow_metrics['material_rack->cutting_table']
        assert material_to_cutting['count'] == 2
        assert material_to_cutting['avg_transition_time'] == 37.5  # (30 + 45) / 2
    
    def test_get_zone_statistics(self, zone_manager):
        """Test zone statistics"""
        stats = zone_manager.get_zone_statistics()
        
        assert len(stats) == 3
        assert 'material_rack' in stats
        assert 'cutting_table' in stats
        assert 'inspection' in stats
        
        material_stats = stats['material_rack']
        assert material_stats['type'] == 'storage'
        assert material_stats['expected_dwell_time'] == 30
        assert material_stats['camera_id'] == 'A11'
        assert material_stats['area'] == 40000  # 200x200 square
    
    def test_invalid_polygon_in_config(self):
        """Test handling of invalid polygon in configuration"""
        invalid_config = {
            'A11': [
                {
                    'name': 'invalid_zone',
                    'description': 'Zone with invalid polygon',
                    'polygon': [[0, 0], [100, 0]],  # Invalid polygon (only 2 points)
                    'type': 'workstation',
                    'expected_dwell_time': 300
                }
            ]
        }
        
        # Should handle invalid polygon gracefully
        zone_manager = ZoneManager(invalid_config)
        assert len(zone_manager.zones) == 0  # Invalid zone should not be loaded
    
    def test_missing_required_fields(self):
        """Test handling of missing required fields"""
        incomplete_config = {
            'A11': [
                {
                    'name': 'incomplete_zone',
                    # Missing description, polygon, type, expected_dwell_time
                }
            ]
        }
        
        zone_manager = ZoneManager(incomplete_config)
        # Should use default values for missing fields
        zone = zone_manager.get_zone_by_name('incomplete_zone')
        if zone:  # Only test if zone was created
            assert zone.expected_dwell_time == 60  # Default value
