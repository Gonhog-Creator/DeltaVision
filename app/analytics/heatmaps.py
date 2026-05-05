import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from scipy.ndimage import gaussian_filter

logger = logging.getLogger(__name__)

class HeatmapAnalyzer:
    """Generate and analyze heatmaps for factory analytics"""
    
    def __init__(self, resolution: int = 50):
        self.resolution = resolution
        
    def create_position_heatmap(self, positions: List[Tuple[float, float]], 
                               width: int, height: int, 
                               title: str = "Worker Position Heatmap") -> go.Figure:
        """Create position density heatmap"""
        if not positions:
            return go.Figure()
        
        # Create 2D histogram
        x_coords = [pos[0] for pos in positions]
        y_coords = [pos[1] for pos in positions]
        
        # Calculate histogram
        hist, xedges, yedges = np.histogram2d(
            x_coords, y_coords, 
            bins=self.resolution,
            range=[[0, width], [0, height]]
        )
        
        # Apply Gaussian smoothing for better visualization
        hist_smooth = gaussian_filter(hist, sigma=1.5)
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=hist_smooth,
            x=xedges[:-1],
            y=yedges[:-1],
            colorscale='YlOrRd',
            colorbar=dict(title="Density"),
            hovertemplate='X: %{x:.0f}<br>Y: %{y:.0f}<br>Density: %{z:.1f}<extra></extra>'
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title="X Position",
            yaxis_title="Y Position",
            width=800,
            height=600
        )
        
        # Set aspect ratio
        fig.update_yaxes(scaleanchor="x", scaleratio=height/width)
        
        return fig
    
    def create_time_based_heatmap(self, time_positions: Dict[datetime, List[Tuple[float, float]]],
                                  width: int, height: int,
                                  time_window: timedelta = timedelta(hours=1)) -> go.Figure:
        """Create animated heatmap showing position changes over time"""
        if not time_positions:
            return go.Figure()
        
        # Sort timestamps
        sorted_times = sorted(time_positions.keys())
        
        # Create frames for animation
        frames = []
        for i, timestamp in enumerate(sorted_times):
            positions = time_positions[timestamp]
            
            if positions:
                x_coords = [pos[0] for pos in positions]
                y_coords = [pos[1] for pos in positions]
                
                hist, xedges, yedges = np.histogram2d(
                    x_coords, y_coords,
                    bins=self.resolution,
                    range=[[0, width], [0, height]]
                )
                
                hist_smooth = gaussian_filter(hist, sigma=1.5)
                
                frame = go.Frame(
                    data=[go.Heatmap(
                        z=hist_smooth,
                        x=xedges[:-1],
                        y=yedges[:-1],
                        colorscale='YlOrRd',
                        colorbar=dict(title="Density")
                    )],
                    name=timestamp.strftime('%H:%M:%S')
                )
                frames.append(frame)
        
        # Create figure with animation
        fig = go.Figure(
            data=frames[0].data if frames else [],
            frames=frames
        )
        
        fig.update_layout(
            title="Worker Position Heatmap Over Time",
            xaxis_title="X Position",
            yaxis_title="Y Position",
            width=800,
            height=600,
            updatemenus=[{
                'type': 'buttons',
                'buttons': [
                    {
                        'label': 'Play',
                        'method': 'animate',
                        'args': [None, {'frame': {'duration': 500, 'redraw': True}}]
                    },
                    {
                        'label': 'Pause',
                        'method': 'animate',
                        'args': [[None], {'frame': {'duration': 0, 'redraw': False}}]
                    }
                ]
            }]
        )
        
        fig.update_yaxes(scaleanchor="x", scaleratio=height/width)
        
        return fig
    
    def create_zone_activity_heatmap(self, zone_data: Dict[str, Dict],
                                   width: int, height: int) -> go.Figure:
        """Create heatmap showing zone activity levels"""
        if not zone_data:
            return go.Figure()
        
        # Create grid for heatmap
        grid = np.zeros((self.resolution, self.resolution))
        
        # Map zone data to grid (simplified approach)
        for zone_name, data in zone_data.items():
            activity_level = data.get('activity_level', 0)
            
            # This would need actual zone polygons to map properly
            # For now, using a simplified approach
            center_x = data.get('center_x', width // 2)
            center_y = data.get('center_y', height // 2)
            
            # Add activity to nearby grid cells
            grid_x = int(center_x * self.resolution / width)
            grid_y = int(center_y * self.resolution / height)
            
            if 0 <= grid_x < self.resolution and 0 <= grid_y < self.resolution:
                grid[grid_y, grid_x] += activity_level
        
        # Apply smoothing
        grid_smooth = gaussian_filter(grid, sigma=2.0)
        
        fig = go.Figure(data=go.Heatmap(
            z=grid_smooth,
            colorscale='Viridis',
            colorbar=dict(title="Activity Level"),
            hovertemplate='Activity: %{z:.1f}<extra></extra>'
        ))
        
        fig.update_layout(
            title="Zone Activity Heatmap",
            xaxis_title="X Position",
            yaxis_title="Y Position",
            width=800,
            height=600
        )
        
        return fig
    
    def create_velocity_heatmap(self, position_velocity_data: List[Tuple[Tuple[float, float], float]],
                              width: int, height: int) -> go.Figure:
        """Create heatmap showing movement velocities"""
        if not position_velocity_data:
            return go.Figure()
        
        # Create grid for velocity data
        velocity_grid = np.zeros((self.resolution, self.resolution))
        count_grid = np.zeros((self.resolution, self.resolution))
        
        for (x, y), velocity in position_velocity_data:
            grid_x = int(x * self.resolution / width)
            grid_y = int(y * self.resolution / height)
            
            if 0 <= grid_x < self.resolution and 0 <= grid_y < self.resolution:
                velocity_grid[grid_y, grid_x] += velocity
                count_grid[grid_y, grid_x] += 1
        
        # Calculate average velocity
        avg_velocity_grid = np.divide(velocity_grid, count_grid, 
                                     where=count_grid > 0,
                                     out=np.zeros_like(velocity_grid))
        
        # Apply smoothing
        smooth_grid = gaussian_filter(avg_velocity_grid, sigma=1.5)
        
        fig = go.Figure(data=go.Heatmap(
            z=smooth_grid,
            colorscale='Plasma',
            colorbar=dict(title="Average Velocity"),
            hovertemplate='Velocity: %{z:.1f}<extra></extra>'
        ))
        
        fig.update_layout(
            title="Movement Velocity Heatmap",
            xaxis_title="X Position",
            yaxis_title="Y Position",
            width=800,
            height=600
        )
        
        return fig
    
    def analyze_hotspots(self, positions: List[Tuple[float, float]], 
                        width: int, height: int,
                        threshold_percentile: float = 90) -> List[Dict]:
        """Identify hotspot areas with high activity"""
        if not positions:
            return []
        
        # Create density map
        x_coords = [pos[0] for pos in positions]
        y_coords = [pos[1] for pos in positions]
        
        hist, xedges, yedges = np.histogram2d(
            x_coords, y_coords,
            bins=self.resolution,
            range=[[0, width], [0, height]]
        )
        
        # Find threshold
        threshold = np.percentile(hist[hist > 0], threshold_percentile)
        
        # Find hotspots
        hotspots = []
        for i in range(hist.shape[0]):
            for j in range(hist.shape[1]):
                if hist[i, j] >= threshold:
                    hotspot = {
                        'x_center': (xedges[j] + xedges[j+1]) / 2,
                        'y_center': (yedges[i] + yedges[i+1]) / 2,
                        'intensity': hist[i, j],
                        'x_range': (xedges[j], xedges[j+1]),
                        'y_range': (yedges[i], yedges[i+1])
                    }
                    hotspots.append(hotspot)
        
        # Sort by intensity
        hotspots.sort(key=lambda x: x['intensity'], reverse=True)
        
        return hotspots
    
    def create_comparison_heatmap(self, position_sets: Dict[str, List[Tuple[float, float]]],
                                width: int, height: int) -> go.Figure:
        """Create comparison heatmap for multiple time periods or conditions"""
        if not position_sets:
            return go.Figure()
        
        fig = make_subplots(
            rows=1, cols=len(position_sets),
            subplot_titles=list(position_sets.keys()),
            specs=[[{"type": "heatmap"} for _ in position_sets]]
        )
        
        for i, (label, positions) in enumerate(position_sets.items()):
            if positions:
                x_coords = [pos[0] for pos in positions]
                y_coords = [pos[1] for pos in positions]
                
                hist, xedges, yedges = np.histogram2d(
                    x_coords, y_coords,
                    bins=self.resolution,
                    range=[[0, width], [0, height]]
                )
                
                hist_smooth = gaussian_filter(hist, sigma=1.5)
                
                fig.add_trace(
                    go.Heatmap(
                        z=hist_smooth,
                        x=xedges[:-1],
                        y=yedges[:-1],
                        colorscale='YlOrRd',
                        name=label,
                        showscale=(i == 0)  # Only show colorbar for first subplot
                    ),
                    row=1, col=i+1
                )
        
        fig.update_layout(
            title="Position Heatmap Comparison",
            width=400 * len(position_sets),
            height=600
        )
        
        return fig

class HeatmapExporter:
    """Export heatmaps to various formats"""
    
    def __init__(self, output_dir: str = "data/exports"):
        self.output_dir = output_dir
    
    def export_to_html(self, fig: go.Figure, filename: str) -> str:
        """Export heatmap as HTML file"""
        import os
        os.makedirs(self.output_dir, exist_ok=True)
        
        filepath = os.path.join(self.output_dir, f"{filename}.html")
        fig.write_html(filepath)
        
        logger.info(f"Exported heatmap to {filepath}")
        return filepath
    
    def export_to_png(self, fig: go.Figure, filename: str, width: int = 1200, height: int = 800) -> str:
        """Export heatmap as PNG file"""
        import os
        os.makedirs(self.output_dir, exist_ok=True)
        
        filepath = os.path.join(self.output_dir, f"{filename}.png")
        fig.write_image(filepath, width=width, height=height)
        
        logger.info(f"Exported heatmap to {filepath}")
        return filepath
    
    def export_to_json(self, heatmap_data: Dict, filename: str) -> str:
        """Export heatmap data as JSON"""
        import os
        import json
        
        os.makedirs(self.output_dir, exist_ok=True)
        filepath = os.path.join(self.output_dir, f"{filename}.json")
        
        with open(filepath, 'w') as f:
            json.dump(heatmap_data, f, indent=2, default=str)
        
        logger.info(f"Exported heatmap data to {filepath}")
        return filepath
