import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import uvicorn

from app.config import config
from app.db.session import get_db, db_manager
from app.analytics.reports import ReportGenerator
from app.analytics.productivity import ProductivityAnalyzer
from app.analytics.bottlenecks import BottleneckDetector
from app.analytics.heatmaps import HeatmapAnalyzer

logger = logging.getLogger(__name__)

# Pydantic models for API
class HealthResponse(BaseModel):
    status: str
    database: bool
    timestamp: datetime

class WorkerMetricsResponse(BaseModel):
    track_id: int
    efficiency_score: float
    productive_time: float
    transit_time: float
    idle_time: float
    tasks_completed: int
    zones_visited: int

class ZoneMetricsResponse(BaseModel):
    zone_name: str
    zone_type: str
    current_occupancy: int
    utilization_rate: float
    average_dwell_time: float
    bottleneck_score: float

class SystemMetricsResponse(BaseModel):
    timestamp: datetime
    total_active_workers: int
    system_utilization: float
    efficiency_score: float
    bottleneck_zones: List[str]

class ProcessingRequest(BaseModel):
    video_path: str
    camera_id: Optional[str] = None
    start_frame: Optional[int] = None
    end_frame: Optional[int] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting DeltaVision API server")
    try:
        # Initialize database
        db_manager.create_tables()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down DeltaVision API server")

