import numpy as np
from typing import List, Tuple, Optional
from shapely.geometry import Point, Polygon, LineString
import math

class GeometryUtils:
    """Utility functions for geometric calculations"""
    
    @staticmethod
    def point_in_polygon(point: Tuple[float, float], polygon: List[Tuple[float, float]]) -> bool:
        """Check if point is inside polygon using ray casting algorithm"""
        x, y = point
        n = len(polygon)
        inside = False
        
        j = n - 1
        for i in range(n):
            xi, yi = polygon[i]
            xj, yj = polygon[j]
            
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            
            j = i
        
        return inside
    
    @staticmethod
    def distance_point_to_point(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance between two points"""
        return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
    
    @staticmethod
    def distance_point_to_line(point: Tuple[float, float], line_start: Tuple[float, float], 
                             line_end: Tuple[float, float]) -> float:
        """Calculate distance from point to line segment"""
        x0, y0 = point
        x1, y1 = line_start
        x2, y2 = line_end
        
        # Calculate line length
        line_length = GeometryUtils.distance_point_to_point(line_start, line_end)
        
        if line_length == 0:
            return GeometryUtils.distance_point_to_point(point, line_start)
        
        # Calculate projection
        t = max(0, min(1, ((x0 - x1) * (x2 - x1) + (y0 - y1) * (y2 - y1)) / line_length**2))
        
        # Find projection point
        projection = (x1 + t * (x2 - x1), y1 + t * (y2 - y1))
        
        return GeometryUtils.distance_point_to_point(point, projection)
    
    @staticmethod
    def centroid_of_polygon(polygon: List[Tuple[float, float]]) -> Tuple[float, float]:
        """Calculate centroid of polygon"""
        if len(polygon) < 3:
            return (0, 0)
        
        x_coords = [p[0] for p in polygon]
        y_coords = [p[1] for p in polygon]
        
        centroid_x = sum(x_coords) / len(x_coords)
        centroid_y = sum(y_coords) / len(y_coords)
        
        return (centroid_x, centroid_y)
    
    @staticmethod
    def area_of_polygon(polygon: List[Tuple[float, float]]) -> float:
        """Calculate area of polygon using shoelace formula"""
        if len(polygon) < 3:
            return 0.0
        
        area = 0.0
        n = len(polygon)
        
        for i in range(n):
            j = (i + 1) % n
            area += polygon[i][0] * polygon[j][1]
            area -= polygon[j][0] * polygon[i][1]
        
        return abs(area) / 2.0
    
    @staticmethod
    def perimeter_of_polygon(polygon: List[Tuple[float, float]]) -> float:
        """Calculate perimeter of polygon"""
        if len(polygon) < 2:
            return 0.0
        
        perimeter = 0.0
        n = len(polygon)
        
        for i in range(n):
            j = (i + 1) % n
            perimeter += GeometryUtils.distance_point_to_point(polygon[i], polygon[j])
        
        return perimeter
    
    @staticmethod
    def bounding_box_of_polygon(polygon: List[Tuple[float, float]]) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """Get bounding box of polygon (min_point, max_point)"""
        if not polygon:
            return ((0, 0), (0, 0))
        
        x_coords = [p[0] for p in polygon]
        y_coords = [p[1] for p in polygon]
        
        min_point = (min(x_coords), min(y_coords))
        max_point = (max(x_coords), max(y_coords))
        
        return (min_point, max_point)
    
    @staticmethod
    def polygon_intersection(poly1: List[Tuple[float, float]], poly2: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Find intersection of two polygons"""
        try:
            polygon1 = Polygon(poly1)
            polygon2 = Polygon(poly2)
            
            intersection = polygon1.intersection(polygon2)
            
            if intersection.is_empty:
                return []
            
            if isinstance(intersection, Polygon):
                return list(intersection.exterior.coords)
            elif hasattr(intersection, 'geoms'):
                # Multiple intersection polygons
                result = []
                for geom in intersection.geoms:
                    if isinstance(geom, Polygon):
                        result.extend(list(geom.exterior.coords))
                return result
            else:
                return []
                
        except Exception:
            return []
    
    @staticmethod
    def polygon_union(poly1: List[Tuple[float, float]], poly2: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Find union of two polygons"""
        try:
            polygon1 = Polygon(poly1)
            polygon2 = Polygon(poly2)
            
            union = polygon1.union(polygon2)
            
            if union.is_empty:
                return []
            
            if isinstance(union, Polygon):
                return list(union.exterior.coords)
            elif hasattr(union, 'geoms'):
                result = []
                for geom in union.geoms:
                    if isinstance(geom, Polygon):
                        result.extend(list(geom.exterior.coords))
                return result
            else:
                return []
                
        except Exception:
            return []
    
    @staticmethod
    def simplify_polygon(polygon: List[Tuple[float, float]], tolerance: float = 1.0) -> List[Tuple[float, float]]:
        """Simplify polygon using Douglas-Peucker algorithm"""
        if len(polygon) < 3:
            return polygon
        
        try:
            shapely_polygon = Polygon(polygon)
            simplified = shapely_polygon.simplify(tolerance, preserve_topology=True)
            
            if simplified.is_empty:
                return polygon
            
            return list(simplified.exterior.coords)
            
        except Exception:
            return polygon
    
    @staticmethod
    def point_to_bounding_box_distance(point: Tuple[float, float], 
                                    bbox_min: Tuple[float, float], 
                                    bbox_max: Tuple[float, float]) -> float:
        """Calculate distance from point to bounding box"""
        x, y = point
        min_x, min_y = bbox_min
        max_x, max_y = bbox_max
        
        # Point is inside bounding box
        if min_x <= x <= max_x and min_y <= y <= max_y:
            return 0.0
        
        # Calculate distance to closest edge
        dx = max(min_x - x, 0, x - max_x)
        dy = max(min_y - y, 0, y - max_y)
        
        return math.sqrt(dx**2 + dy**2)
    
    @staticmethod
    def angle_between_points(p1: Tuple[float, float], p2: Tuple[float, float], 
                           p3: Tuple[float, float]) -> float:
        """Calculate angle between three points (p1-p2-p3) in degrees"""
        # Vectors from p2 to p1 and p2 to p3
        v1 = (p1[0] - p2[0], p1[1] - p2[1])
        v2 = (p3[0] - p2[0], p3[1] - p2[1])
        
        # Calculate angle using dot product
        dot_product = v1[0] * v2[0] + v1[1] * v2[1]
        magnitude1 = math.sqrt(v1[0]**2 + v1[1]**2)
        magnitude2 = math.sqrt(v2[0]**2 + v2[1]**2)
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        cos_angle = dot_product / (magnitude1 * magnitude2)
        cos_angle = max(-1.0, min(1.0, cos_angle))  # Clamp to [-1, 1]
        
        angle_rad = math.acos(cos_angle)
        angle_deg = math.degrees(angle_rad)
        
        return angle_deg
    
    @staticmethod
    def rotate_point(point: Tuple[float, float], center: Tuple[float, float], angle_degrees: float) -> Tuple[float, float]:
        """Rotate point around center by given angle"""
        x, y = point
        cx, cy = center
        
        # Convert angle to radians
        angle_rad = math.radians(angle_degrees)
        
        # Translate to origin
        x_translated = x - cx
        y_translated = y - cy
        
        # Rotate
        x_rotated = x_translated * math.cos(angle_rad) - y_translated * math.sin(angle_rad)
        y_rotated = x_translated * math.sin(angle_rad) + y_translated * math.cos(angle_rad)
        
        # Translate back
        x_final = x_rotated + cx
        y_final = y_rotated + cy
        
        return (x_final, y_final)
    
    @staticmethod
    def scale_point(point: Tuple[float, float], center: Tuple[float, float], scale_factor: float) -> Tuple[float, float]:
        """Scale point relative to center"""
        x, y = point
        cx, cy = center
        
        # Translate to origin
        x_translated = x - cx
        y_translated = y - cy
        
        # Scale
        x_scaled = x_translated * scale_factor
        y_scaled = y_translated * scale_factor
        
        # Translate back
        x_final = x_scaled + cx
        y_final = y_scaled + cy
        
        return (x_final, y_final)
    
    @staticmethod
    def interpolate_points(p1: Tuple[float, float], p2: Tuple[float, float], t: float) -> Tuple[float, float]:
        """Linear interpolation between two points (t in [0, 1])"""
        x = p1[0] + t * (p2[0] - p1[0])
        y = p1[1] + t * (p2[1] - p1[1])
        return (x, y)
    
    @staticmethod
    def smooth_path(points: List[Tuple[float, float]], window_size: int = 3) -> List[Tuple[float, float]]:
        """Apply moving average smoothing to path"""
        if len(points) < window_size:
            return points
        
        smoothed = []
        half_window = window_size // 2
        
        for i in range(len(points)):
            start_idx = max(0, i - half_window)
            end_idx = min(len(points), i + half_window + 1)
            
            window_points = points[start_idx:end_idx]
            avg_x = sum(p[0] for p in window_points) / len(window_points)
            avg_y = sum(p[1] for p in window_points) / len(window_points)
            
            smoothed.append((avg_x, avg_y))
        
        return smoothed
    
    @staticmethod
    def calculate_path_length(path: List[Tuple[float, float]]) -> float:
        """Calculate total length of path"""
        if len(path) < 2:
            return 0.0
        
        total_length = 0.0
        for i in range(1, len(path)):
            total_length += GeometryUtils.distance_point_to_point(path[i-1], path[i])
        
        return total_length
    
    @staticmethod
    def find_closest_point_on_path(point: Tuple[float, float], path: List[Tuple[float, float]]) -> Tuple[Tuple[float, float], float]:
        """Find closest point on path to given point and return distance"""
        if not path:
            return point, float('inf')
        
        min_distance = float('inf')
        closest_point = path[0]
        
        for i in range(len(path) - 1):
            # Check distance to line segment
            dist_to_segment = GeometryUtils.distance_point_to_line(point, path[i], path[i+1])
            
            if dist_to_segment < min_distance:
                min_distance = dist_to_segment
                
                # Find actual closest point on segment
                t = max(0, min(1, ((point[0] - path[i][0]) * (path[i+1][0] - path[i][0]) + 
                                  (point[1] - path[i][1]) * (path[i+1][1] - path[i][1])) / 
                         GeometryUtils.distance_point_to_point(path[i], path[i+1])**2)
                
                closest_point = GeometryUtils.interpolate_points(path[i], path[i+1], t)
        
        # Also check distance to vertices
        for path_point in path:
            dist = GeometryUtils.distance_point_to_point(point, path_point)
            if dist < min_distance:
                min_distance = dist
                closest_point = path_point
        
        return closest_point, min_distance
