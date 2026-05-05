import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

@dataclass
class WorkerProductivity:
    """Productivity metrics for a worker"""
    track_id: int
    camera_id: str
    date: datetime
    
    # Time metrics
    total_time_tracked: float  # seconds
    productive_time: float     # seconds in work zones
    transit_time: float        # seconds in transit
    idle_time: float          # seconds stationary
    
    # Movement metrics
    total_distance: float      # pixels
    walking_efficiency: float  # productive_time / (productive_time + transit_time)
    
    # Task metrics
    zones_visited: int
    tasks_completed: int       # estimated
    efficiency_score: float    # 0-1
    
    # Quality metrics
    rework_visits: int
    inspection_passes: int

@dataclass
class ZoneProductivity:
    """Productivity metrics for a zone"""
    zone_name: str
    zone_type: str
    date: datetime
    
    # Utilization metrics
    utilization_rate: float    # 0-1
    throughput: float         # workers per hour
    average_dwell_time: float # seconds
    
    # Efficiency metrics
    processing_efficiency: float  # actual vs expected time
    queue_time: float            # average time waiting
    bottleneck_frequency: int    # bottlenecks per hour
    
    # Quality metrics
    error_rate: float           # rework rate
    output_quality_score: float  # 0-1

class ProductivityAnalyzer:
    """Analyze productivity metrics for factory operations"""
    
    def __init__(self, time_window_hours: int = 8):
        self.time_window = timedelta(hours=time_window_hours)
        
        # Productivity data storage
        self.worker_productivity: Dict[int, WorkerProductivity] = {}
        self.zone_productivity: Dict[str, ZoneProductivity] = {}
        
        # Historical data
        self.productivity_history: deque = deque(maxlen=1000)
        self.baseline_productivity: Dict[str, float] = {}
        
        # Zone type definitions for productivity calculation
        self.productive_zone_types = {'workstation', 'quality_control'}
        self.transit_zone_types = {'transit', 'aisle'}
        self.storage_zone_types = {'storage'}
        
    def calculate_worker_productivity(self, track_data: Dict, zone_manager) -> WorkerProductivity:
        """Calculate productivity metrics for a worker"""
        track_id = track_data['track_id']
        camera_id = track_data['camera_id']
        
        # Extract time data
        positions = track_data.get('positions', [])
        zone_visits = track_data.get('zone_visits', [])
        
        if not positions:
            return None
        
        # Calculate time metrics
        start_time = positions[0]['timestamp']
        end_time = positions[-1]['timestamp']
        total_time = (end_time - start_time).total_seconds()
        
        # Categorize time by zone type
        productive_time = 0
        transit_time = 0
        idle_time = 0
        
        for visit in zone_visits:
            zone = zone_manager.get_zone_by_name(visit['zone_name'])
            if not zone:
                continue
            
            dwell_time = visit.get('dwell_time', 0)
            
            if zone.zone_type in self.productive_zone_types:
                productive_time += dwell_time
            elif zone.zone_type in self.transit_zone_types:
                transit_time += dwell_time
            else:
                # Storage or other zones
                productive_time += dwell_time * 0.5  # Partial credit
        
        # Calculate movement metrics
        total_distance = self._calculate_total_distance(positions)
        walking_efficiency = productive_time / max(productive_time + transit_time, 1)
        
        # Calculate task metrics
        zones_visited = len(set(visit['zone_name'] for visit in zone_visits))
        tasks_completed = self._estimate_tasks_completed(zone_visits, zone_manager)
        
        # Calculate quality metrics
        rework_visits = sum(1 for visit in zone_visits 
                           if 'rework' in visit['zone_name'].lower())
        inspection_passes = sum(1 for visit in zone_visits 
                               if 'inspection' in visit['zone_name'].lower())
        
        # Calculate efficiency score
        efficiency_score = self._calculate_worker_efficiency(
            productive_time, transit_time, total_distance, tasks_completed, total_time
        )
        
        productivity = WorkerProductivity(
            track_id=track_id,
            camera_id=camera_id,
            date=start_time.date(),
            total_time_tracked=total_time,
            productive_time=productive_time,
            transit_time=transit_time,
            idle_time=idle_time,
            total_distance=total_distance,
            walking_efficiency=walking_efficiency,
            zones_visited=zones_visited,
            tasks_completed=tasks_completed,
            efficiency_score=efficiency_score,
            rework_visits=rework_visits,
            inspection_passes=inspection_passes
        )
        
        self.worker_productivity[track_id] = productivity
        return productivity
    
    def calculate_zone_productivity(self, zone_data: Dict, zone_name: str, zone_manager) -> ZoneProductivity:
        """Calculate productivity metrics for a zone"""
        zone = zone_manager.get_zone_by_name(zone_name)
        if not zone:
            return None
        
        # Extract zone data
        occupancy_data = zone_data.get('occupancy_history', [])
        visits = zone_data.get('visits', [])
        
        if not occupancy_data:
            return None
        
        # Calculate utilization metrics
        current_occupancy = occupancy_data[-1]['occupancy'] if occupancy_data else 0
        avg_occupancy = np.mean([d['occupancy'] for d in occupancy_data])
        utilization_rate = min(avg_occupancy / max(zone.expected_dwell_time / 60, 1), 1.0)
        
        # Calculate throughput
        time_window_hours = self.time_window.total_seconds() / 3600
        throughput = len(visits) / max(time_window_hours, 1)
        
        # Calculate average dwell time
        dwell_times = [v.get('dwell_time', 0) for v in visits if v.get('dwell_time')]
        avg_dwell_time = np.mean(dwell_times) if dwell_times else 0
        
        # Calculate processing efficiency
        expected_dwell_time = zone.expected_dwell_time
        processing_efficiency = min(expected_dwell_time / max(avg_dwell_time, 1), 2.0)
        
        # Calculate queue time (time above expected occupancy)
        queue_time = self._calculate_queue_time(occupancy_data, zone)
        
        # Calculate bottleneck frequency
        bottleneck_frequency = zone_data.get('bottleneck_count', 0)
        
        # Calculate quality metrics
        error_rate = self._calculate_error_rate(visits, zone_name)
        output_quality_score = max(0, 1 - error_rate)
        
        productivity = ZoneProductivity(
            zone_name=zone_name,
            zone_type=zone.zone_type,
            date=datetime.now().date(),
            utilization_rate=utilization_rate,
            throughput=throughput,
            average_dwell_time=avg_dwell_time,
            processing_efficiency=processing_efficiency,
            queue_time=queue_time,
            bottleneck_frequency=bottleneck_frequency,
            error_rate=error_rate,
            output_quality_score=output_quality_score
        )
        
        self.zone_productivity[zone_name] = productivity
        return productivity
    
    def get_productivity_trends(self, time_window_days: int = 7) -> Dict:
        """Analyze productivity trends over time"""
        cutoff_date = datetime.now().date() - timedelta(days=time_window_days)
        
        # Filter recent productivity data
        recent_worker_data = [
            p for p in self.productivity_history
            if p.date >= cutoff_date and hasattr(p, 'track_id')
        ]
        
        recent_zone_data = [
            p for p in self.productivity_history
            if p.date >= cutoff_date and hasattr(p, 'zone_name')
        ]
        
        trends = {
            'worker_trends': self._analyze_worker_trends(recent_worker_data),
            'zone_trends': self._analyze_zone_trends(recent_zone_data),
            'overall_trends': self._analyze_overall_trends(recent_worker_data, recent_zone_data)
        }
        
        return trends
    
    def get_productivity_benchmarks(self) -> Dict:
        """Get productivity benchmarks and comparisons"""
        if not self.worker_productivity:
            return {}
        
        # Calculate worker benchmarks
        worker_efficiencies = [p.efficiency_score for p in self.worker_productivity.values()]
        worker_productivities = [p.productive_time / max(p.total_time_tracked, 1) 
                               for p in self.worker_productivity.values()]
        
        # Calculate zone benchmarks
        zone_utilizations = [p.utilization_rate for p in self.zone_productivity.values()]
        zone_throughputs = [p.throughput for p in self.zone_productivity.values()]
        
        benchmarks = {
            'worker_benchmarks': {
                'avg_efficiency': np.mean(worker_efficiencies) if worker_efficiencies else 0,
                'median_efficiency': np.median(worker_efficiencies) if worker_efficiencies else 0,
                'top_quartile_efficiency': np.percentile(worker_efficiencies, 75) if worker_efficiencies else 0,
                'avg_productivity_ratio': np.mean(worker_productivities) if worker_productivities else 0,
                'most_productive_workers': self._get_top_performers('efficiency', 5)
            },
            'zone_benchmarks': {
                'avg_utilization': np.mean(zone_utilizations) if zone_utilizations else 0,
                'median_utilization': np.median(zone_utilizations) if zone_utilizations else 0,
                'avg_throughput': np.mean(zone_throughputs) if zone_throughputs else 0,
                'most_utilized_zones': self._get_top_performers('utilization', 5),
                'least_utilized_zones': self._get_bottom_performers('utilization', 5)
            },
            'productivity_distribution': {
                'high_performers': len([e for e in worker_efficiencies if e > 0.8]),
                'average_performers': len([e for e in worker_efficiencies if 0.5 <= e <= 0.8]),
                'low_performers': len([e for e in worker_efficiencies if e < 0.5])
            }
        }
        
        return benchmarks
    
    def get_productivity_recommendations(self) -> List[Dict]:
        """Generate productivity improvement recommendations"""
        recommendations = []
        
        if not self.worker_productivity:
            return recommendations
        
        # Analyze low-performing workers
        low_performers = [
            p for p in self.worker_productivity.values() 
            if p.efficiency_score < 0.5
        ]
        
        for worker in low_performers:
            if worker.idle_time > worker.total_time_tracked * 0.3:
                recommendations.append({
                    'type': 'worker_idle_time',
                    'target': f'Worker {worker.track_id}',
                    'priority': 'medium',
                    'recommendation': f"Worker {worker.track_id} has high idle time ({worker.idle_time:.1f}s). Consider task reallocation.",
                    'metric': worker.idle_time / worker.total_time_tracked,
                    'threshold': 0.3
                })
            
            if worker.walking_efficiency < 0.6:
                recommendations.append({
                    'type': 'worker_movement',
                    'target': f'Worker {worker.track_id}',
                    'priority': 'medium',
                    'recommendation': f"Worker {worker.track_id} has low walking efficiency ({worker.walking_efficiency:.2f}). Consider workspace optimization.",
                    'metric': worker.walking_efficiency,
                    'threshold': 0.6
                })
        
        # Analyze zone productivity
        low_utilization_zones = [
            p for p in self.zone_productivity.values() 
            if p.utilization_rate < 0.3 and p.zone_type in self.productive_zone_types
        ]
        
        for zone in low_utilization_zones:
            recommendations.append({
                'type': 'zone_utilization',
                'target': zone.zone_name,
                'priority': 'high',
                'recommendation': f"Zone {zone.zone_name} has low utilization ({zone.utilization_rate:.2f}). Consider workload balancing.",
                'metric': zone.utilization_rate,
                'threshold': 0.3
            })
        
        # Analyze bottlenecks
        high_bottleneck_zones = [
            p for p in self.zone_productivity.values() 
            if p.bottleneck_frequency > 5
        ]
        
        for zone in high_bottleneck_zones:
            recommendations.append({
                'type': 'zone_bottleneck',
                'target': zone.zone_name,
                'priority': 'high',
                'recommendation': f"Zone {zone.zone_name} experiences frequent bottlenecks ({zone.bottleneck_frequency}/day). Consider capacity increase.",
                'metric': zone.bottleneck_frequency,
                'threshold': 5
            })
        
        return sorted(recommendations, key=lambda x: x['priority'], reverse=True)
    
    def _calculate_total_distance(self, positions: List[Dict]) -> float:
        """Calculate total distance traveled"""
        if len(positions) < 2:
            return 0.0
        
        total_distance = 0.0
        for i in range(1, len(positions)):
            prev_pos = positions[i-1]['centroid']
            curr_pos = positions[i]['centroid']
            
            distance = np.sqrt(
                (curr_pos[0] - prev_pos[0])**2 + 
                (curr_pos[1] - prev_pos[1])**2
            )
            total_distance += distance
        
        return total_distance
    
    def _estimate_tasks_completed(self, zone_visits: List[Dict], zone_manager) -> int:
        """Estimate number of tasks completed based on zone visits"""
        tasks = 0
        
        for visit in zone_visits:
            zone = zone_manager.get_zone_by_name(visit['zone_name'])
            if not zone:
                continue
            
            # Estimate tasks based on zone type and dwell time
            dwell_time = visit.get('dwell_time', 0)
            expected_time = zone.expected_dwell_time
            
            if zone.zone_type in self.productive_zone_types:
                # Estimate tasks completed
                estimated_tasks = dwell_time / max(expected_time, 60)
                tasks += int(estimated_tasks)
        
        return tasks
    
    def _calculate_worker_efficiency(self, productive_time: float, transit_time: float,
                                   total_distance: float, tasks_completed: int, total_time: float) -> float:
        """Calculate overall worker efficiency score"""
        if total_time == 0:
            return 0.0
        
        # Time efficiency (productive vs total time)
        time_efficiency = productive_time / total_time
        
        # Movement efficiency (less walking is better)
        movement_efficiency = 1.0 - min(total_distance / 10000, 0.5)  # Normalize to reasonable range
        
        # Task efficiency (tasks per time)
        task_rate = tasks_completed / max(total_time / 3600, 1)  # tasks per hour
        task_efficiency = min(task_rate / 10, 1.0)  # Normalize to 10 tasks/hour as optimal
        
        # Weighted combination
        efficiency = (time_efficiency * 0.4) + (movement_efficiency * 0.3) + (task_efficiency * 0.3)
        
        return max(0, min(efficiency, 1.0))
    
    def _calculate_queue_time(self, occupancy_data: List[Dict], zone) -> float:
        """Calculate average queue time for a zone"""
        if not occupancy_data:
            return 0.0
        
        expected_capacity = zone.expected_dwell_time / 60  # rough estimate
        queue_time = 0.0
        
        for data in occupancy_data:
            if data['occupancy'] > expected_capacity:
                excess = data['occupancy'] - expected_capacity
                queue_time += excess * 60  # Convert to seconds
        
        return queue_time / len(occupancy_data) if occupancy_data else 0.0
    
    def _calculate_error_rate(self, visits: List[Dict], zone_name: str) -> float:
        """Calculate error rate based on rework visits"""
        if 'rework' in zone_name.lower():
            return 1.0  # Rework zone itself indicates errors
        
        total_visits = len(visits)
        if total_visits == 0:
            return 0.0
        
        # Count visits that lead to rework
        rework_visits = sum(1 for visit in visits 
                           if visit.get('next_zone', '').lower().find('rework') != -1)
        
        return rework_visits / total_visits
    
    def _analyze_worker_trends(self, worker_data: List) -> Dict:
        """Analyze trends in worker productivity"""
        if not worker_data:
            return {}
        
        # Group by date
        daily_data = defaultdict(list)
        for data in worker_data:
            daily_data[data.date].append(data)
        
        trends = {}
        for date, day_data in daily_data.items():
            efficiencies = [d.efficiency_score for d in day_data]
            trends[date.isoformat()] = {
                'avg_efficiency': np.mean(efficiencies),
                'worker_count': len(day_data),
                'efficiency_std': np.std(efficiencies)
            }
        
        return trends
    
    def _analyze_zone_trends(self, zone_data: List) -> Dict:
        """Analyze trends in zone productivity"""
        if not zone_data:
            return {}
        
        # Group by date and zone
        daily_data = defaultdict(lambda: defaultdict(list))
        for data in zone_data:
            daily_data[data.date][data.zone_name].append(data)
        
        trends = {}
        for date, zones in daily_data.items():
            trends[date.isoformat()] = {}
            for zone_name, zone_data_list in zones.items():
                utilizations = [d.utilization_rate for d in zone_data_list]
                trends[date.isoformat()][zone_name] = {
                    'avg_utilization': np.mean(utilizations),
                    'throughput': zone_data_list[0].throughput  # Assuming single record per zone per day
                }
        
        return trends
    
    def _analyze_overall_trends(self, worker_data: List, zone_data: List) -> Dict:
        """Analyze overall productivity trends"""
        return {
            'worker_count_trend': len(worker_data),
            'zone_count_trend': len(zone_data),
            'avg_worker_efficiency': np.mean([d.efficiency_score for d in worker_data]) if worker_data else 0,
            'avg_zone_utilization': np.mean([d.utilization_rate for d in zone_data]) if zone_data else 0
        }
    
    def _get_top_performers(self, metric: str, count: int) -> List[Dict]:
        """Get top performers by metric"""
        if metric == 'efficiency':
            performers = sorted(
                [(p.track_id, p.efficiency_score) for p in self.worker_productivity.values()],
                key=lambda x: x[1], reverse=True
            )[:count]
        elif metric == 'utilization':
            performers = sorted(
                [(p.zone_name, p.utilization_rate) for p in self.zone_productivity.values()],
                key=lambda x: x[1], reverse=True
            )[:count]
        else:
            return []
        
        return [{'id': p[0], 'value': p[1]} for p in performers]
    
    def _get_bottom_performers(self, metric: str, count: int) -> List[Dict]:
        """Get bottom performers by metric"""
        if metric == 'utilization':
            performers = sorted(
                [(p.zone_name, p.utilization_rate) for p in self.zone_productivity.values()],
                key=lambda x: x[1]
            )[:count]
        else:
            return []
        
        return [{'id': p[0], 'value': p[1]} for p in performers]
