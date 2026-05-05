import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path
import json

from app.analytics.productivity import ProductivityAnalyzer
from app.analytics.bottlenecks import BottleneckDetector
from app.analytics.heatmaps import HeatmapAnalyzer, HeatmapExporter

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generate comprehensive analytics reports"""
    
    def __init__(self, output_dir: str = "data/exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.productivity_analyzer = ProductivityAnalyzer()
        self.bottleneck_detector = BottleneckDetector()
        self.heatmap_analyzer = HeatmapAnalyzer()
        self.heatmap_exporter = HeatmapExporter(str(self.output_dir))
    
    def generate_daily_report(self, date: datetime, 
                            worker_data: Dict, zone_data: Dict,
                            system_metrics: Dict) -> Dict[str, str]:
        """Generate comprehensive daily report"""
        date_str = date.strftime('%Y-%m-%d')
        report_files = {}
        
        try:
            # Generate productivity analysis
            productivity_report = self._generate_productivity_report(worker_data, zone_data, date)
            report_files['productivity'] = self._save_report(
                productivity_report, f"productivity_report_{date_str}.json"
            )
            
            # Generate bottleneck analysis
            bottleneck_report = self._generate_bottleneck_report(zone_data, date)
            report_files['bottlenecks'] = self._save_report(
                bottleneck_report, f"bottleneck_report_{date_str}.json"
            )
            
            # Generate efficiency analysis
            efficiency_report = self._generate_efficiency_report(worker_data, zone_data, system_metrics, date)
            report_files['efficiency'] = self._save_report(
                efficiency_report, f"efficiency_report_{date_str}.json"
            )
            
            # Generate summary dashboard
            summary_report = self._generate_summary_report(
                productivity_report, bottleneck_report, efficiency_report, date
            )
            report_files['summary'] = self._save_report(
                summary_report, f"summary_report_{date_str}.json"
            )
            
            # Generate CSV exports
            csv_files = self._generate_csv_exports(worker_data, zone_data, date_str)
            report_files.update(csv_files)
            
            logger.info(f"Generated daily report for {date_str}")
            return report_files
            
        except Exception as e:
            logger.error(f"Error generating daily report: {e}")
            return {}
    
    def generate_shift_report(self, shift_start: datetime, shift_end: datetime,
                            worker_data: Dict, zone_data: Dict) -> Dict[str, str]:
        """Generate report for specific shift"""
        shift_duration = (shift_end - shift_start).total_seconds() / 3600  # hours
        shift_name = f"{shift_start.strftime('%H%M')}-{shift_end.strftime('%H%M')}"
        date_str = shift_start.strftime('%Y-%m-%d')
        
        report_files = {}
        
        try:
            # Filter data for shift timeframe
            filtered_worker_data = self._filter_data_by_time(worker_data, shift_start, shift_end)
            filtered_zone_data = self._filter_data_by_time(zone_data, shift_start, shift_end)
            
            # Generate shift-specific reports
            shift_report = {
                'shift_info': {
                    'date': date_str,
                    'shift_name': shift_name,
                    'start_time': shift_start.isoformat(),
                    'end_time': shift_end.isoformat(),
                    'duration_hours': shift_duration
                },
                'productivity': self._analyze_shift_productivity(filtered_worker_data, filtered_zone_data),
                'bottlenecks': self._analyze_shift_bottlenecks(filtered_zone_data),
                'efficiency': self._analyze_shift_efficiency(filtered_worker_data, filtered_zone_data),
                'recommendations': self._generate_shift_recommendations(filtered_worker_data, filtered_zone_data)
            }
            
            report_files['shift_report'] = self._save_report(
                shift_report, f"shift_report_{date_str}_{shift_name}.json"
            )
            
            logger.info(f"Generated shift report for {date_str} {shift_name}")
            return report_files
            
        except Exception as e:
            logger.error(f"Error generating shift report: {e}")
            return {}
    
    def generate_weekly_report(self, week_start: datetime, daily_data: List[Dict]) -> Dict[str, str]:
        """Generate weekly summary report"""
        week_end = week_start + timedelta(days=7)
        week_str = f"{week_start.strftime('%Y-%m-%d')}_to_{week_end.strftime('%Y-%m-%d')}"
        
        report_files = {}
        
        try:
            # Aggregate daily data
            weekly_summary = self._aggregate_weekly_data(daily_data)
            
            # Generate weekly analysis
            weekly_report = {
                'week_info': {
                    'start_date': week_start.strftime('%Y-%m-%d'),
                    'end_date': week_end.strftime('%Y-%m-%d'),
                    'days_analyzed': len(daily_data)
                },
                'trends': self._analyze_weekly_trends(daily_data),
                'productivity_summary': weekly_summary['productivity'],
                'bottleneck_summary': weekly_summary['bottlenecks'],
                'efficiency_summary': weekly_summary['efficiency'],
                'improvement_areas': self._identify_improvement_areas(weekly_summary),
                'kpi_summary': self._calculate_weekly_kpis(weekly_summary)
            }
            
            report_files['weekly_report'] = self._save_report(
                weekly_report, f"weekly_report_{week_str}.json"
            )
            
            # Generate trend charts
            trend_files = self._generate_trend_charts(daily_data, week_str)
            report_files.update(trend_files)
            
            logger.info(f"Generated weekly report for {week_str}")
            return report_files
            
        except Exception as e:
            logger.error(f"Error generating weekly report: {e}")
            return {}
    
    def _generate_productivity_report(self, worker_data: Dict, zone_data: Dict, date: datetime) -> Dict:
        """Generate productivity analysis report"""
        productivities = []
        
        # Analyze worker productivity
        for track_id, data in worker_data.items():
            productivity = self.productivity_analyzer.calculate_worker_productivity(data, None)
            if productivity:
                productivities.append({
                    'track_id': productivity.track_id,
                    'efficiency_score': productivity.efficiency_score,
                    'productive_time': productivity.productive_time,
                    'transit_time': productivity.transit_time,
                    'idle_time': productivity.idle_time,
                    'tasks_completed': productivity.tasks_completed,
                    'walking_efficiency': productivity.walking_efficiency
                })
        
        # Analyze zone productivity
        zone_productivities = []
        for zone_name, data in zone_data.items():
            productivity = self.productivity_analyzer.calculate_zone_productivity(data, zone_name, None)
            if productivity:
                zone_productivities.append({
                    'zone_name': productivity.zone_name,
                    'zone_type': productivity.zone_type,
                    'utilization_rate': productivity.utilization_rate,
                    'throughput': productivity.throughput,
                    'average_dwell_time': productivity.average_dwell_time,
                    'processing_efficiency': productivity.processing_efficiency,
                    'output_quality_score': productivity.output_quality_score
                })
        
        return {
            'date': date.strftime('%Y-%m-%d'),
            'worker_productivity': {
                'workers_analyzed': len(productivities),
                'avg_efficiency': np.mean([p['efficiency_score'] for p in productivities]) if productivities else 0,
                'top_performers': sorted(productivities, key=lambda x: x['efficiency_score'], reverse=True)[:5],
                'low_performers': sorted(productivities, key=lambda x: x['efficiency_score'])[:5],
                'details': productivities
            },
            'zone_productivity': {
                'zones_analyzed': len(zone_productivities),
                'avg_utilization': np.mean([p['utilization_rate'] for p in zone_productivities]) if zone_productivities else 0,
                'most_utilized': sorted(zone_productivities, key=lambda x: x['utilization_rate'], reverse=True)[:3],
                'least_utilized': sorted(zone_productivities, key=lambda x: x['utilization_rate'])[:3],
                'details': zone_productivities
            },
            'benchmarks': self.productivity_analyzer.get_productivity_benchmarks()
        }
    
    def _generate_bottleneck_report(self, zone_data: Dict, date: datetime) -> Dict:
        """Generate bottleneck analysis report"""
        bottlenecks = []
        
        for zone_name, data in zone_data.items():
            # Detect bottlenecks for this zone
            zone_bottlenecks = self.bottleneck_detector.detect_congestion_bottlenecks(
                {zone_name: data}, datetime.now()
            )
            
            for bottleneck in zone_bottlenecks:
                bottlenecks.append({
                    'zone_name': bottleneck.zone_name,
                    'zone_type': bottleneck.zone_type,
                    'severity_score': bottleneck.severity_score,
                    'current_occupancy': bottleneck.current_occupancy,
                    'expected_occupancy': bottleneck.expected_occupancy,
                    'bottleneck_type': bottleneck.bottleneck_type,
                    'timestamp': bottleneck.timestamp.isoformat()
                })
        
        # Get bottleneck summary and recommendations
        bottleneck_summary = self.bottleneck_detector.get_bottleneck_summary()
        recommendations = self.bottleneck_detector.get_bottleneck_recommendations()
        
        return {
            'date': date.strftime('%Y-%m-%d'),
            'bottlenecks_detected': len(bottlenecks),
            'bottleneck_summary': bottleneck_summary,
            'active_bottlenecks': bottlenecks,
            'recommendations': recommendations,
            'severity_distribution': self._analyze_severity_distribution(bottlenecks)
        }
    
    def _generate_efficiency_report(self, worker_data: Dict, zone_data: Dict, 
                                  system_metrics: Dict, date: datetime) -> Dict:
        """Generate efficiency analysis report"""
        # Calculate overall efficiency metrics
        worker_count = len(worker_data)
        zone_count = len(zone_data)
        
        # Worker efficiency metrics
        worker_efficiencies = []
        total_productive_time = 0
        total_transit_time = 0
        
        for track_id, data in worker_data.items():
            productivity = self.productivity_analyzer.calculate_worker_productivity(data, None)
            if productivity:
                worker_efficiencies.append(productivity.efficiency_score)
                total_productive_time += productivity.productive_time
                total_transit_time += productivity.transit_time
        
        # Zone efficiency metrics
        zone_efficiencies = []
        for zone_name, data in zone_data.items():
            productivity = self.productivity_analyzer.calculate_zone_productivity(data, zone_name, None)
            if productivity:
                zone_efficiencies.append(productivity.processing_efficiency)
        
        # Calculate overall efficiency score
        overall_efficiency = self._calculate_overall_efficiency(
            worker_efficiencies, zone_efficiencies, system_metrics
        )
        
        return {
            'date': date.strftime('%Y-%m-%d'),
            'overall_efficiency_score': overall_efficiency,
            'worker_efficiency': {
                'workers_analyzed': len(worker_efficiencies),
                'avg_efficiency': np.mean(worker_efficiencies) if worker_efficiencies else 0,
                'efficiency_distribution': {
                    'high': len([e for e in worker_efficiencies if e > 0.8]),
                    'medium': len([e for e in worker_efficiencies if 0.5 <= e <= 0.8]),
                    'low': len([e for e in worker_efficiencies if e < 0.5])
                },
                'time_allocation': {
                    'productive_time_ratio': total_productive_time / max(total_productive_time + total_transit_time, 1),
                    'transit_time_ratio': total_transit_time / max(total_productive_time + total_transit_time, 1)
                }
            },
            'zone_efficiency': {
                'zones_analyzed': len(zone_efficiencies),
                'avg_processing_efficiency': np.mean(zone_efficiencies) if zone_efficiencies else 0,
                'efficiency_by_type': self._analyze_efficiency_by_zone_type(zone_data)
            },
            'system_efficiency': system_metrics,
            'efficiency_trends': self._analyze_efficiency_trends(worker_data, zone_data)
        }
    
    def _generate_summary_report(self, productivity_report: Dict, bottleneck_report: Dict,
                               efficiency_report: Dict, date: datetime) -> Dict:
        """Generate executive summary report"""
        return {
            'date': date.strftime('%Y-%m-%d'),
            'executive_summary': {
                'overall_health_score': self._calculate_health_score(
                    productivity_report, bottleneck_report, efficiency_report
                ),
                'key_metrics': {
                    'total_workers': productivity_report['worker_productivity']['workers_analyzed'],
                    'avg_worker_efficiency': productivity_report['worker_productivity']['avg_efficiency'],
                    'avg_zone_utilization': productivity_report['zone_productivity']['avg_utilization'],
                    'active_bottlenecks': bottleneck_report['bottlenecks_detected'],
                    'overall_efficiency': efficiency_report['overall_efficiency_score']
                },
                'status': self._determine_overall_status(
                    productivity_report, bottleneck_report, efficiency_report
                )
            },
            'highlights': self._extract_highlights(productivity_report, bottleneck_report, efficiency_report),
            'concerns': self._extract_concerns(productivity_report, bottleneck_report, efficiency_report),
            'top_recommendations': self._get_top_recommendations(bottleneck_report['recommendations'][:3])
        }
    
    def _generate_csv_exports(self, worker_data: Dict, zone_data: Dict, date_str: str) -> Dict[str, str]:
        """Generate CSV exports for data analysis"""
        csv_files = {}
        
        try:
            # Worker productivity CSV
            worker_rows = []
            for track_id, data in worker_data.items():
                productivity = self.productivity_analyzer.calculate_worker_productivity(data, None)
                if productivity:
                    worker_rows.append({
                        'track_id': productivity.track_id,
                        'date': date_str,
                        'efficiency_score': productivity.efficiency_score,
                        'productive_time': productivity.productive_time,
                        'transit_time': productivity.transit_time,
                        'idle_time': productivity.idle_time,
                        'total_distance': productivity.total_distance,
                        'tasks_completed': productivity.tasks_completed,
                        'zones_visited': productivity.zones_visited
                    })
            
            if worker_rows:
                worker_df = pd.DataFrame(worker_rows)
                worker_csv_path = self.output_dir / f"worker_productivity_{date_str}.csv"
                worker_df.to_csv(worker_csv_path, index=False)
                csv_files['worker_csv'] = str(worker_csv_path)
            
            # Zone metrics CSV
            zone_rows = []
            for zone_name, data in zone_data.items():
                productivity = self.productivity_analyzer.calculate_zone_productivity(data, zone_name, None)
                if productivity:
                    zone_rows.append({
                        'zone_name': productivity.zone_name,
                        'date': date_str,
                        'zone_type': productivity.zone_type,
                        'utilization_rate': productivity.utilization_rate,
                        'throughput': productivity.throughput,
                        'average_dwell_time': productivity.average_dwell_time,
                        'processing_efficiency': productivity.processing_efficiency,
                        'bottleneck_frequency': productivity.bottleneck_frequency,
                        'output_quality_score': productivity.output_quality_score
                    })
            
            if zone_rows:
                zone_df = pd.DataFrame(zone_rows)
                zone_csv_path = self.output_dir / f"zone_metrics_{date_str}.csv"
                zone_df.to_csv(zone_csv_path, index=False)
                csv_files['zone_csv'] = str(zone_csv_path)
            
        except Exception as e:
            logger.error(f"Error generating CSV exports: {e}")
        
        return csv_files
    
    def _save_report(self, report_data: Dict, filename: str) -> str:
        """Save report to file"""
        filepath = self.output_dir / filename
        with open(filepath, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        return str(filepath)
    
    def _filter_data_by_time(self, data: Dict, start_time: datetime, end_time: datetime) -> Dict:
        """Filter data by time range"""
        filtered_data = {}
        
        for key, value in data.items():
            if isinstance(value, dict) and 'timestamp' in value:
                timestamp = value['timestamp']
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp)
                
                if start_time <= timestamp <= end_time:
                    filtered_data[key] = value
            else:
                filtered_data[key] = value
        
        return filtered_data
    
    def _calculate_overall_efficiency(self, worker_efficiencies: List[float], 
                                    zone_efficiencies: List[float], 
                                    system_metrics: Dict) -> float:
        """Calculate overall efficiency score"""
        worker_avg = np.mean(worker_efficiencies) if worker_efficiencies else 0
        zone_avg = np.mean(zone_efficiencies) if zone_efficiencies else 0
        system_eff = system_metrics.get('efficiency_score', 0)
        
        # Weighted average
        overall = (worker_avg * 0.4) + (zone_avg * 0.3) + (system_eff * 0.3)
        return max(0, min(overall, 1.0))
    
    def _calculate_health_score(self, productivity_report: Dict, bottleneck_report: Dict, 
                              efficiency_report: Dict) -> float:
        """Calculate overall health score (0-100)"""
        # Extract key metrics
        worker_eff = productivity_report['worker_productivity']['avg_efficiency']
        zone_util = productivity_report['zone_productivity']['avg_utilization']
        bottleneck_count = bottleneck_report['bottlenecks_detected']
        overall_eff = efficiency_report['overall_efficiency_score']
        
        # Calculate health score
        health_score = (worker_eff * 30) + (zone_util * 25) + (overall_eff * 35)
        
        # Penalize for bottlenecks
        bottleneck_penalty = min(bottleneck_count * 5, 10)
        health_score -= bottleneck_penalty
        
        return max(0, min(health_score, 100))
    
    def _determine_overall_status(self, productivity_report: Dict, bottleneck_report: Dict,
                                 efficiency_report: Dict) -> str:
        """Determine overall system status"""
        health_score = self._calculate_health_score(productivity_report, bottleneck_report, efficiency_report)
        
        if health_score >= 80:
            return "Excellent"
        elif health_score >= 65:
            return "Good"
        elif health_score >= 50:
            return "Fair"
        else:
            return "Poor"
    
    def _extract_highlights(self, productivity_report: Dict, bottleneck_report: Dict,
                          efficiency_report: Dict) -> List[str]:
        """Extract key highlights from reports"""
        highlights = []
        
        # Productivity highlights
        if productivity_report['worker_productivity']['avg_efficiency'] > 0.8:
            highlights.append("High worker efficiency maintained")
        
        if productivity_report['zone_productivity']['avg_utilization'] > 0.7:
            highlights.append("Good zone utilization across factory")
        
        # Bottleneck highlights
        if bottleneck_report['bottlenecks_detected'] == 0:
            highlights.append("No bottlenecks detected")
        
        # Efficiency highlights
        if efficiency_report['overall_efficiency_score'] > 0.8:
            highlights.append("Excellent overall system efficiency")
        
        return highlights
    
    def _extract_concerns(self, productivity_report: Dict, bottleneck_report: Dict,
                         efficiency_report: Dict) -> List[str]:
        """Extract key concerns from reports"""
        concerns = []
        
        # Productivity concerns
        if productivity_report['worker_productivity']['avg_efficiency'] < 0.5:
            concerns.append("Low worker efficiency detected")
        
        if productivity_report['zone_productivity']['avg_utilization'] < 0.4:
            concerns.append("Poor zone utilization")
        
        # Bottleneck concerns
        if bottleneck_report['bottlenecks_detected'] > 5:
            concerns.append("Multiple bottlenecks affecting operations")
        
        # Efficiency concerns
        if efficiency_report['overall_efficiency_score'] < 0.5:
            concerns.append("Low overall system efficiency")
        
        return concerns
    
    def _get_top_recommendations(self, recommendations: List[Dict]) -> List[str]:
        """Get top recommendations"""
        return [rec['recommendation'] for rec in recommendations[:3]]
    
    def _analyze_severity_distribution(self, bottlenecks: List[Dict]) -> Dict:
        """Analyze distribution of bottleneck severities"""
        if not bottlenecks:
            return {'high': 0, 'medium': 0, 'low': 0}
        
        severities = [b['severity_score'] for b in bottlenecks]
        
        return {
            'high': len([s for s in severities if s > 0.7]),
            'medium': len([s for s in severities if 0.4 <= s <= 0.7]),
            'low': len([s for s in severities if s < 0.4])
        }
    
    def _analyze_efficiency_by_zone_type(self, zone_data: Dict) -> Dict:
        """Analyze efficiency by zone type"""
        type_efficiencies = defaultdict(list)
        
        for zone_name, data in zone_data.items():
            productivity = self.productivity_analyzer.calculate_zone_productivity(data, zone_name, None)
            if productivity:
                type_efficiencies[productivity.zone_type].append(productivity.processing_efficiency)
        
        return {
            zone_type: {
                'avg_efficiency': np.mean(efficiencies),
                'zone_count': len(efficiencies)
            }
            for zone_type, efficiencies in type_efficiencies.items()
        }
    
    def _analyze_efficiency_trends(self, worker_data: Dict, zone_data: Dict) -> Dict:
        """Analyze efficiency trends (placeholder for time series analysis)"""
        return {
            'trend_direction': 'stable',  # Would need historical data
            'trend_percentage': 0.0,
            'data_points': len(worker_data) + len(zone_data)
        }
    
    # Additional helper methods for shift and weekly reports would go here
    # For brevity, including method signatures only
    
    def _analyze_shift_productivity(self, worker_data: Dict, zone_data: Dict) -> Dict:
        """Analyze productivity for specific shift"""
        return {}
    
    def _analyze_shift_bottlenecks(self, zone_data: Dict) -> Dict:
        """Analyze bottlenecks for specific shift"""
        return {}
    
    def _analyze_shift_efficiency(self, worker_data: Dict, zone_data: Dict) -> Dict:
        """Analyze efficiency for specific shift"""
        return {}
    
    def _generate_shift_recommendations(self, worker_data: Dict, zone_data: Dict) -> List[Dict]:
        """Generate recommendations for specific shift"""
        return []
    
    def _aggregate_weekly_data(self, daily_data: List[Dict]) -> Dict:
        """Aggregate data across multiple days"""
        return {}
    
    def _analyze_weekly_trends(self, daily_data: List[Dict]) -> Dict:
        """Analyze trends across the week"""
        return {}
    
    def _identify_improvement_areas(self, weekly_summary: Dict) -> List[str]:
        """Identify areas needing improvement"""
        return []
    
    def _calculate_weekly_kpis(self, weekly_summary: Dict) -> Dict:
        """Calculate weekly KPIs"""
        return {}
    
    def _generate_trend_charts(self, daily_data: List[Dict], week_str: str) -> Dict[str, str]:
        """Generate trend charts for weekly report"""
        return {}
