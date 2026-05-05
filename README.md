# DeltaVision - Factory Analytics for Bulletproof Vest Manufacturing

DeltaVision is a production-ready computer vision system designed to analyze CCTV footage from bulletproof vest manufacturing facilities. It provides real-time analytics, productivity metrics, bottleneck detection, and comprehensive reporting for optimizing factory operations.

## Key Features

- **Real-time Person Detection & Tracking**: Uses YOLOv8 and ByteTrack for anonymous worker tracking
- **Zone-based Analytics**: Define work zones (cutting, sewing, inspection, packing) and monitor occupancy
- **Productivity Metrics**: Calculate worker efficiency, zone utilization, and system throughput
- **Bottleneck Detection**: Identify congestion and queue buildup in real-time
- **Interactive Dashboards**: FastAPI backend with comprehensive analytics endpoints
- **Visual Analytics**: Heatmaps, time-series plots, and flow analysis
- **Production Ready**: Docker Compose setup with PostgreSQL, Redis, Grafana, and monitoring

## Factory-Specific Analytics

DeltaVision focuses on manufacturing flow optimization:

- **Material Flow Analysis**: Track movement from material racks → cutting → assembly → sewing → inspection → packing
- **Workstation Occupancy**: Monitor utilization of cutting tables, sewing lines, and inspection stations
- **Handoff Efficiency**: Measure delays between work zones
- **Walking Waste Analysis**: Identify excessive movement patterns
- **Queue Detection**: Alert when inspection or packing areas become congested

## Quick Start

### Prerequisites

- Python 3.11+
- PyCharm Professional (recommended) or Community Edition
- Docker & Docker Compose
- NVIDIA GPU with CUDA (optional, for better performance)
- 16GB+ RAM recommended

### PyCharm Setup

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd DeltaVision
   ```

2. **Open in PyCharm**
   - Open PyCharm
   - Select "Open" and choose the DeltaVision directory
   - PyCharm will detect the Python project structure

3. **Configure Virtual Environment**
   - Go to `File → Settings → Project: DeltaVision → Python Interpreter`
   - Click "Add Interpreter" → "New Environment"
   - Select "Virtualenv Environment"
   - Choose base interpreter: Python 3.11
   - Check "Inherit global site-packages"
   - Click OK to create

4. **Install Dependencies**
   ```bash
   # In PyCharm terminal or system terminal
   pip install -r requirements.txt
   ```

5. **Configure Project Structure**
   - Right-click on `app/` directory → "Mark Directory as" → "Sources Root"
   - This enables proper imports and code navigation

6. **Set Up Environment Variables**
   - Copy `.env.example` to `.env`
   - Edit `.env` with your configuration:
   ```bash
   cp .env.example .env
   # Edit .env with your database and API settings
   ```

7. **Create Run Configurations**

   **API Server:**
   - Go to `Run → Edit Configurations`
   - Click "+" → "Python"
   - Name: "DeltaVision API"
   - Script path: `app/main.py`
   - Parameters: `serve`
   - Python interpreter: Your project venv
   - Environment variables: Add env file or set manually

   **Video Processing:**
   - Name: "Process Video"
   - Script path: `app/main.py`
   - Parameters: `process-video ../vids/A11_20260406000000.mp4`

   **Database Init:**
   - Name: "Init Database"
   - Script path: `app/main.py`
   - Parameters: `init-db`

8. **Test Configuration**
   ```bash
   python app/main.py test-config
   ```

### Docker Setup (Recommended for Production)

1. **Start Services**
   ```bash
   docker-compose up -d
   ```

2. **Initialize Database**
   ```bash
   docker-compose exec api python app/main.py init-db
   ```

3. **Access Services**
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Grafana: http://localhost:3000 (admin/admin123)
   - PgAdmin: http://localhost:5050 (admin@deltavision.com/admin123)
   - Prometheus: http://localhost:9090

## Usage Examples

### Process Single Video
```bash
python app/main.py process-video ../vids/A11_20260406000000.mp4 --camera-id A11 --save-annotated
```

### Process Video Folder
```bash
python app/main.py process-folder ../vids --parallel 2
```

### Start API Server
```bash
python app/main.py serve --host 0.0.0.0 --port 8000
```

### Generate Daily Report
```bash
python app/main.py analyze --days 7
```

### Replay Day Analysis
```bash
python app/main.py replay-day 2024-01-15
```

## Project Structure

```
DeltaVision/
├── app/                          # Main application code
│   ├── main.py                   # CLI entry point
│   ├── config.py                 # Configuration management
│   ├── pipeline/                 # Video processing pipeline
│   │   ├── ingest.py            # Video ingestion
│   │   ├── detector.py          # Person detection (YOLO)
│   │   ├── tracker.py           # Object tracking (ByteTrack)
│   │   ├── zones.py             # Zone management
│   │   ├── metrics.py           # Metrics calculation
│   │   └── exporter.py          # Data export
│   ├── analytics/                # Analytics modules
│   │   ├── heatmaps.py          # Heatmap generation
│   │   ├── bottlenecks.py       # Bottleneck detection
│   │   ├── productivity.py      # Productivity analysis
│   │   └── reports.py          # Report generation
│   ├── api/                     # FastAPI server
│   │   └── server.py           # API endpoints
│   ├── db/                      # Database models
│   │   ├── models.py            # SQLAlchemy models
│   │   └── session.py          # Database session
│   └── utils/                   # Utility functions
│       ├── video.py             # Video processing utilities
│       └── geometry.py          # Geometric calculations
├── configs/                      # Configuration files
│   ├── cameras.yaml             # Camera configurations
│   ├── zones.json              # Zone definitions
│   ├── settings.yaml            # System settings
│   ├── nginx.conf              # Nginx configuration
│   ├── prometheus.yml          # Prometheus config
│   └── pgadmin-servers.json   # PgAdmin servers
├── data/                         # Data directories
│   ├── raw_video/              # Input videos
│   ├── processed/              # Processed outputs
│   └── exports/               # Analytics exports
├── tests/                        # Unit tests
├── vids/                         # Your video files
├── docker-compose.yml             # Docker services
├── Dockerfile                    # Container definition
├── requirements.txt              # Python dependencies
└── README.md                    # This file
```

## Configuration

### Camera Setup (configs/cameras.yaml)
```yaml
cameras:
  A11:
    id: "A11"
    name: "Camera A11 - Main Assembly Floor"
    fps: 30
    resolution:
      width: 1920
      height: 1080
    detection_threshold: 0.5
