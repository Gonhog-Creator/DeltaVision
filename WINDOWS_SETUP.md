# DeltaVision Windows Setup Guide

This guide provides step-by-step instructions for setting up DeltaVision on a Windows PC.

## Prerequisites

### System Requirements
- Windows 10/11 (64-bit)
- Python 3.11+ (recommended: 3.11.5)
- 16GB+ RAM (recommended)
- NVIDIA GPU with CUDA (optional, for better performance)
- 50GB+ free disk space

### Required Software
1. **Python 3.11+**
   - Download from https://www.python.org/downloads/
   - During installation, check "Add Python to PATH"
   - Verify installation: `python --version`

2. **Git**
   - Download from https://git-scm.com/download/win
   - Use default settings during installation

3. **PostgreSQL** (for database)
   - Download from https://www.postgresql.org/download/windows/
   - Remember your password during installation
   - Default port: 5432

4. **Docker Desktop** (optional, for containerized setup)
   - Download from https://www.docker.com/products/docker-desktop/

## Installation Steps

### 1. Clone Repository
```bash
git clone <repository-url>
cd DeltaVision
```

### 2. Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. GPU Support (Optional)
If you have an NVIDIA GPU, install CUDA-enabled PyTorch:
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### 5. Database Setup

#### Option A: Local PostgreSQL
1. Open pgAdmin (installed with PostgreSQL)
2. Create a new database named `deltavision`
3. Create a user with password:
   ```sql
   CREATE USER deltavision_user WITH PASSWORD 'deltavision_pass';
   GRANT ALL PRIVILEGES ON DATABASE deltavision TO deltavision_user;
   ```

#### Option B: Docker PostgreSQL
```bash
docker run -d --name postgres-deltavision -e POSTGRES_DB=deltavision -e POSTGRES_USER=deltavision_user -e POSTGRES_PASSWORD=deltavision_pass -p 5432:5432 postgres:15
```

### 6. Configuration Setup

1. **Copy Environment File**
   ```bash
   copy .env.example .env
   ```

2. **Edit .env file** (use Notepad or VS Code):
   ```env
   # Database Configuration
   DATABASE_HOST=localhost
   DATABASE_PORT=5432
   DATABASE_NAME=deltavision
   DATABASE_USER=deltavision_user
   DATABASE_PASSWORD=your_postgres_password

   # API Configuration
   API_HOST=0.0.0.0
   API_PORT=8000
   API_DEBUG=false

   # Model Configuration
   YOLO_MODEL_PATH=yolov8n.pt
   DEVICE=cuda  # Change to 'cpu' if no GPU

   # Paths
   VIDEO_DATA_PATH=../vids
   CONFIG_PATH=configs
   LOG_PATH=logs
   ```

### 7. Create Required Directories
```bash
mkdir data\raw_video
mkdir data\processed
mkdir data\exports
mkdir logs
mkdir vids
```

### 8. Initialize Database
```bash
python app/main.py init-db
```

### 9. Test Configuration
```bash
python app/main.py test-config
```

## Starting the Application

### Option 1: API Server Only
```bash
python app/main.py serve --host 0.0.0.0 --port 8000
```

### Option 2: GUI Application
```bash
python app/main.py gui
```

### Option 3: Docker Setup (Recommended for Production)
```bash
docker-compose up -d
```

## Verification Steps

1. **API Server Check**
   - Open browser: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

2. **GUI Application Check**
   - Open browser: http://localhost:8501

3. **Database Connection Test**
   ```bash
   python app/main.py test-config
   ```

## Project Structure (Windows)

```
DeltaVision\
├── app\                          # Main application code
│   ├── main.py                   # CLI entry point
│   ├── api\                      # FastAPI server
│   ├── pipeline\                 # Video processing pipeline
│   └── db\                       # Database models
├── configs\                      # Configuration files
│   ├── cameras.yaml              # Camera configurations
│   ├── zones.json               # Zone definitions
│   └── settings.yaml            # System settings
├── data\                         # Data directories
│   ├── raw_video\              # Input videos
│   ├── processed\              # Processed outputs
│   └── exports\               # Analytics exports
├── vids\                         # Your video files
├── venv\                         # Virtual environment
├── .env                          # Environment variables
├── requirements.txt              # Python dependencies
└── docker-compose.yml            # Docker services
```

## Common Windows Issues and Solutions

### Issue 1: Python not found in PATH
**Solution**: Reinstall Python with "Add Python to PATH" checked, or manually add to PATH:
```
C:\Users\YourUser\AppData\Local\Programs\Python\Python311
C:\Users\YourUser\AppData\Local\Programs\Python\Python311\Scripts
```

### Issue 2: PostgreSQL connection failed
**Solution**: Ensure PostgreSQL service is running:
1. Open Services (services.msc)
2. Find "postgresql-x64-15" (or similar)
3. Right-click → Start

### Issue 3: CUDA out of memory
**Solution**: Reduce GPU memory usage in `.env`:
```env
GPU_MEMORY_FRACTION=0.5
MAX_WORKERS=2
```

### Issue 4: YOLO model download fails
**Solution**: Manually download model:
```bash
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
```

### Issue 5: Permission denied on Windows
**Solution**: Run Command Prompt as Administrator or use PowerShell with elevated privileges.

## Development Setup

### Install Development Tools
```bash
pip install black flake8 mypy pytest pytest-cov
```

### Code Formatting
```bash
black app/
flake8 app/
mypy app/
```

### Run Tests
```bash
pytest
pytest --cov=app
```

## Performance Tips for Windows

1. **Use SSD Storage**: Place video files on SSD for faster I/O
2. **GPU Acceleration**: Use CUDA-enabled PyTorch if available
3. **Memory Management**: Adjust `GPU_MEMORY_FRACTION` in `.env`
4. **Parallel Processing**: Increase `MAX_WORKERS` based on CPU cores
5. **Antivirus Exclusions**: Add project folder to antivirus exclusions

## Troubleshooting Commands

### Check Python Environment
```bash
python --version
pip list
```

### Database Health Check
```bash
python app/main.py test-config
```

### Verify Model Loading
```bash
python -c "from ultralytics import YOLO; model = YOLO('yolov8n.pt'); print('Model loaded successfully')"
```

### Check API Server
```bash
curl http://localhost:8000/health
```

## Next Steps

1. **Add Video Files**: Place video files in `vids/` directory
2. **Configure Cameras**: Edit `configs/cameras.yaml`
3. **Define Zones**: Edit `configs/zones.json`
4. **Process Video**: `python app/main.py process-video vids/your_video.mp4`
5. **View Analytics**: Access GUI at http://localhost:8501

## Support

For technical support:
1. Check logs in `logs/deltavision.log`
2. Run `python app/main.py test-config` for diagnostics
3. Review troubleshooting section above
4. Contact development team for further assistance
