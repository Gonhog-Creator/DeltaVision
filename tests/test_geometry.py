import pytest
import math
from app.utils.geometry import GeometryUtils

class TestGeometryUtils:
    """Test geometry utility functions"""
    
    def test_point_in_polygon_inside(self):
        """Test point inside polygon"""
        polygon = [(0, 0), (100, 0), (100, 100), (0, 100)]
        point = (50, 50)
        
        assert GeometryUtils.point_in_polygon(point, polygon) == True
    
    def test_point_in_polygon_outside(self):
        """Test point outside polygon"""
        polygon = [(0, 0), (100, 0), (100, 100), (0, 100)]
        point = (150, 150)
        
        assert GeometryUtils.point_in_polygon(point, polygon) == False
    
    def test_point_in_polygon_on_boundary(self):
        """Test point on polygon boundary"""
        polygon = [(0, 0), (100, 0), (100, 100), (0, 100)]
        point = (0, 50)  # On left edge
        
        assert GeometryUtils.point_in_polygon(point, polygon) == True
    
    def test_point_in_polygon_complex(self):
        """Test point in complex polygon"""
        # L-shaped polygon
        polygon = [(0, 0), (100, 0), (100, 50), (50, 50), (50, 100), (0, 100)]
        
        # Point inside L-shape
        point_inside = (25, 75)
        assert GeometryUtils.point_in_polygon(point_inside, polygon) == True
        
        # Point in cutout area
        point_cutout = (75, 75)
        assert GeometryUtils.point_in_polygon(point_cutout, polygon) == False
    
    def test_distance_point_to_point(self):
        """Test distance between two points"""
        p1 = (0, 0)
        p2 = (3, 4)
        
        distance = GeometryUtils.distance_point_to_point(p1, p2)
        assert distance == 5.0  # 3-4-5 triangle
    
    def test_distance_point_to_point_same(self):
        """Test distance between same points"""
        p1 = (10, 10)
        p2 = (10, 10)
        
        distance = GeometryUtils.distance_point_to_point(p1, p2)
        assert distance == 0.0
    
    def test_distance_point_to_line(self):
        """Test distance from point to line segment"""
        point = (0, 10)
        line_start = (0, 0)
        line_end = (10, 0)
        
        distance = GeometryUtils.distance_point_to_line(point, line_start, line_end)
        assert distance == 10.0
    
    def test_distance_point_to_line_on_line(self):
        """Test distance from point on line to line"""
        point = (5, 0)
        line_start = (0, 0)
        line_end = (10, 0)
        
        distance = GeometryUtils.distance_point_to_line(point, line_start, line_end)
        assert distance == 0.0
    
    def test_distance_point_to_line_vertical(self):
        """Test distance from point to vertical line"""
        point = (10, 5)
        line_start = (0, 0)
        line_end = (0, 10)
        
        distance = GeometryUtils.distance_point_to_line(point, line_start, line_end)
        assert distance == 10.0
    
    def test_centroid_of_polygon(self):
        """Test polygon centroid calculation"""
        polygon = [(0, 0), (100, 0), (100, 100), (0, 100)]
        centroid = GeometryUtils.centroid_of_polygon(polygon)
        
        assert centroid[0] == 50.0
        assert centroid[1] == 50.0
    
    def test_centroid_of_triangle(self):
        """Test triangle centroid calculation"""
        polygon = [(0, 0), (6, 0), (3, 6)]
        centroid = GeometryUtils.centroid_of_polygon(polygon)
        
        assert centroid[0] == 3.0
        assert centroid[1] == 2.0
    
    def test_centroid_of_insufficient_points(self):
        """Test centroid with insufficient points"""
        polygon = [(0, 0), (100, 0)]  # Only 2 points
        centroid = GeometryUtils.centroid_of_polygon(polygon)
        
        assert centroid == (0, 0)
    
    def test_area_of_polygon_square(self):
        """Test area of square"""
        polygon = [(0, 0), (100, 0), (100, 100), (0, 100)]
        area = GeometryUtils.area_of_polygon(polygon)
        
        assert area == 10000.0
    
    def test_area_of_polygon_triangle(self):
        """Test area of triangle"""
        polygon = [(0, 0), (6, 0), (3, 6)]
        area = GeometryUtils.area_of_polygon(polygon)
        
        assert area == 18.0  # (6 * 6) / 2
    
    def test_area_of_polygon_insufficient_points(self):
        """Test area with insufficient points"""
        polygon = [(0, 0), (100, 0)]  # Only 2 points
        area = GeometryUtils.area_of_polygon(polygon)
        
        assert area == 0.0
    
    def test_perimeter_of_polygon_square(self):
        """Test perimeter of square"""
        polygon = [(0, 0), (100, 0), (100, 100), (0, 100)]
        perimeter = GeometryUtils.perimeter_of_polygon(polygon)
        
        assert perimeter == 400.0
    
    def test_perimeter_of_polygon_triangle(self):
        """Test perimeter of triangle"""
        polygon = [(0, 0), (3, 0), (0, 4)]
        perimeter = GeometryUtils.perimeter_of_polygon(polygon)
        
        assert perimeter == 12.0  # 3 + 4 + 5
    
    def test_perimeter_of_polygon_insufficient_points(self):
        """Test perimeter with insufficient points"""
        polygon = [(0, 0)]  # Only 1 point
        perimeter = GeometryUtils.perimeter_of_polygon(polygon)
        
        assert perimeter == 0.0
    
    def test_bounding_box_of_polygon(self):
        """Test bounding box calculation"""
        polygon = [(-10, -5), (20, 15), (30, -10), (5, 25)]
        min_point, max_point = GeometryUtils.bounding_box_of_polygon(polygon)
        
        assert min_point == (-10, -10)
        assert max_point == (30, 25)
    
    def test_bounding_box_of_empty_polygon(self):
        """Test bounding box of empty polygon"""
        polygon = []
        min_point, max_point = GeometryUtils.bounding_box_of_polygon(polygon)
        
        assert min_point == (0, 0)
        assert max_point == (0, 0)
    
    def test_angle_between_points(self):
        """Test angle calculation between three points"""
        p1 = (0, 0)
        p2 = (1, 0)  # Vertex
        p3 = (1, 1)
        
        angle = GeometryUtils.angle_between_points(p1, p2, p3)
        assert abs(angle - 90.0) < 0.1  # 90 degree angle
    
    def test_angle_between_points_straight_line(self):
        """Test angle for straight line"""
        p1 = (0, 0)
        p2 = (1, 0)  # Vertex
        p3 = (2, 0)
        
        angle = GeometryUtils.angle_between_points(p1, p2, p3)
        assert abs(angle - 180.0) < 0.1  # 180 degree angle
    
    def test_angle_between_points_zero_angle(self):
        """Test zero angle"""
        p1 = (0, 0)
        p2 = (1, 1)  # Vertex
        p3 = (2, 2)
        
        angle = GeometryUtils.angle_between_points(p1, p2, p3)
        assert abs(angle - 0.0) < 0.1  # 0 degree angle
    
    def test_rotate_point(self):
        """Test point rotation"""
        point = (1, 0)
        center = (0, 0)
        angle = 90.0
        
        rotated = GeometryUtils.rotate_point(point, center, angle)
        
        assert abs(rotated[0] - 0.0) < 0.1  # Should be near 0
        assert abs(rotated[1] - 1.0) < 0.1  # Should be near 1
    
    def test_rotate_point_45_degrees(self):
        """Test point rotation by 45 degrees"""
        point = (1, 0)
        center = (0, 0)
        angle = 45.0
        
        rotated = GeometryUtils.rotate_point(point, center, angle)
        
        # Should be at (cos(45), sin(45))
        expected_x = math.cos(math.radians(45))
        expected_y = math.sin(math.radians(45))
        
        assert abs(rotated[0] - expected_x) < 0.1
        assert abs(rotated[1] - expected_y) < 0.1
    
    def test_scale_point(self):
        """Test point scaling"""
        point = (10, 20)
        center = (0, 0)
        scale_factor = 2.0
        
        scaled = GeometryUtils.scale_point(point, center, scale_factor)
        
        assert scaled == (20, 40)
    
    def test_scale_point_with_offset_center(self):
        """Test point scaling with offset center"""
        point = (15, 25)
        center = (5, 5)
        scale_factor = 2.0
        
        scaled = GeometryUtils.scale_point(point, center, scale_factor)
        
        # Translate to origin: (10, 20), scale: (20, 40), translate back: (25, 45)
        assert scaled == (25, 45)
    
    def test_interpolate_points(self):
        """Test point interpolation"""
        p1 = (0, 0)
        p2 = (10, 10)
        t = 0.5  # Midpoint
        
        interpolated = GeometryUtils.interpolate_points(p1, p2, t)
        
        assert interpolated == (5, 5)
    
    def test_interpolate_points_zero(self):
        """Test interpolation at t=0"""
        p1 = (5, 10)
        p2 = (15, 20)
        t = 0.0
        
        interpolated = GeometryUtils.interpolate_points(p1, p2, t)
        
        assert interpolated == p1
    
    def test_interpolate_points_one(self):
        """Test interpolation at t=1"""
        p1 = (5, 10)
        p2 = (15, 20)
        t = 1.0
        
        interpolated = GeometryUtils.interpolate_points(p1, p2, t)
        
        assert interpolated == p2
    
    def test_smooth_path(self):
        """Test path smoothing"""
        path = [(0, 0), (10, 0), (20, 0), (30, 0)]
        smoothed = GeometryUtils.smooth_path(path, window_size=3)
        
        # Should be very close to original for straight line
        assert len(smoothed) == len(path)
        for original, smoothed_point in zip(path, smoothed):
            assert abs(original[0] - smoothed_point[0]) < 0.1
            assert abs(original[1] - smoothed_point[1]) < 0.1
    
    def test_smooth_path_short(self):
        """Test smoothing short path"""
        path = [(0, 0), (10, 0)]
        smoothed = GeometryUtils.smooth_path(path, window_size=3)
        
        assert smoothed == path  # Should return unchanged
    
    def test_calculate_path_length(self):
        """Test path length calculation"""
        path = [(0, 0), (3, 4), (6, 4)]
        length = GeometryUtils.calculate_path_length(path)
        
        # Distance from (0,0) to (3,4) = 5
        # Distance from (3,4) to (6,4) = 3
        # Total = 8
        assert abs(length - 8.0) < 0.1
    
    def test_calculate_path_length_single_point(self):
        """Test path length with single point"""
        path = [(5, 5)]
        length = GeometryUtils.calculate_path_length(path)
        
        assert length == 0.0
    
    def test_calculate_path_length_empty(self):
        """Test path length with empty path"""
        path = []
        length = GeometryUtils.calculate_path_length(path)
        
        assert length == 0.0
    
    def test_find_closest_point_on_path(self):
        """Test finding closest point on path"""
        path = [(0, 0), (10, 0), (10, 10)]
        point = (5, 5)
        
        closest_point, distance = GeometryUtils.find_closest_point_on_path(point, path)
        
        # Should be closest to the line from (10,0) to (10,10)
        assert closest_point[0] == 10.0
        assert abs(closest_point[1] - 5.0) < 0.1
        assert distance == 5.0
    
    def test_find_closest_point_on_path_empty(self):
        """Test finding closest point on empty path"""
        path = []
        point = (5, 5)
        
        closest_point, distance = GeometryUtils.find_closest_point_on_path(point, path)
        
        assert closest_point == point
        assert distance == float('inf')
    
    def test_point_to_bounding_box_distance_inside(self):
        """Test distance to bounding box when point is inside"""
        point = (5, 5)
        bbox_min = (0, 0)
        bbox_max = (10, 10)
        
        distance = GeometryUtils.point_to_bounding_box_distance(point, bbox_min, bbox_max)
        
        assert distance == 0.0
    
    def test_point_to_bounding_box_distance_outside(self):
        """Test distance to bounding box when point is outside"""
        point = (15, 15)
        bbox_min = (0, 0)
        bbox_max = (10, 10)
        
        distance = GeometryUtils.point_to_bounding_box_distance(point, bbox_min, bbox_max)
        
        # Distance from (15,15) to (10,10) = sqrt(5^2 + 5^2) = sqrt(50)
        expected = math.sqrt(50)
        assert abs(distance - expected) < 0.1
