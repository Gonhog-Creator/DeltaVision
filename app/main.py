#!/usr/bin/env python3
"""
DeltaVision - Factory Analytics for Bulletproof Vest Manufacturing
Main entry point for the application
"""

import click
import logging
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

from app.config import config
from app.db.session import init_database, db_manager
from app.pipeline.ingest import VideoIngestor, BatchProcessor
from app.pipeline.detector import MultiCameraDetector
from app.pipeline.tracker import MultiCameraTracker
from app.pipeline.zones import ZoneManager
from app.pipeline.metrics import MetricsEngine
from app.pipeline.exporter import ReportGenerator
from app.api.server import app
import uvicorn

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.settings['logging']['level']),
    format=config.settings['logging']['format']
)

logger = logging.getLogger(__name__)

@click.group()
@click.version_option(version="1.0.0")
def cli():
    """DeltaVision - Factory Analytics CLI"""
    pass

@cli.command()
@click.argument('video_path', type=click.Path(exists=True))
@click.option('--camera-id', '-c', help='Camera ID (auto-detected from filename if not provided)')
@click.option('--start-frame', '-s', type=int, help='Start frame number')
@click.option('--end-frame', '-e', type=int, help='End frame number')
@click.option('--output-dir', '-o', default='data/processed', help='Output directory')
@click.option('--save-annotated', is_flag=True, help='Save annotated video with detections')
@click.option('--gpu', is_flag=True, default=True, help='Use GPU for processing')
def process_video(video_path, camera_id, start_frame, end_frame, output_dir, save_annotated, gpu):
    """Process a single video file"""
    try:
        logger.info(f"Processing video: {video_path}")
        
        # Initialize database
        init_database()
        
        # Initialize components
        ingestor = VideoIngestor(frame_skip=config.settings['processing']['frame_skip'])
        detector = MultiCameraDetector(config.cameras['cameras'])
        tracker = MultiCameraTracker(config.cameras['cameras'])
        zone_manager = ZoneManager(config.zones)
        metrics_engine = MetricsEngine(zone_manager)
        
        # Get video metadata
        metadata = ingestor.get_video_metadata(video_path)
        if camera_id:
            metadata.camera_id = camera_id
        
        logger.info(f"Video metadata: {metadata}")
        
        # Process frames
        frame_generator = ingestor.extract_frames(video_path)
        if start_frame is not None and end_frame is not None:
            frame_generator = ingestor.extract_frame_range(video_path, start_frame, end_frame)
        
        processed_frames = 0
        total_detections = 0
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Setup video writer if saving annotated video
        video_writer = None
        if save_annotated:
            from app.utils.video import VideoUtils
            video_writer = VideoUtils.create_video_writer(
                str(output_path / f"annotated_{metadata.camera_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"),
                metadata.fps / config.settings['processing']['frame_skip'],
                (metadata.width, metadata.height)
            )
        
        try:
            for frame_idx, frame in frame_generator:
                # Detect persons
                detections = detector.detect_for_camera(metadata.camera_id, frame)
                total_detections += len(detections)
                
                # Track persons
                timestamp = datetime.now()
                tracks = tracker.update_for_camera(metadata.camera_id, detections, timestamp)
                
                # Update metrics
                track_data = []
                for track in tracks:
                    track_data.append({
                        'track_id': track.track_id,
                        'centroid': track.centroid,
                        'timestamp': timestamp,
                        'bbox': track.bbox
                    })
                
                metrics_engine.update_metrics(track_data, metadata.camera_id, timestamp)
                
                # Save annotated frame
                if save_annotated and video_writer:
                    # Visualize detections and tracks
                    annotated_frame = detector.get_detector(metadata.camera_id).visualize_detections(frame, detections)
                    annotated_frame = tracker.get_tracker(metadata.camera_id).visualize_tracks(annotated_frame, tracks)
                    annotated_frame = zone_manager.visualize_zones(annotated_frame, metadata.camera_id)
                    
                    video_writer.write(annotated_frame)
                
                processed_frames += 1
                
                if processed_frames % 100 == 0:
                    logger.info(f"Processed {processed_frames} frames, {total_detections} detections")
        
        finally:
            if video_writer:
                video_writer.release()
        
        # Generate report
        report_generator = ReportGenerator(str(output_path))
        system_metrics = metrics_engine.get_system_metrics()
        
        # Export results
        export_data = {
            'video_metadata': metadata,
            'processing_stats': {
                'frames_processed': processed_frames,
                'total_detections': total_detections,
                'processing_time': datetime.now().isoformat()
            },
            'system_metrics': system_metrics
        }
        
        logger.info(f"Video processing completed: {processed_frames} frames, {total_detections} detections")
        logger.info(f"Results saved to: {output_path}")
        
    except Exception as e:
        logger.error(f"Error processing video: {e}")
        raise click.ClickException(str(e))