# Create FastAPI app
app = FastAPI(
    title="DeltaVision API",
    description="Factory Analytics API for Bulletproof Vest Manufacturing",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.settings['api']['cors_origins'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize analytics components
report_generator = ReportGenerator()
productivity_analyzer = ProductivityAnalyzer()
bottleneck_detector = BottleneckDetector()
heatmap_analyzer = HeatmapAnalyzer()

@app.get("/", response_model=Dict)
async def root():
    """Root endpoint"""
    return {
        "message": "DeltaVision API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    db_healthy = db_manager.health_check()
    
    return HealthResponse(
        status="healthy" if db_healthy else "unhealthy",
        database=db_healthy,
        timestamp=datetime.now()
    )

@app.get("/metrics/live", response_model=SystemMetricsResponse)
async def get_live_metrics():
    """Get live system metrics"""
    try:
        # This would typically connect to real-time metrics
        # For now, returning mock data
        return SystemMetricsResponse(
            timestamp=datetime.now(),
            total_active_workers=15,
            system_utilization=0.75,
            efficiency_score=0.82,
            bottleneck_zones=["sewing_line", "inspection"]
        )
    except Exception as e:
        logger.error(f"Error getting live metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get live metrics")

@app.get("/metrics/daily")
async def get_daily_metrics(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    camera_id: Optional[str] = Query(None, description="Camera ID filter")
):
    """Get daily metrics"""
    try:
        if date:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        else:
            target_date = datetime.now().date()
        
        # This would query the database for daily metrics
        # For now, returning mock data
        return {
            "date": target_date.isoformat(),
            "camera_id": camera_id,
            "worker_metrics": {
                "total_workers": 25,
                "avg_efficiency": 0.78,
                "total_tasks_completed": 145
            },
            "zone_metrics": {
                "total_zones": 12,
                "avg_utilization": 0.72,
                "bottlenecks_detected": 2
            },
            "system_metrics": {
                "efficiency_score": 0.81,
                "throughput": 18.5,  # workers per hour
                "uptime": 0.98
            }
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        logger.error(f"Error getting daily metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get daily metrics")

@app.get("/workers/active", response_model=List[WorkerMetricsResponse])
async def get_active_workers():
    """Get currently active workers"""
    try:
        # This would query active workers from database
        # For now, returning mock data
        active_workers = [
            WorkerMetricsResponse(
                track_id=1,
                efficiency_score=0.85,
                productive_time=3600,
                transit_time=900,
                idle_time=300,
                tasks_completed=8,
                zones_visited=5
            ),
            WorkerMetricsResponse(
                track_id=2,
                efficiency_score=0.72,
                productive_time=3200,
                transit_time=1200,
                idle_time=600,
                tasks_completed=6,
                zones_visited=4
            )
        ]
        
        return active_workers
    except Exception as e:
        logger.error(f"Error getting active workers: {e}")
        raise HTTPException(status_code=500, detail="Failed to get active workers")

@app.get("/workers/{track_id}")
async def get_worker_details(track_id: int):
    """Get detailed information for a specific worker"""
    try:
        # This would query worker details from database
        # For now, returning mock data
        return {
            "track_id": track_id,
            "camera_id": "A11",
            "first_seen": datetime.now() - timedelta(hours=2),
            "last_seen": datetime.now(),
            "total_time_tracked": 7200,
            "current_zone": "sewing_line",
            "zone_history": [
                {"zone": "material_rack", "entry_time": datetime.now() - timedelta(hours=2), "dwell_time": 120},
                {"zone": "cutting_table", "entry_time": datetime.now() - timedelta(hours=1.8), "dwell_time": 600},
                {"zone": "sewing_line", "entry_time": datetime.now() - timedelta(hours=1), "dwell_time": 3600}
            ],
            "productivity_metrics": {
                "efficiency_score": 0.85,
                "tasks_completed": 8,
                "walking_distance": 1250,
                "idle_time": 300
            }
        }
    except Exception as e:
        logger.error(f"Error getting worker details: {e}")
        raise HTTPException(status_code=500, detail="Failed to get worker details")

@app.get("/zones", response_model=List[ZoneMetricsResponse])
async def get_zone_metrics(camera_id: Optional[str] = Query(None)):
    """Get metrics for all zones"""
    try:
        # This would query zone metrics from database
        # For now, returning mock data
        zones = [
            ZoneMetricsResponse(
                zone_name="material_rack",
                zone_type="storage",
                current_occupancy=2,
                utilization_rate=0.4,
                average_dwell_time=45,
                bottleneck_score=0.1
            ),
            ZoneMetricsResponse(
                zone_name="sewing_line",
                zone_type="workstation",
                current_occupancy=8,
                utilization_rate=0.9,
                average_dwell_time=420,
                bottleneck_score=0.7
            ),
            ZoneMetricsResponse(
                zone_name="inspection",
                zone_type="quality_control",
                current_occupancy=3,
                utilization_rate=0.75,
                average_dwell_time=180,
                bottleneck_score=0.3
            )
        ]
        
        if camera_id:
            # Filter by camera_id if provided
            pass  # Would implement filtering logic
        
        return zones
    except Exception as e:
        logger.error(f"Error getting zone metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get zone metrics")

@app.get("/zones/{zone_name}")
async def get_zone_details(zone_name: str):
    """Get detailed information for a specific zone"""
    try:
        # This would query zone details from database
        # For now, returning mock data
        return {
            "zone_name": zone_name,
            "zone_type": "workstation",
            "camera_id": "A11",
            "expected_dwell_time": 300,
            "current_metrics": {
                "occupancy": 8,
                "utilization_rate": 0.9,
                "average_dwell_time": 420,
                "throughput": 12.5,  # workers per hour
                "bottleneck_score": 0.7
            },
            "historical_metrics": {
                "daily_avg_utilization": 0.82,
                "peak_occupancy": 12,
                "avg_dwell_time": 380,
                "bottleneck_frequency": 3  # per day
            },
            "polygon_coords": [[450, 100], [750, 100], [750, 350], [450, 350]]
        }
    except Exception as e:
        logger.error(f"Error getting zone details: {e}")
        raise HTTPException(status_code=500, detail="Failed to get zone details")

@app.get("/heatmap/{camera_id}")
async def get_heatmap(camera_id: str, 
                     date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
                     metric: str = Query("position", description="Heatmap metric: position, velocity, activity")):
    """Generate heatmap for camera"""
    try:
        # This would generate actual heatmap using the heatmap analyzer
        # For now, returning a placeholder response
        heatmap_path = f"data/exports/heatmap_{camera_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        return {
            "camera_id": camera_id,
            "date": date or datetime.now().strftime("%Y-%m-%d"),
            "metric": metric,
            "heatmap_url": f"/exports/{heatmap_path.split('/')[-1]}",
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error generating heatmap: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate heatmap")

@app.get("/exports/{filename}")
async def get_export_file(filename: str):
    """Serve exported files"""
    try:
        file_path = f"data/exports/{filename}"
        return FileResponse(file_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")

@app.post("/process-video")
async def process_video(request: ProcessingRequest, background_tasks: BackgroundTasks):
    """Start video processing"""
    try:
        # This would start background video processing
        processing_id = f"proc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Add processing task to background
        background_tasks.add_task(
            process_video_background,
            processing_id,
            request.video_path,
            request.camera_id,
            request.start_frame,
            request.end_frame
        )
        
        return {
            "processing_id": processing_id,
            "status": "started",
            "message": "Video processing started",
            "video_path": request.video_path,
            "camera_id": request.camera_id
        }
    except Exception as e:
        logger.error(f"Error starting video processing: {e}")
        raise HTTPException(status_code=500, detail="Failed to start video processing")

@app.get("/process/{processing_id}/status")
async def get_processing_status(processing_id: str):
    """Get status of video processing"""
    try:
        # This would check processing status from database
        # For now, returning mock status
        return {
            "processing_id": processing_id,
            "status": "completed",  # running, completed, failed
            "progress": 100,
            "frames_processed": 5400,
            "total_frames": 5400,
            "detections_found": 1250,
            "tracks_created": 15,
            "started_at": datetime.now() - timedelta(minutes=10),
            "completed_at": datetime.now(),
            "error_message": None
        }
    except Exception as e:
        logger.error(f"Error getting processing status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get processing status")

@app.get("/reports/daily")
async def get_daily_report(date: Optional[str] = Query(None)):
    """Get daily report"""
    try:
        if date:
            target_date = datetime.strptime(date, "%Y-%m-%d")
        else:
            target_date = datetime.now()
        
        # This would generate actual report using report generator
        # For now, returning mock report data
        return {
            "date": target_date.strftime("%Y-%m-%d"),
            "summary": {
                "total_workers": 25,
                "avg_efficiency": 0.78,
                "total_zones": 12,
                "bottleneck_zones": 2,
                "efficiency_score": 0.81
            },
            "worker_performance": {
                "top_performers": [
                    {"track_id": 1, "efficiency": 0.92, "tasks_completed": 10},
                    {"track_id": 5, "efficiency": 0.88, "tasks_completed": 9}
                ],
                "low_performers": [
                    {"track_id": 3, "efficiency": 0.45, "tasks_completed": 3}
                ]
            },
            "zone_performance": {
                "most_utilized": [
                    {"zone": "sewing_line", "utilization": 0.92},
                    {"zone": "inspection", "utilization": 0.85}
                ],
                "least_utilized": [
                    {"zone": "material_rack", "utilization": 0.35}
                ]
            },
            "bottlenecks": [
                {
                    "zone": "sewing_line",
                    "severity": 0.7,
                    "type": "congestion",
                    "recommendation": "Consider adding capacity"
                }
            ],
            "recommendations": [
                "Optimize sewing line capacity",
                "Rebalance material rack workload",
                "Investigate inspection queue times"
            ]
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        logger.error(f"Error getting daily report: {e}")
        raise HTTPException(status_code=500, detail="Failed to get daily report")

@app.get("/analytics/productivity")
async def get_productivity_analytics(
    time_range: str = Query("day", description="Time range: hour, day, week"),
    camera_id: Optional[str] = Query(None)
):
    """Get productivity analytics"""
    try:
        # This would use productivity analyzer for real analytics
        return {
            "time_range": time_range,
            "camera_id": camera_id,
            "overall_productivity": {
                "efficiency_score": 0.78,
                "productivity_trend": "improving",  # improving, stable, declining
                "trend_percentage": 5.2
            },
            "worker_analytics": {
                "avg_efficiency": 0.78,
                "efficiency_distribution": {
                    "high": 8,  # > 0.8
                    "medium": 12,  # 0.5-0.8
                    "low": 5  # < 0.5
                },
                "top_performers": [
                    {"track_id": 1, "efficiency": 0.92},
                    {"track_id": 7, "efficiency": 0.89}
                ]
            },
            "zone_analytics": {
                "avg_utilization": 0.72,
                "utilization_by_type": {
                    "workstation": 0.85,
                    "storage": 0.45,
                    "transit": 0.68
                },
                "bottleneck_zones": ["sewing_line", "inspection"]
            },
            "recommendations": [
                "Focus on improving low-performer efficiency",
                "Address sewing line bottlenecks",
                "Optimize material rack utilization"
            ]
        }
    except Exception as e:
        logger.error(f"Error getting productivity analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get productivity analytics")

@app.get("/analytics/bottlenecks")
async def get_bottleneck_analytics(
    time_range: str = Query("day", description="Time range: hour, day, week"),
    severity_threshold: float = Query(0.5, description="Minimum severity score")
):
    """Get bottleneck analytics"""
    try:
        # This would use bottleneck detector for real analytics
        return {
            "time_range": time_range,
            "severity_threshold": severity_threshold,
            "summary": {
                "total_bottlenecks": 5,
                "active_bottlenecks": 2,
                "zones_affected": 3,
                "avg_severity": 0.65
            },
            "active_bottlenecks": [
                {
                    "zone": "sewing_line",
                    "type": "congestion",
                    "severity": 0.78,
                    "current_occupancy": 8,
                    "expected_occupancy": 4,
                    "duration": 1800,  # seconds
                    "recommendation": "Add parallel sewing station"
                },
                {
                    "zone": "inspection",
                    "type": "queue",
                    "severity": 0.62,
                    "current_occupancy": 4,
                    "expected_occupancy": 2,
                    "duration": 900,
                    "recommendation": "Optimize inspection process"
                }
            ],
            "historical_bottlenecks": [
                {
                    "zone": "packing",
                    "type": "congestion",
                    "severity": 0.55,
                    "resolved_at": datetime.now() - timedelta(hours=2),
                    "duration": 1200
                }
            ],
            "trends": {
                "bottleneck_frequency": "increasing",
                "avg_resolution_time": 1800,
                "most_affected_zones": ["sewing_line", "inspection"]
            }
        }
    except Exception as e:
        logger.error(f"Error getting bottleneck analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get bottleneck analytics")

# Background task for video processing
async def process_video_background(processing_id: str, video_path: str, 
                                 camera_id: Optional[str], 
                                 start_frame: Optional[int], 
                                 end_frame: Optional[int]):
    """Background task for video processing"""
    try:
        logger.info(f"Starting video processing: {processing_id}")
        
        # This would implement actual video processing pipeline
        # For now, just logging
        await asyncio.sleep(5)  # Simulate processing time
        
        logger.info(f"Completed video processing: {processing_id}")
        
    except Exception as e:
        logger.error(f"Error in video processing {processing_id}: {e}")

# Import asyncio for background task
import asyncio

if __name__ == "__main__":
    uvicorn.run(
        "app.api.server:app",
        host=config.settings['api']['host'],
        port=config.settings['api']['port'],
        reload=config.settings['api']['debug'],
        log_level="info"
    )
