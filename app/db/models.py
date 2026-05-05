from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class VideoMetadata(Base):
    """Video file metadata"""
    __tablename__ = "video_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False, index=True)
    camera_id = Column(String(50), nullable=False, index=True)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    duration = Column(Float)
    fps = Column(Float)
    frame_count = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    processed_at = Column(DateTime)
    is_processed = Column(Boolean, default=False)
    
    # Relationships
    detections = relationship("Detection", back_populates="video")
    
    def __repr__(self):
        return f"<VideoMetadata(filename='{self.filename}', camera_id='{self.camera_id}')>"

class Detection(Base):
    """Individual person detection"""
    __tablename__ = "detections"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("video_metadata.id"), nullable=False)
    frame_number = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    track_id = Column(Integer, index=True)
    camera_id = Column(String(50), nullable=False, index=True)
    
    # Bounding box coordinates
    bbox_x1 = Column(Float, nullable=False)
    bbox_y1 = Column(Float, nullable=False)
    bbox_x2 = Column(Float, nullable=False)
    bbox_y2 = Column(Float, nullable=False)
    
    # Detection confidence
    confidence = Column(Float, nullable=False)
    
    # Centroid coordinates
    centroid_x = Column(Float, nullable=False)
    centroid_y = Column(Float, nullable=False)
    
    # Movement metrics
    velocity = Column(Float)
    is_moving = Column(Boolean)
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    video = relationship("VideoMetadata", back_populates="detections")
    zone_visits = relationship("ZoneVisit", back_populates="detection")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_detection_video_frame', 'video_id', 'frame_number'),
        Index('idx_detection_camera_timestamp', 'camera_id', 'timestamp'),
        Index('idx_detection_track_time', 'track_id', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<Detection(track_id={self.track_id}, camera_id='{self.camera_id}', timestamp='{self.timestamp}')>"

class Zone(Base):
    """Defined zones in the factory"""
    __tablename__ = "zones"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    camera_id = Column(String(50), nullable=False, index=True)
    description = Column(Text)
    zone_type = Column(String(50), nullable=False, index=True)  # workstation, storage, transit, etc.
    expected_dwell_time = Column(Float)  # seconds
    
    # Polygon coordinates (stored as JSON string)
    polygon_coords = Column(Text, nullable=False)
    
    # Zone metrics
    area = Column(Float)
    centroid_x = Column(Float)
    centroid_y = Column(Float)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    visits = relationship("ZoneVisit", back_populates="zone")
    
    def __repr__(self):
        return f"<Zone(name='{self.name}', camera_id='{self.camera_id}', type='{self.zone_type}')>"

class ZoneVisit(Base):
    """Record of worker visiting a zone"""
    __tablename__ = "zone_visits"
    
    id = Column(Integer, primary_key=True, index=True)
    detection_id = Column(Integer, ForeignKey("detections.id"), nullable=False)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False)
    track_id = Column(Integer, nullable=False, index=True)
    camera_id = Column(String(50), nullable=False, index=True)
    
    # Timing
    entry_time = Column(DateTime, nullable=False, index=True)
    exit_time = Column(DateTime)
    dwell_time = Column(Float)  # seconds
    
    # Visit status
    is_active = Column(Boolean, default=True, index=True)
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    detection = relationship("Detection", back_populates="zone_visits")
    zone = relationship("Zone", back_populates="visits")
    
    # Indexes
    __table_args__ = (
        Index('idx_zone_visit_track_time', 'track_id', 'entry_time'),
        Index('idx_zone_visit_zone_time', 'zone_id', 'entry_time'),
    )
    
    def __repr__(self):
        return f"<ZoneVisit(track_id={self.track_id}, zone='{self.zone.name if self.zone else 'Unknown'}', dwell_time={self.dwell_time})>"

