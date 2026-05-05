import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator, Optional
import os

from app.config import config
from app.db.models import Base

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database connection and session management"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or config.database_url
        self.engine = None
        self.SessionLocal = None
        self._initialize_engine()
        
    def _initialize_engine(self):
        """Initialize database engine"""
        try:
            # Configure engine based on database type
            if self.database_url.startswith('sqlite'):
                self.engine = create_engine(
                    self.database_url,
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool,
                    echo=False
                )
            else:
                # PostgreSQL configuration
                self.engine = create_engine(
                    self.database_url,
                    pool_size=config.settings['database']['pool_size'],
                    max_overflow=config.settings['database']['max_overflow'],
                    echo=False
                )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info(f"Database engine initialized: {self.database_url}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise
    
    def create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all database tables"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("Database tables dropped successfully")
            
        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise
    
    def get_session(self) -> Session:
        """Get database session"""
        if self.SessionLocal is None:
            raise RuntimeError("Database not initialized")
        
        return self.SessionLocal()
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of operations"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database transaction failed: {e}")
            raise
        finally:
            session.close()
    
    def health_check(self) -> bool:
        """Check database connection health"""
        try:
            with self.session_scope() as session:
                from sqlalchemy import text
                session.execute(text("SELECT 1"))
            return True
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def get_connection_info(self) -> dict:
        """Get database connection information"""
        return {
            'database_url': self.database_url.split('@')[-1] if '@' in self.database_url else self.database_url,
            'pool_size': self.engine.pool.size() if hasattr(self.engine, 'pool') else None,
            'checked_out': self.engine.pool.checkedout() if hasattr(self.engine, 'pool') else None,
            'is_healthy': self.health_check()
        }

# Global database manager instance
db_manager = DatabaseManager()

# Dependency for FastAPI
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency to get database session"""
    with db_manager.session_scope() as session:
        yield session

class DatabaseService:
    """High-level database operations service"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db_manager = db_manager or db_manager
    
    def create_video_metadata(self, session: Session, video_data: dict) -> 'VideoMetadata':
        """Create video metadata record"""
        from app.db.models import VideoMetadata
        
        video = VideoMetadata(**video_data)
        session.add(video)
        session.flush()  # Get the ID without committing
        return video
    
    def create_detection(self, session: Session, detection_data: dict) -> 'Detection':
        """Create detection record"""
        from app.db.models import Detection
        
        detection = Detection(**detection_data)
        session.add(detection)
        session.flush()
        return detection
    
    def create_zone_visit(self, session: Session, visit_data: dict) -> 'ZoneVisit':
        """Create zone visit record"""
        from app.db.models import ZoneVisit
        
        visit = ZoneVisit(**visit_data)
        session.add(visit)
        session.flush()
        return visit
    
    def get_active_zone_visits(self, session: Session, track_id: int, camera_id: str) -> list:
        """Get active zone visits for a track"""
        from app.db.models import ZoneVisit
        
        return session.query(ZoneVisit).filter(
            ZoneVisit.track_id == track_id,
            ZoneVisit.camera_id == camera_id,
            ZoneVisit.is_active == True
        ).all()
    
    def update_zone_visit_exit(self, session: Session, visit_id: int, exit_time, dwell_time: float):
        """Update zone visit with exit time"""
        from app.db.models import ZoneVisit
        
        visit = session.query(ZoneVisit).filter(ZoneVisit.id == visit_id).first()
        if visit:
            visit.exit_time = exit_time
            visit.dwell_time = dwell_time
            visit.is_active = False
    
    def get_worker_metrics_for_date(self, session: Session, track_id: int, date) -> Optional['WorkerMetrics']:
        """Get worker metrics for specific date"""
        from app.db.models import WorkerMetrics
        
        return session.query(WorkerMetrics).filter(
            WorkerMetrics.track_id == track_id,
            WorkerMetrics.date == date
        ).first()
    
    def upsert_worker_metrics(self, session: Session, metrics_data: dict) -> 'WorkerMetrics':
        """Create or update worker metrics"""
        from app.db.models import WorkerMetrics
        
        existing = self.get_worker_metrics_for_date(
            session, 
            metrics_data['track_id'], 
            metrics_data['date']
        )
        
        if existing:
            # Update existing record
            for key, value in metrics_data.items():
                setattr(existing, key, value)
            session.flush()
            return existing
        else:
            # Create new record
            metrics = WorkerMetrics(**metrics_data)
            session.add(metrics)
            session.flush()
            return metrics
    
    def get_zone_metrics_for_date(self, session: Session, zone_id: int, date) -> Optional['ZoneMetrics']:
        """Get zone metrics for specific date"""
        from app.db.models import ZoneMetrics
        
        return session.query(ZoneMetrics).filter(
            ZoneMetrics.zone_id == zone_id,
            ZoneMetrics.date == date
        ).first()
    
    def upsert_zone_metrics(self, session: Session, metrics_data: dict) -> 'ZoneMetrics':
        """Create or update zone metrics"""
        from app.db.models import ZoneMetrics
        
        existing = self.get_zone_metrics_for_date(
            session,
            metrics_data['zone_id'],
            metrics_data['date']
        )
        
        if existing:
            # Update existing record
            for key, value in metrics_data.items():
                setattr(existing, key, value)
            session.flush()
            return existing
        else:
            # Create new record
            metrics = ZoneMetrics(**metrics_data)
            session.add(metrics)
            session.flush()
            return metrics
    
    def create_system_metrics(self, session: Session, metrics_data: dict) -> 'SystemMetrics':
        """Create system metrics record"""
        from app.db.models import SystemMetrics
        
        metrics = SystemMetrics(**metrics_data)
        session.add(metrics)
        session.flush()
        return metrics
    
    def get_recent_detections(self, session: Session, camera_id: str, limit: int = 100):
        """Get recent detections for camera"""
        from app.db.models import Detection
        
        return session.query(Detection).filter(
            Detection.camera_id == camera_id
        ).order_by(Detection.timestamp.desc()).limit(limit).all()
    
    def get_zone_statistics(self, session: Session, camera_id: str = None):
        """Get zone statistics"""
        from app.db.models import Zone, ZoneVisit, ZoneMetrics
        
        query = session.query(Zone)
        if camera_id:
            query = query.filter(Zone.camera_id == camera_id)
        
        zones = query.all()
        stats = {}
        
        for zone in zones:
            # Get recent visit count
            recent_visits = session.query(ZoneVisit).filter(
                ZoneVisit.zone_id == zone.id,
                ZoneVisit.entry_time >= func.datetime('now', '-1 day')
            ).count()
            
            # Get latest metrics
            latest_metrics = session.query(ZoneMetrics).filter(
                ZoneMetrics.zone_id == zone.id
            ).order_by(ZoneMetrics.date.desc()).first()
            
            stats[zone.name] = {
                'zone_type': zone.zone_type,
                'expected_dwell_time': zone.expected_dwell_time,
                'recent_visits': recent_visits,
                'latest_metrics': latest_metrics
            }
        
        return stats

# Global database service instance
db_service = DatabaseService()

# Initialize database on import
def init_database():
    """Initialize database tables"""
    try:
        db_manager.create_tables()
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

# Import required functions
from sqlalchemy import func