```

### Zone Definition (configs/zones.json)
```json
{
  "A11": [
    {
      "name": "material_rack",
      "description": "Raw material storage area",
      "polygon": [[100, 100], [400, 100], [400, 300], [100, 300]],
      "type": "storage",
      "expected_dwell_time": 30
    }
  ]
}
```

### System Settings (configs/settings.yaml)
```yaml
database:
  host: "localhost"
  port: 5432
  name: "deltavision"
  user: "deltavision_user"
  password: "deltavision_pass"

models:
  yolo:
    model_path: "yolov8n.pt"
    device: "cuda"
    confidence_threshold: 0.5
```

## API Endpoints

### Health & Status
- `GET /health` - System health check
- `GET /metrics/live` - Live system metrics

### Workers
- `GET /workers/active` - Get currently active workers
- `GET /workers/{track_id}` - Get worker details

### Zones
- `GET /zones` - Get all zone metrics
- `GET /zones/{zone_name}` - Get zone details
- `GET /heatmap/{camera_id}` - Generate zone heatmap

### Analytics
- `GET /analytics/productivity` - Productivity analytics
- `GET /analytics/bottlenecks` - Bottleneck analysis
- `GET /reports/daily` - Daily reports

### Processing
- `POST /process-video` - Start video processing
- `GET /process/{processing_id}/status` - Check processing status

## Testing

### Run All Tests
```bash
pytest
```

### Run with Coverage
```bash
pytest --cov=app --cov-report=html
```

### Run Specific Test Categories
```bash
pytest -m unit          # Unit tests only
pytest -m integration    # Integration tests only
pytest -m "not slow"    # Skip slow tests
```

### PyCharm Test Configuration
1. Go to `Run → Edit Configurations`
2. Click "+" → "pytest"
3. Name: "DeltaVision Tests"
4. Target: "Module name" → `tests`
5. Python interpreter: Your project venv
6. Add additional arguments: `--cov=app --cov-report=html`

## Performance Optimization

### GPU Acceleration
- Ensure CUDA is installed: `nvidia-smi`
- Install PyTorch with CUDA: `pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118`
- Set device to "cuda" in settings.yaml

### Memory Optimization
- Adjust frame_skip in camera config to reduce memory usage
- Use smaller YOLO models (yolov8n vs yolov8s)
- Limit batch sizes in processing settings

### RTX 4070 Optimization
```yaml
models:
  yolo:
    device: "cuda"
    model_path: "yolov8s.pt"  # Better accuracy for RTX 4070

processing:
  frame_batch_size: 32
  gpu_memory_fraction: 0.8
```

## Monitoring & Observability

### Grafana Dashboards
- System metrics (CPU, GPU, memory)
- Application performance (processing FPS, detection rates)
- Business metrics (worker efficiency, zone utilization)

### Prometheus Metrics
- `deltavision_processed_frames_total`
- `deltavision_detections_total`
- `deltavision_active_workers`
- `deltavision_zone_occupancy`

### Logging
- Structured JSON logging
- Configurable log levels
- File rotation and archival

## Security Considerations

- **Anonymous Tracking**: No facial recognition or personal identification
- **Data Privacy**: All worker identities are anonymized track IDs
- **Access Control**: Role-based API access
- **Network Security**: HTTPS/TLS encryption in production

## Troubleshooting

### Common Issues

**CUDA Out of Memory**
```bash
# Reduce batch size in settings.yaml
processing:
  frame_batch_size: 16
```

**YOLO Model Not Found**
```bash
# Models auto-download on first run
# Or manually download:
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
```

**Database Connection Failed**
```bash
# Check if PostgreSQL is running
docker-compose ps postgres
# Restart if needed
docker-compose restart postgres
```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python app/main.py serve --reload
```

### Performance Profiling
```bash
# Profile video processing
python -m cProfile -o profile.stats app/main.py process-video video.mp4
```

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Make changes with tests
4. Run tests: `pytest --cov=app`
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push branch: `git push origin feature/amazing-feature`
7. Open Pull Request

### Code Style
- Use Black for formatting: `black app/`
- Use flake8 for linting: `flake8 app/`
- Use mypy for type checking: `mypy app/`

## License

This project is proprietary software for DeltaVision factory analytics.

## Support

For technical support:
- Check troubleshooting section above
- Review logs in `logs/deltavision.log`
- Contact the development team

## Roadmap

### Phase 1 (Current)
- [x] Core detection and tracking
- [x] Zone-based analytics
- [x] Basic reporting
- [x] Docker deployment

### Phase 2 (Q2 2026)
- [ ] Advanced task recognition
- [ ] Predictive analytics
- [ ] Mobile dashboard
- [ ] Alert system integration

### Phase 3 (Q3 2026)
- [ ] Multi-site support
- [ ] Machine learning optimization
- [ ] Advanced reporting
- [ ] API v2

---

**DeltaVision** - Transforming factory operations through computer vision analytics.
