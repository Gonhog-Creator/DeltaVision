import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

@dataclass
class BottleneckEvent:
    """Represents a bottleneck detection event"""
    zone_name: str
    zone_type: str
    timestamp: datetime
    severity_score: float  # 0-1
    current_occupancy: int
    expected_occupancy: float
    bottleneck_type: str  # congestion, queue, resource_shortage
    duration: Optional[float] = None
    resolved_at: Optional[datetime] = None

@dataclass
class FlowAnalysis:
    """Analysis of flow between zones"""
    from_zone: str
    to_zone: str
    transition_count: int
    average_time: float
    bottleneck_score: float
    efficiency_score: float

class BottleneckDetector:
    """Detect and analyze bottlenecks in factory flow"""
    
    def __init__(self, congestion_threshold: float = 2.0, 
                 queue_threshold: int = 5,
                 time_window_minutes: int = 30):
        self.congestion_threshold = congestion_threshold
        self.queue_threshold = queue_threshold
        self.time_window = timedelta(minutes=time_window_minutes)
        
        # Historical data for analysis
        self.occupancy_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.transition_history: deque = deque(maxlen=5000)
        self.active_bottlenecks: Dict[str, BottleneckEvent] = {}
        self.bottleneck_history: List[BottleneckEvent] = []
        
    def update_occupancy_data(self, zone_name: str, occupancy: int, timestamp: datetime):
        """Update occupancy data for bottleneck detection"""
        self.occupancy_history[zone_name].append({
            'timestamp': timestamp,
            'occupancy': occupancy
        })
    
    def update_transition_data(self, transition: Dict):
        """Update transition data for flow analysis"""
        self.transition_history.append(transition)
    
    def detect_congestion_bottlenecks(self, zones_config: Dict, current_time: datetime) -> List[BottleneckEvent]:
        """Detect congestion-based bottlenecks"""
        bottlenecks = []
        
        for zone_name, zone_config in zones_config.items():
            if zone_name not in self.occupancy_history:
                continue
            
            recent_occupancy = self.occupancy_history[zone_name]
            if len(recent_occupancy) < 5:
                continue
            
            # Get current and average occupancy
            current_occupancy = recent_occupancy[-1]['occupancy']
            occupancy_values = [d['occupancy'] for d in recent_occupancy]
            avg_occupancy = np.mean(occupancy_values)
            
            # Calculate expected occupancy based on zone type
            expected_occupancy = self._calculate_expected_occupancy(zone_config)
            
            # Detect congestion
            if current_occupancy > expected_occupancy * self.congestion_threshold:
                severity = min((current_occupancy - expected_occupancy) / expected_occupancy, 1.0)
                
                bottleneck = BottleneckEvent(
                    zone_name=zone_name,
                    zone_type=zone_config.get('type', 'unknown'),
                    timestamp=current_time,
                    severity_score=severity,
                    current_occupancy=current_occupancy,
                    expected_occupancy=expected_occupancy,
                    bottleneck_type='congestion'
                )
                
                bottlenecks.append(bottleneck)
                
                # Update active bottleneck
                if zone_name not in self.active_bottlenecks:
                    self.active_bottlenecks[zone_name] = bottleneck
                    logger.warning(f"Congestion bottleneck detected in {zone_name}: severity {severity:.2f}")
        
        return bottlenecks
    
    def detect_queue_bottlenecks(self, zones_config: Dict, current_time: datetime) -> List[BottleneckEvent]:
        """Detect queue-based bottlenecks"""
        bottlenecks = []
        
        for zone_name, zone_config in zones_config.items():
            if zone_name not in self.occupancy_history:
                continue
            
            recent_occupancy = self.occupancy_history[zone_name]
            if len(recent_occupancy) < 10:
                continue
            
            # Check for sustained high occupancy (queue)
            occupancy_values = [d['occupancy'] for d in list(recent_occupancy)[-10:]]
            
            if all(occ >= self.queue_threshold for occ in occupancy_values):
                current_occupancy = recent_occupancy[-1]['occupancy']
                expected_occupancy = self._calculate_expected_occupancy(zone_config)
                
                severity = min((current_occupancy - self.queue_threshold) / max(expected_occupancy, 1), 1.0)
                
                bottleneck = BottleneckEvent(
                    zone_name=zone_name,
                    zone_type=zone_config.get('type', 'unknown'),
                    timestamp=current_time,
                    severity_score=severity,
                    current_occupancy=current_occupancy,
                    expected_occupancy=expected_occupancy,
                    bottleneck_type='queue'
                )
                
                bottlenecks.append(bottleneck)
                
                if zone_name not in self.active_bottlenecks:
                    self.active_bottlenecks[zone_name] = bottleneck
                    logger.warning(f"Queue bottleneck detected in {zone_name}: severity {severity:.2f}")
        
        return bottlenecks
    
    def detect_flow_bottlenecks(self, current_time: datetime) -> List[FlowAnalysis]:
        """Detect flow bottlenecks between zones"""
        flow_data = defaultdict(list)
        
        # Aggregate transition data
        for transition in self.transition_history:
            if transition['timestamp'] >= current_time - self.time_window:
                key = f"{transition['from_zone']}->{transition['to_zone']}"
                flow_data[key].append(transition)
        
        flow_analyses = []
        
        for flow_key, transitions in flow_data.items():
            if len(transitions) < 3:
                continue
            
            from_zone, to_zone = flow_key.split('->')
            transition_times = [t.get('transition_time', 0) for t in transitions]
            
            # Calculate metrics
            avg_time = np.mean(transition_times)
            transition_count = len(transitions)
            
            # Calculate bottleneck score based on time variance and frequency
            time_variance = np.var(transition_times)
            bottleneck_score = min((time_variance / max(avg_time, 1)) * 0.5 + 
                                 (transition_count / 10) * 0.5, 1.0)
            
            # Calculate efficiency score
            expected_time = self._get_expected_transition_time(from_zone, to_zone)
            efficiency_score = max(0, 1 - (avg_time - expected_time) / max(expected_time, 1))
            
            flow_analysis = FlowAnalysis(
                from_zone=from_zone,
                to_zone=to_zone,
                transition_count=transition_count,
                average_time=avg_time,
                bottleneck_score=bottleneck_score,
                efficiency_score=efficiency_score
            )
            
            flow_analyses.append(flow_analysis)
        
        return sorted(flow_analyses, key=lambda x: x.bottleneck_score, reverse=True)
    
    def resolve_bottlenecks(self, current_time: datetime):
        """Mark bottlenecks as resolved if conditions improved"""
        resolved_zones = []
        
        for zone_name, bottleneck in list(self.active_bottlenecks.items()):
            if zone_name not in self.occupancy_history:
                continue
            
            recent_occupancy = self.occupancy_history[zone_name]
            if len(recent_occupancy) < 3:
                continue
            
            current_occupancy = recent_occupancy[-1]['occupancy']
            expected_occupancy = bottleneck.expected_occupancy
            
            # Check if bottleneck is resolved
            if current_occupancy <= expected_occupancy * 1.2:  # 20% tolerance
                bottleneck.duration = (current_time - bottleneck.timestamp).total_seconds()
                bottleneck.resolved_at = current_time
                
                self.bottleneck_history.append(bottleneck)
                del self.active_bottlenecks[zone_name]
                resolved_zones.append(zone_name)
                
                logger.info(f"Bottleneck resolved in {zone_name} after {bottleneck.duration:.1f} seconds")
        
        return resolved_zones
    
    def get_bottleneck_summary(self, time_window: timedelta = None) -> Dict:
        """Get summary of bottleneck activity"""
        if time_window is None:
            time_window = self.time_window
        
        cutoff_time = datetime.now() - time_window
        
        # Filter recent bottlenecks
        recent_bottlenecks = [
            b for b in self.bottleneck_history 
            if b.timestamp >= cutoff_time
        ]
        
        # Group by zone
        zone_bottlenecks = defaultdict(list)
        for bottleneck in recent_bottlenecks:
            zone_bottlenecks[bottleneck.zone_name].append(bottleneck)
        
        summary = {
            'total_bottlenecks': len(recent_bottlenecks),
            'active_bottlenecks': len(self.active_bottlenecks),
            'zones_affected': len(zone_bottlenecks),
            'zone_details': {},
            'bottleneck_types': defaultdict(int),
            'average_duration': 0,
            'total_downtime': 0
        }
        
        # Calculate zone-specific metrics
        for zone_name, bottlenecks in zone_bottlenecks.items():
            durations = [b.duration for b in bottlenecks if b.duration]
            severities = [b.severity_score for b in bottlenecks]
            
            summary['zone_details'][zone_name] = {
                'count': len(bottlenecks),
                'avg_severity': np.mean(severities) if severities else 0,
                'avg_duration': np.mean(durations) if durations else 0,
                'total_duration': sum(durations) if durations else 0,
                'types': list(set(b.bottleneck_type for b in bottlenecks))
            }
            
            summary['total_downtime'] += sum(durations) if durations else 0
        
        # Calculate overall metrics
        all_durations = [b.duration for b in recent_bottlenecks if b.duration]
        if all_durations:
            summary['average_duration'] = np.mean(all_durations)
        
        # Count bottleneck types
        for bottleneck in recent_bottlenecks:
            summary['bottleneck_types'][bottleneck.bottleneck_type] += 1
        
        return summary
    
    def get_bottleneck_recommendations(self) -> List[Dict]:
        """Generate recommendations for resolving bottlenecks"""
        recommendations = []
        
        # Analyze active bottlenecks
        for zone_name, bottleneck in self.active_bottlenecks.items():
            if bottleneck.bottleneck_type == 'congestion':
                recommendations.append({
                    'zone': zone_name,
                    'type': 'congestion',
                    'priority': 'high' if bottleneck.severity_score > 0.7 else 'medium',
                    'recommendation': f"Consider adding capacity or rebalancing workload in {zone_name}",
                    'severity': bottleneck.severity_score,
                    'current_occupancy': bottleneck.current_occupancy,
                    'expected_occupancy': bottleneck.expected_occupancy
                })
            
            elif bottleneck.bottleneck_type == 'queue':
                recommendations.append({
                    'zone': zone_name,
                    'type': 'queue',
                    'priority': 'high' if bottleneck.severity_score > 0.6 else 'medium',
                    'recommendation': f"Investigate processing speed in {zone_name} or add parallel stations",
                    'severity': bottleneck.severity_score,
                    'current_occupancy': bottleneck.current_occupancy,
                    'queue_length': bottleneck.current_occupancy
                })
        
        # Analyze flow bottlenecks
        flow_analyses = self.detect_flow_bottlenecks(datetime.now())
        for flow in flow_analyses[:5]:  # Top 5 flow issues
            if flow.bottleneck_score > 0.5:
                recommendations.append({
                    'zone': f"{flow.from_zone}->{flow.to_zone}",
                    'type': 'flow',
                    'priority': 'medium',
                    'recommendation': f"Optimize handoff process from {flow.from_zone} to {flow.to_zone}",
                    'severity': flow.bottleneck_score,
                    'efficiency': flow.efficiency_score,
                    'avg_time': flow.average_time
                })
        
        return sorted(recommendations, key=lambda x: x['severity'], reverse=True)
    
    def _calculate_expected_occupancy(self, zone_config: Dict) -> float:
        """Calculate expected occupancy for a zone"""
        zone_type = zone_config.get('type', 'unknown')
        expected_dwell_time = zone_config.get('expected_dwell_time', 60)
        
        # Base expected occupancy by zone type
        base_occupancy = {
            'workstation': 2.0,  # 2 workers per station on average
            'storage': 1.0,
            'transit': 3.0,  # Higher for transit areas
            'quality_control': 1.5,
            'rework': 1.0,
            'unknown': 1.0
        }
        
        # Adjust based on expected dwell time
        time_factor = min(expected_dwell_time / 300, 2.0)  # Normalize to 5 minutes
        
        return base_occupancy.get(zone_type, 1.0) * time_factor
    
    def _get_expected_transition_time(self, from_zone: str, to_zone: str) -> float:
        """Get expected transition time between zones"""
        # This could be configured based on factory layout
        # For now, using simple estimates
        zone_distances = {
            ('material_rack', 'cutting_table'): 30,
            ('cutting_table', 'panel_assembly'): 20,
            ('panel_assembly', 'sewing_line'): 25,
            ('sewing_line', 'inspection'): 40,
            ('inspection', 'packing'): 15,
            ('inspection', 'rework'): 35,
            ('rework', 'sewing_line'): 30,
            ('packing', 'finished_goods'): 20,
        }
        
        return zone_distances.get((from_zone, to_zone), 30)  # Default 30 seconds