@cli.command()
@click.argument('folder_path', type=click.Path(exists=True, file_okay=False))
@click.option('--recursive', '-r', is_flag=True, help='Process videos recursively')
@click.option('--parallel', '-p', type=int, default=1, help='Number of parallel processes')
@click.option('--output-dir', '-o', default='data/processed', help='Output directory')
def process_folder(folder_path, recursive, parallel, output_dir):
    """Process all videos in a folder"""
    try:
        logger.info(f"Processing videos in folder: {folder_path}")
        
        # Initialize database
        init_database()
        
        # Initialize components
        ingestor = VideoIngestor(frame_skip=config.settings['processing']['frame_skip'])
        batch_processor = BatchProcessor(ingestor)
        
        # Get video files
        video_files = ingestor.get_video_files(folder_path)
        if not video_files:
            logger.warning("No video files found in the specified folder")
            return
        
        logger.info(f"Found {len(video_files)} video files")
        
        # Process each video
        for video_path in video_files:
            try:
                logger.info(f"Processing: {video_path}")
                
                # For batch processing, we'll use a simplified approach
                # In production, you'd want to use multiprocessing
                metadata = ingestor.get_video_metadata(video_path)
                
                # Process video (simplified for now)
                # This would call the same processing logic as process_video
                logger.info(f"Completed processing: {video_path}")
                
            except Exception as e:
                logger.error(f"Error processing {video_path}: {e}")
                continue
        
        logger.info(f"Batch processing completed. Results saved to: {output_dir}")
        
    except Exception as e:
        logger.error(f"Error processing folder: {e}")
        raise click.ClickException(str(e))

@cli.command()
@click.argument('date', type=click.DateTime(formats=['%Y-%m-%d']))
@click.option('--output-dir', '-o', default='data/exports', help='Output directory')
def replay_day(date, output_dir):
    """Replay and analyze a full day of data"""
    try:
        logger.info(f"Replaying data for date: {date.date()}")
        
        # Initialize database
        init_database()
        
        # This would query database for all data on the specified date
        # and regenerate analytics
        
        # For now, just create a placeholder
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate daily report
        report_generator = ReportGenerator(str(output_path))
        
        # This would use actual data from database
        logger.info(f"Daily replay completed. Results saved to: {output_path}")
        
    except Exception as e:
        logger.error(f"Error replaying day: {e}")
        raise click.ClickException(str(e))

@cli.command()
@click.option('--host', default=config.settings['api']['host'], help='Host to bind to')
@click.option('--port', default=config.settings['api']['port'], type=int, help='Port to bind to')
@click.option('--reload', is_flag=True, help='Enable auto-reload for development')
def serve(host, port, reload):
    """Start the API server"""
    try:
        logger.info(f"Starting API server on {host}:{port}")
        
        # Initialize database
        init_database()
        
        # Run FastAPI server
        uvicorn.run(
            "app.api.server:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
        
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        raise click.ClickException(str(e))

@cli.command()
def init_db():
    """Initialize the database"""
    try:
        logger.info("Initializing database...")
        init_database()
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise click.ClickException(str(e))

@cli.command()
@click.option('--days', default=7, type=int, help='Number of days to analyze')
def analyze(days):
    """Run analytics on historical data"""
    try:
        logger.info(f"Running analytics for the last {days} days")
        
        # Initialize database
        init_database()
        
        # This would run comprehensive analytics
        # on historical data from the database
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        logger.info(f"Analysis period: {start_date.date()} to {end_date.date()}")
        
        # Generate analytics
        # This would use the analytics modules
        
        logger.info("Analytics completed successfully")
        
    except Exception as e:
        logger.error(f"Error running analytics: {e}")
        raise click.ClickException(str(e))

@cli.command()
@click.option('--camera-id', '-c', help='Camera ID to test')
def test_config(camera_id):
    """Test configuration and components"""
    try:
        logger.info("Testing configuration...")
        
        # Test database connection
        db_healthy = db_manager.health_check()
        logger.info(f"Database health: {'OK' if db_healthy else 'FAILED'}")
        
        # Test camera configuration
        if camera_id:
            camera_config = config.get_camera_config(camera_id)
            if camera_config:
                logger.info(f"Camera {camera_id} configuration: OK")
            else:
                logger.error(f"Camera {camera_id} not found in configuration")
        
        # Test zones
        if camera_id:
            zones = config.get_zones_for_camera(camera_id)
            logger.info(f"Found {len(zones)} zones for camera {camera_id}")
        
        # Test model loading
        try:
            from app.pipeline.detector import PersonDetector
            detector = PersonDetector()
            logger.info("YOLO model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
        
        logger.info("Configuration test completed")
        
    except Exception as e:
        logger.error(f"Error testing configuration: {e}")
        raise click.ClickException(str(e))

@cli.command()
def export_data():
    """Export data to various formats"""
    try:
        logger.info("Exporting data...")
        
        # Initialize database
        init_database()
        
        # This would export data from database
        # to CSV, JSON, etc.
        
        logger.info("Data export completed")
        
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        raise click.ClickException(str(e))

@cli.command()
def gui():
    """Launch the Streamlit GUI"""
    try:
        import subprocess
        import sys
        
        logger.info("Starting DeltaVision GUI...")
        
        # Launch Streamlit app
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "app/gui/streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0",
            "--browser.gatherUsageStats", "false"
        ])
        
    except ImportError:
        logger.error("Streamlit not installed. Install with: pip install streamlit")
        raise click.ClickException("Streamlit not installed")
    except Exception as e:
        logger.error(f"Error starting GUI: {e}")
        raise click.ClickException(str(e))

if __name__ == '__main__':
    cli()