class WorkerMetrics(Base):
    """Aggregated metrics for each tracked worker"""
    __tablename__ = "worker_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    track_id = Column(Integer, nullable=False, index=True)
    camera_id = Column(String(50), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    
    # Time metrics
    total_time_tracked = Column(Float)  # seconds
    active_time = Column(Float)  # seconds (moving)
    idle_time = Column(Float)  # seconds (stationary)
    
    # Movement metrics
    total_distance = Column(Float)  # pixels
    average_velocity = Column(Float)
    max_velocity = Column(Float)
    
    # Zone metrics
    zones_visited = Column(Integer)
    zone_transitions = Column(Integer)
    
    # Productivity metrics
    work_zone_time = Column(Float)  # time in workstation zones
    transit_zone_time = Column(Float)  # time in transit zones
    
    # Quality metrics
    detection_confidence_avg = Column(Float)
    detection_confidence_min = Column(Float)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_worker_metrics_track_date', 'track_id', 'date'),
        Index('idx_worker_metrics_camera_date', 'camera_id', 'date'),
    )
    
    def __repr__(self):
        return f"<WorkerMetrics(track_id={self.track_id}, date='{self.date}', total_time={self.total_time_tracked})>"

class ZoneMetrics(Base):
    """Aggregated metrics for each zone"""
    __tablename__ = "zone_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False, index=True)
    camera_id = Column(String(50), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    
    # Occupancy metrics
    current_occupancy = Column(Integer, default=0)
    average_occupancy = Column(Float)
    peak_occupancy = Column(Integer)
    min_occupancy = Column(Integer)
    
    # Time metrics
    total_visits = Column(Integer)
    average_dwell_time = Column(Float)  # seconds
    total_dwell_time = Column(Float)  # seconds
    
    # Utilization metrics
    utilization_rate = Column(Float)  # 0-1
    bottleneck_score = Column(Float)  # 0-1
    
    # Flow metrics
    entries = Column(Integer)
    exits = Column(Integer)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    zone = relationship("Zone")
    
    # Indexes
    __table_args__ = (
        Index('idx_zone_metrics_zone_date', 'zone_id', 'date'),
        Index('idx_zone_metrics_camera_date', 'camera_id', 'date'),
    )
    
    def __repr__(self):
        return f"<ZoneMetrics(zone_id={self.zone_id}, date='{self.date}', utilization={self.utilization_rate})>"

class SystemMetrics(Base):
    """Overall system performance metrics"""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # Worker metrics
    total_active_workers = Column(Integer)
    total_tracks_created = Column(Integer)
    
    # Zone metrics
    total_zones = Column(Integer)
    active_zones = Column(Integer)
    bottleneck_zones = Column(Integer)  # count
    
    # Performance metrics
    system_utilization = Column(Float)  # 0-1
    average_throughput = Column(Float)  # transitions per minute
    efficiency_score = Column(Float)  # 0-1
    
    # Processing metrics
    frames_processed = Column(Integer)
    detections_made = Column(Integer)
    processing_fps = Column(Float)
    
    # Quality metrics
    average_detection_confidence = Column(Float)
    tracking_accuracy = Column(Float)  # if available
    
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<SystemMetrics(timestamp='{self.timestamp}', active_workers={self.total_active_workers}, efficiency={self.efficiency_score})>"

class ProcessingLog(Base):
    """Log of video processing sessions"""
    __tablename__ = "processing_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), nullable=False, unique=True, index=True)
    
    # Processing details
    video_files_processed = Column(Integer)
    total_frames_processed = Column(Integer)
    processing_start_time = Column(DateTime, nullable=False)
    processing_end_time = Column(DateTime)
    processing_duration = Column(Float)  # seconds
    
    # Performance metrics
    average_fps = Column(Float)
    peak_memory_usage = Column(Float)  # MB
    gpu_utilization = Column(Float)  # 0-1
    
    # Results
    total_detections = Column(Integer)
    total_tracks = Column(Integer)
    errors_count = Column(Integer)
    
    # Status
    status = Column(String(20), default="running")  # running, completed, failed
    error_message = Column(Text)
    
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<ProcessingLog(session_id='{self.session_id}', status='{self.status}', duration={self.processing_duration})>"
