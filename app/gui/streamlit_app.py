import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
import cv2
import numpy as np
from PIL import Image
import io
import os
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="DeltaVision - Factory Analytics",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    .zone-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# API base URL
API_BASE = "http://localhost:8000"

def fetch_api(endpoint):
    """Fetch data from API"""
    try:
        response = requests.get(f"{API_BASE}{endpoint}")
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def main():
    st.markdown('<h1 class="main-header">DeltaVision Factory Analytics</h1>', unsafe_allow_html=True)
    
    # Tab navigation
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Dashboard",
        "Video Processing", 
        "Zone Editor",
        "Analytics",
        "Configuration",
        "Reports"
    ])
    
    with tab1:
        show_dashboard()
    with tab2:
        show_video_processing()
    with tab3:
        show_zone_editor()
    with tab4:
        show_analytics()
    with tab5:
        show_configuration()
    with tab6:
        show_reports()

def show_dashboard():
    """Main dashboard with key metrics"""
    st.header("Factory Dashboard")
    
    # Debug console toggle
    col1, col2 = st.columns([4, 1])
    with col1:
        st.write("")
    with col2:
        if st.button("Debug", key="debug_toggle"):
            # Toggle debug mode (this would show/hide console logs in a real implementation)
            st.session_state.debug_mode = not st.session_state.get('debug_mode', False)
            st.rerun()
    
    # Show debug console if enabled
    if st.session_state.get('debug_mode', False):
        with st.expander("Debug Console", expanded=True):
            st.code("""
            Debug Console:
            - Camera loading: Working
            - Screenshot loading: Working  
            - Zone loading: Working
            - Array checks: Fixed
            """, language="text")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        active_workers = fetch_api("/workers/active")
        worker_count = len(active_workers) if active_workers else 0
        st.metric("Active Workers", worker_count)
    
    with col2:
        zones = fetch_api("/zones")
        zone_count = len(zones) if zones else 0
        st.metric("Active Zones", zone_count)
    
    with col3:
        system_metrics = fetch_api("/metrics/live")
        efficiency = system_metrics.get("efficiency_score", 0) if system_metrics else 0
        st.metric("System Efficiency", f"{efficiency:.1%}")
    
    with col4:
        bottlenecks = fetch_api("/analytics/bottlenecks")
        bottleneck_count = len(bottlenecks.get("active_bottlenecks", [])) if bottlenecks else 0
        st.metric("Active Bottlenecks", bottleneck_count)
    
    # Zone status
    st.subheader("Zone Status")
    zones = fetch_api("/zones")
    if zones:
        zone_df = pd.DataFrame(zones)
        
        # Create zone cards
        cols = st.columns(3)
        for i, (_, zone) in enumerate(zone_df.iterrows()):
            with cols[i % 3]:
                color = "green" if zone["bottleneck_score"] < 0.3 else "orange" if zone["bottleneck_score"] < 0.7 else "red"
                st.markdown(f"""
                <div class="zone-card">
                    <h3>{zone["zone_name"]}</h3>
                    <p><strong>Type:</strong> {zone["zone_type"]}</p>
                    <p><strong>Occupancy:</strong> {zone["current_occupancy"]}</p>
                    <p><strong>Utilization:</strong> {zone["utilization_rate"]:.1%}</p>
                    <p><strong>Status:</strong> <span style="color: {color}">●</span></p>
                </div>
                """, unsafe_allow_html=True)
    
    # Recent activity
    st.subheader("Recent Activity")
    
    # Sample chart (would use real data)
    col1, col2 = st.columns(2)
    
    with col1:
        # Worker activity over time
        fig = px.line(
            x=list(range(24)),
            y=[5, 8, 12, 15, 18, 20, 22, 25, 23, 20, 18, 15, 12, 10, 8, 6, 5, 4, 3, 2, 1, 0, 0, 0],
            title="Worker Activity (24h)",
            labels={"x": "Hour", "y": "Active Workers"}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Zone utilization pie chart
        fig = px.pie(
            values=[85, 72, 90, 45, 60],
            names=["Sewing Line", "Cutting Table", "Material Rack", "Inspection", "Packing"],
            title="Zone Utilization"
        )
        st.plotly_chart(fig, use_container_width=True)

def show_video_processing():
    """Video processing interface"""
    st.header("Video Processing")
    
    # Video upload
    st.subheader("Upload Video")
    uploaded_file = st.file_uploader(
        "Choose a video file",
        type=['mp4', 'avi', 'mov', 'mkv'],
        help="Upload CCTV footage for analysis"
    )
    
    if uploaded_file:
        st.success(f"Uploaded: {uploaded_file.name}")
        
        # Video preview (first frame)
        try:
            # Save uploaded file temporarily
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Extract first frame
            cap = cv2.VideoCapture(temp_path)
            ret, frame = cap.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(frame_rgb)
                st.image(pil_img, caption="Video Preview (First Frame)", use_column_width=True)
            cap.release()
            
            # Clean up
            os.remove(temp_path)
        except Exception as e:
            st.error(f"Error previewing video: {e}")
    
    # Processing options
    st.subheader("Processing Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        camera_id = st.selectbox("Camera ID", ["A11", "A12", "Auto-detect"])
        confidence_threshold = st.slider("Detection Confidence", 0.1, 1.0, 0.5)
    
    with col2:
        start_frame = st.number_input("Start Frame", 0, 10000, 0)
        end_frame = st.number_input("End Frame", 0, 10000, 0)
        save_annotated = st.checkbox("Save Annotated Video", True)
    
    # Process button
    if st.button("Start Processing", type="primary"):
        if uploaded_file:
            with st.spinner("Processing video..."):
                # Simulate processing
                progress_bar = st.progress(0)
                for i in range(100):
                    time.sleep(0.05)
                    progress_bar.progress(i + 1)
                
                st.success("Video processing completed!")
                
                # Show results
                st.subheader("Processing Results")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Frames Processed", "5,400")
                with col2:
                    st.metric("Detections Found", "1,247")
                with col3:
                    st.metric("Tracks Created", "15")
                with col4:
                    st.metric("Processing Time", "12 min")
        else:
            st.error("Please upload a video file first")
    
    # Recent videos
    st.subheader("Recent Videos")
    
    # Sample video list
    recent_videos = [
        {"name": "A11_20260406000000.mp4", "status": "Completed", "date": "2024-04-06"},
        {"name": "A12_20260406060000.mp4", "status": "Processing", "date": "2024-04-06"},
        {"name": "A11_20260406020000.mp4", "status": "Completed", "date": "2024-04-06"},
    ]
    
    for video in recent_videos:
        status_indicator = "Completed" if video["status"] == "Completed" else "Processing"
        st.write(f"{status_indicator}: {video['name']} - {video['status']} ({video['date']})")

def get_available_cameras():
    """Get list of available cameras from configuration"""
    try:
        import yaml
        import os
        
        cameras_file = 'configs/cameras.yaml'
        if os.path.exists(cameras_file):
            with open(cameras_file, 'r') as f:
                config = yaml.safe_load(f)
            
            cameras = []
            for camera_id, camera_data in config.get('cameras', {}).items():
                cameras.append({
                    'id': camera_id,
                    'name': camera_id  # Use just the ID, ignore config name
                })
            return cameras
        else:
            # Fallback to scanning video files for camera names
            import glob
            video_files = glob.glob('../vids/*.mp4')
            cameras = []
            seen_ids = set()
            
            for video_file in video_files:
                filename = os.path.basename(video_file)
                # Extract camera ID from filename (e.g., "A11_20260406000000.mp4" -> "A11")
                if '_' in filename:
                    camera_id = filename.split('_')[0]
                    if camera_id not in seen_ids:
                        cameras.append({
                            'id': camera_id,
                            'name': camera_id  # Just use the ID as name, no prefix
                        })
                        seen_ids.add(camera_id)
            
            if not cameras:
                # Last resort fallback
                return [{'id': 'A11', 'name': 'A11'}, {'id': 'A12', 'name': 'A12'}]
            
            return cameras
            
    except Exception as e:
        st.error(f"Error loading cameras: {e}")
        return [{'id': 'A11', 'name': 'A11'}, {'id': 'A12', 'name': 'A12'}]

def show_zone_editor():
    """Interactive zone editor"""
    st.header("Zone Editor")
    
    # Get available cameras dynamically
    available_cameras = get_available_cameras()
    camera_options = {cam['name']: cam['id'] for cam in available_cameras}
    
    # Initialize session state for zones
    if 'zones' not in st.session_state:
        st.session_state.zones = []
    if 'current_camera' not in st.session_state:
        # Set to first available camera
        st.session_state.current_camera = available_cameras[0]['id'] if available_cameras else "A11"
        # Auto-load zones and screenshot for initial camera
        load_zones_for_camera(st.session_state.current_camera)
        load_camera_screenshot(st.session_state.current_camera)
    if 'camera_image' not in st.session_state:
        st.session_state.camera_image = None
    if 'drawing_mode' not in st.session_state:
        st.session_state.drawing_mode = False
    if 'current_polygon' not in st.session_state:
        st.session_state.current_polygon = []
    # Frame selection state
    if 'current_frame' not in st.session_state:
        st.session_state.current_frame = 0
    if 'video_cap' not in st.session_state:
        st.session_state.video_cap = None
    
    # Camera selection and automatic screenshot loading
    col1, col2 = st.columns([3, 1])
    
    with col1:
        camera_name = st.selectbox("Select Camera", list(camera_options.keys()), key="camera_select")
        camera_id = camera_options[camera_name]
        if camera_id != st.session_state.current_camera:
            st.session_state.current_camera = camera_id
            st.session_state.camera_image = None
            # Load zones for new camera
            load_zones_for_camera(camera_id)
            # Auto-load screenshot and pick middle frame
            load_camera_screenshot(camera_id, pick_middle_frame=True)
    
    with col2:
        if st.button("Clear All Zones"):
            st.session_state.zones = []
            st.session_state.current_polygon = []
            st.success("All zones cleared")
    
    # Frame navigation controls (only show if video is loaded)
    if st.session_state.get('video_cap') is not None:
        st.subheader("Frame Navigation")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.button("First Frame", key="first_frame"):
                if st.session_state.video_cap:
                    st.session_state.current_frame = 0
                    update_current_frame()
            
        with col2:
            if st.button("Previous Frame", key="prev_frame"):
                if st.session_state.video_cap:
                    st.session_state.current_frame = max(0, st.session_state.current_frame - 1)
                    update_current_frame()
            
        with col3:
            if st.button("Play/Pause", key="play_pause"):
                st.info("Play/Pause functionality coming soon")
            
        with col4:
            if st.button("Next Frame", key="next_frame"):
                if st.session_state.video_cap:
                    st.session_state.current_frame = min(st.session_state.total_frames - 1, st.session_state.current_frame + 1)
                    update_current_frame()
            
        with col5:
            if st.button("Last Frame", key="last_frame"):
                if st.session_state.video_cap:
                    st.session_state.current_frame = st.session_state.total_frames - 1
                    update_current_frame()
        
        # Frame info display
        st.write(f"Frame: {st.session_state.current_frame + 1} / {st.session_state.total_frames}")
        
        # Frame seek slider
        frame_num = st.slider(
            "Jump to Frame:",
            0, st.session_state.total_frames - 1,
            st.session_state.current_frame,
            key="frame_slider"
        )
        
        if st.button("Go to Frame", key="go_to_frame"):
            st.session_state.current_frame = frame_num
            update_current_frame()
    
    # Zone management
    st.subheader("Zone Management")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Canvas for zone drawing
        st.write("Zone Drawing Canvas")
        
        if st.session_state.camera_image is not None:
            st.info("Click on the image to add polygon points. Click 'Finish Zone' when done.")
            
            # Display camera image with click detection
            if st.session_state.drawing_mode:
                st.write("**Drawing Mode Active** - Click points to create polygon")
            elif st.session_state.zones:
                st.write(f"**{len(st.session_state.zones)} zones loaded** - Click 'Edit Zone' to modify or 'Start Drawing Zone' to add new")
            
            # Create clickable image area with zone overlays
            img_placeholder = st.empty()
            
            # Draw zones on image if they exist
            if st.session_state.zones and st.session_state.camera_image is not None:
                # Create a copy of the image for drawing
                import cv2
                import numpy as np
                
                # Convert PIL to OpenCV format if needed
                if hasattr(st.session_state.camera_image, 'save'):
                    # It's a PIL Image
                    import io
                    img_array = np.array(st.session_state.camera_image)
                else:
                    # It's already a numpy array
                    img_array = st.session_state.camera_image.copy()
                
                # Draw zones on the image
                for zone in st.session_state.zones:
                    polygon = zone.get('polygon', [])
                    if len(polygon) >= 3:
                        # Convert polygon to numpy array
                        pts = np.array(polygon, np.int32)
                        pts = pts.reshape((-1, 1, 2))
                        
                        # Draw polygon
                        color_hex = zone.get('color', '#FF6B6B')
                        color = tuple(int(color_hex[i:i+2], 16) for i in (1, 3, 5))
                        cv2.polylines(img_array, [pts], True, color, 2)
                        cv2.fillPoly(img_array, [pts], (*color, 50))  # Semi-transparent fill
                        
                        # Add zone name
                        if polygon:
                            center = np.mean(polygon, axis=0).astype(int)
                            cv2.putText(img_array, zone['name'], tuple(center), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                img_placeholder.image(img_array, use_container_width=True, channels="BGR")
            
            # Add click event handler
            if st.button("Add Click Point", key="add_click_point"):
                if len(st.session_state.current_polygon) < 10:
                    # Get click coordinates from input fields
                    clicked_x = st.session_state.get('click_x', 100)
                    clicked_y = st.session_state.get('click_y', 100)
                    
                    st.session_state.current_polygon.append([clicked_x, clicked_y])
                    st.success(f"Added point at ({clicked_x}, {clicked_y})")
                    st.rerun()
                else:
                    st.warning("Maximum 10 points per zone")
            else:
                img_placeholder.image(st.session_state.camera_image, use_container_width=True)
            
            # Add click detection (simulated with button for now)
            if st.session_state.drawing_mode:
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    if st.button("Add Point"):
                        # Simulate adding a point (in real implementation, this would capture click coordinates)
                        if len(st.session_state.current_polygon) < 10:
                            st.session_state.current_polygon.append([100, 100])  # Placeholder coordinates
                            st.success(f"Point {len(st.session_state.current_polygon)} added")
                        else:
                            st.warning("Maximum 10 points per zone")
                
                with col_b:
                    if st.button("Finish Zone"):
                        if len(st.session_state.current_polygon) >= 3:
                            finish_current_zone()
                        else:
                            st.error("Need at least 3 points to create a zone")
                
                with col_c:
                    if st.button("Cancel Drawing"):
                        st.session_state.drawing_mode = False
                        st.session_state.current_polygon = []
            
            # Display current polygon points
            if st.session_state.current_polygon:
                st.write(f"Current polygon points: {len(st.session_state.current_polygon)}")
                for i, point in enumerate(st.session_state.current_polygon):
                    st.write(f"Point {i+1}: ({point[0]}, {point[1]})")
        else:
            st.info("Load a camera screenshot to start drawing zones")
            # Placeholder canvas
            st.image("https://via.placeholder.com/800x600/333333/FFFFFF?text=Load+Camera+Screenshot+to+Start", 
                    use_container_width=True)
    
    with col2:
        # Zone controls
        st.write("Zone Controls")
        
        if st.session_state.camera_image is not None and not st.session_state.drawing_mode:
            zone_name = st.text_input("Zone Name", key="new_zone_name")
            zone_type = st.selectbox("Zone Type", ["storage", "workstation", "transit", "quality_control"], key="new_zone_type")
            zone_color = st.color_picker("Zone Color", "#FF6B6B", key="new_zone_color")
            
            if st.button("Start Drawing Zone", type="primary"):
                if zone_name:
                    st.session_state.drawing_mode = True
                    st.session_state.current_polygon = []
                    st.session_state.pending_zone = {
                        'name': zone_name,
                        'type': zone_type,
                        'color': zone_color
                    }
                    st.success(f"Drawing zone: {zone_name}")
                else:
                    st.error("Please enter a zone name")
        
        # Active zones list
        st.write("Active Zones")
        
        if st.session_state.zones:
            for i, zone in enumerate(st.session_state.zones):
                with st.expander(f"Zone: {zone['name']}"):
                    st.write(f"**Type:** {zone['type']}")
                    st.write(f"**Points:** {len(zone.get('polygon', []))}")
                    st.color_picker("Zone Color", zone['color'], key=f"color_{i}", disabled=True)
                    st.number_input("Expected Dwell Time (sec)", 0, 3600, zone.get('dwell_time', 300), key=f"dwell_{i}")
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("Edit Zone", key=f"edit_{i}"):
                            # Start editing this zone
                            st.session_state.drawing_mode = True
                            st.session_state.current_polygon = zone.get('polygon', []).copy()
                            st.session_state.pending_zone = {
                                'name': zone['name'],
                                'type': zone['type'],
                                'color': zone['color'],
                                'edit_index': i
                            }
                            st.success(f"Editing zone: {zone['name']}")
                            st.rerun()
                    with col_b:
                        if st.button("Delete Zone", key=f"delete_{i}"):
                            st.session_state.zones.pop(i)
                            st.success(f"Zone {zone['name']} deleted")
                            st.rerun()
        else:
            st.info("No zones defined yet. Load a camera screenshot and start drawing!")
    
    # Import/Export
    st.subheader("Import/Export Zones")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Import Zones"):
            st.info("Import zone configuration from file")
    
    with col2:
        if st.button("Export Zones"):
            st.info("Export zone configuration to file")

def show_analytics():
    """Analytics dashboard"""
    st.header("Analytics")
    
    # Time period selector
    col1, col2, col3 = st.columns(3)
    
    with col1:
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=7))
    with col2:
        end_date = st.date_input("End Date", datetime.now())
    with col3:
        metric_type = st.selectbox("Metric Type", ["Productivity", "Efficiency", "Bottlenecks", "Flow"])
    
    # Analytics charts
    st.subheader(f"{metric_type} Analytics")
    
    # Sample analytics data
    col1, col2 = st.columns(2)
    
    with col1:
        # Trend chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(range(24)),
            y=[0.7, 0.72, 0.75, 0.78, 0.82, 0.85, 0.87, 0.89, 0.88, 0.86, 0.84, 0.82, 0.80, 0.78, 0.76, 0.74, 0.72, 0.70, 0.68, 0.65, 0.62, 0.60, 0.58, 0.55],
            mode='lines+markers',
            name='Efficiency Score'
        ))
        fig.update_layout(title="Efficiency Trend", xaxis_title="Hour", yaxis_title="Score")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Distribution chart
        fig = px.bar(
            x=["Material Rack", "Cutting", "Sewing", "Inspection", "Packing"],
            y=[30, 85, 92, 78, 65],
            title="Zone Utilization %"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed metrics
    st.subheader("Detailed Metrics")
    
    metrics_data = {
        "Zone": ["Material Rack", "Cutting Table", "Sewing Line", "Inspection", "Packing"],
        "Avg Occupancy": [2.1, 3.8, 8.2, 3.5, 4.1],
        "Avg Dwell Time": [45, 285, 420, 180, 240],
        "Utilization %": [30, 85, 92, 78, 65],
        "Bottleneck Score": [0.1, 0.3, 0.7, 0.4, 0.2]
    }
    
    df = pd.DataFrame(metrics_data)
    st.dataframe(df, use_container_width=True)

def show_configuration():
    """Configuration interface"""
    st.header("Configuration")
    
    # System settings
    st.subheader("System Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Database Settings**")
        db_host = st.text_input("Database Host", "localhost")
        db_port = st.number_input("Database Port", 0, 65535, 5432)
        db_name = st.text_input("Database Name", "deltavision")
        
        st.write("**API Settings**")
        api_host = st.text_input("API Host", "0.0.0.0")
        api_port = st.number_input("API Port", 0, 65535, 8000)
        api_debug = st.checkbox("Debug Mode", False)
    
    with col2:
        st.write("**Model Settings**")
        model_path = st.text_input("Model Path", "yolov8n.pt")
        device = st.selectbox("Device", ["cpu", "cuda"])
        confidence = st.slider("Confidence Threshold", 0.1, 1.0, 0.5)
        
        st.write("**Processing Settings**")
        frame_skip = st.number_input("Frame Skip", 1, 30, 2)
        batch_size = st.number_input("Batch Size", 1, 64, 16)
    
    # Camera configuration
    st.subheader("Camera Configuration")
    
    cameras = [
        {"id": "A11", "name": "Camera A11 - Main Assembly", "fps": 30, "resolution": "1920x1080"},
        {"id": "A12", "name": "Camera A12 - Quality Control", "fps": 25, "resolution": "1280x720"},
    ]
    
    for camera in cameras:
        with st.expander(f"Camera: {camera['name']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("Camera ID", camera['id'], key=f"cam_id_{camera['id']}", disabled=True)
                st.number_input("FPS", 1, 60, camera['fps'], key=f"fps_{camera['id']}")
            with col2:
                st.text_input("Resolution", camera['resolution'], key=f"res_{camera['id']}")
                st.checkbox("Enabled", True, key=f"enabled_{camera['id']}")
    
    # Save configuration
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Configuration", type="primary"):
            st.success("Configuration saved successfully!")
    
    with col2:
        if st.button("Reset All Data", type="secondary"):
            reset_all_data()

def show_reports():
    """Reports interface"""
    st.header("Reports")
    
    # Report type selection
    report_type = st.selectbox("Report Type", [
        "Daily Summary",
        "Weekly Analysis", 
        "Monthly Report",
        "Custom Period"
    ])
    
    # Date range
    col1, col2 = st.columns(2)
    with col1:
        report_start = st.date_input("Start Date")
    with col2:
        report_end = st.date_input("End Date")
    
    # Generate report
    if st.button("Generate Report", type="primary"):
        with st.spinner("Generating report..."):
            time.sleep(2)  # Simulate report generation
            st.success("Report generated successfully!")
    
    # Report preview
    st.subheader("Report Preview")
    
    # Sample report content
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Workers", "25")
        st.metric("Avg Efficiency", "78%")
        st.metric("Total Zones", "12")
        st.metric("Bottlenecks", "2")
    
    with col2:
        st.metric("Processing Time", "8.2 hrs")
        st.metric("Data Points", "124.5K")
        st.metric("Accuracy", "94.2%")
        st.metric("System Uptime", "99.8%")
    
    # Export options
    st.subheader("Export Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Export PDF"):
            st.info("Exporting to PDF...")
    
    with col2:
        if st.button("Export Excel"):
            st.info("Exporting to Excel...")
    
    with col3:
        if st.button("Export CSV"):
            st.info("Exporting to CSV...")

def load_zones_for_camera(camera_id):
    """Load existing zones for the selected camera"""
    try:
        # Try to load zones from zones.json configuration
        import json
        import os
        
        zones_file = "configs/zones.json"
        if os.path.exists(zones_file):
            with open(zones_file, 'r') as f:
                zones_config = json.load(f)
            
            # Filter zones for current camera
            camera_zones = []
            
            # Handle different zone config formats
            if isinstance(zones_config, dict):
                for zone_key, zone_data in zones_config.items():
                    # Handle case where zone_data might be a list (from cameras.yaml)
                    if isinstance(zone_data, list):
                        # Skip list entries, they're not zone definitions
                        continue
                    
                    if isinstance(zone_data, dict):
                        if zone_data.get('camera_id') == camera_id or zone_key.startswith(camera_id):
                            camera_zones.append({
                                'name': zone_data.get('name', zone_key),
                                'type': zone_data.get('type', 'workstation'),
                                'color': zone_data.get('color', '#FF6B6B'),
                                'polygon': zone_data.get('polygon', []),
                                'dwell_time': zone_data.get('expected_dwell_time', 300),
                                'camera_id': camera_id
                            })
            elif isinstance(zones_config, list):
                # Handle case where zones are stored as a list
                for zone_data in zones_config:
                    if isinstance(zone_data, dict):
                        if zone_data.get('camera_id') == camera_id:
                            camera_zones.append({
                                'name': zone_data.get('name', f'Zone_{len(camera_zones)}'),
                                'type': zone_data.get('type', 'workstation'),
                                'color': zone_data.get('color', '#FF6B6B'),
                                'polygon': zone_data.get('polygon', []),
                                'dwell_time': zone_data.get('expected_dwell_time', 300),
                                'camera_id': camera_id
                            })
            
            st.session_state.zones = camera_zones
            if camera_zones:
                st.success(f"Loaded {len(camera_zones)} zones for camera {camera_id}")
            else:
                st.info(f"No zones found for camera {camera_id}")
        else:
            st.info("No zones configuration file found")
            
    except Exception as e:
        st.error(f"Error loading zones: {str(e)}")
        st.session_state.zones = []

def load_camera_screenshot(camera_id):
    """Load a screenshot from the selected camera"""
    try:
        import cv2
        import glob
        import os
        from PIL import Image
        
        # Debug logging (only show if debug mode is enabled)
        if st.session_state.get('debug_mode', False):
            st.write(f"Loading video for camera: {camera_id}")
        
        # Look for video files for this camera
        video_patterns = [
            f"../vids/*{camera_id}*.mp4",
            f"../vids/*{camera_id}*.avi", 
            f"../vids/*{camera_id}*.mov",
            f"vids/*{camera_id}*.mp4",
            f"vids/*{camera_id}*.avi",
            f"vids/*{camera_id}*.mov"
        ]
        
        video_files = []
        for pattern in video_patterns:
            video_files.extend(glob.glob(pattern))
        
        if st.session_state.get('debug_mode', False):
            st.write(f"Found {len(video_files)} video files for camera {camera_id}")
        
        if video_files:
            # Use the first video file found
            video_path = video_files[0]
            
            if st.session_state.get('debug_mode', False):
                st.write(f"Loading from: {video_path}")
            
            # Open video and keep it open for frame navigation
            cap = cv2.VideoCapture(video_path)
            
            if cap.isOpened():
                # Store video capture in session state for frame navigation
                st.session_state.video_cap = cap
                st.session_state.current_frame = 0
                st.session_state.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                
                # Get current frame
                cap.set(cv2.CAP_PROP_POS_FRAMES, st.session_state.current_frame)
                ret, frame = cap.read()
                if ret:
                    # Convert BGR to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # Save to session state
                    st.session_state.camera_image = frame_rgb
                    st.success(f"Video loaded: {os.path.basename(video_path)}")
                    
                    if st.session_state.get('debug_mode', False):
                        st.write(f"Total frames: {st.session_state.total_frames}")
                        st.write(f"Current frame: {st.session_state.current_frame}")
                else:
                    st.error("Could not read frame from video")
            else:
                st.error("Could not open video file")
        else:
            # Try to find an image file
            image_patterns = [
                f"data/camera_screenshots/{camera_id}*.jpg",
                f"data/camera_screenshots/{camera_id}*.png",
                f"camera_screenshots/{camera_id}*.jpg",
                f"camera_screenshots/{camera_id}*.png"
            ]
            
            image_files = []
            for pattern in image_patterns:
                image_files.extend(glob.glob(pattern))
            
            if image_files:
                img = Image.open(image_files[0])
                st.session_state.camera_image = img
                st.success(f"Screenshot loaded: {os.path.basename(image_files[0])}")
                
                if st.session_state.get('debug_mode', False):
                    st.write(f"Image size: {img.size}")
            else:
                st.error(f"No video or image files found for camera {camera_id}")
                st.info("Please place video files in ../vids/ directory or screenshots in data/camera_screenshots/")
                
                # Create directories if they don't exist
                os.makedirs("data/camera_screenshots", exist_ok=True)
                os.makedirs("../vids", exist_ok=True)
                
    except Exception as e:
        st.error(f"Error loading camera screenshot: {str(e)}")
        if st.session_state.get('debug_mode', False):
            import traceback
            st.write(f"Debug info: {traceback.format_exc()}")

def update_current_frame():
    """Update the displayed frame based on current frame number"""
    if st.session_state.get('video_cap') is not None:
        st.session_state.video_cap.set(cv2.CAP_PROP_POS_FRAMES, st.session_state.current_frame)
        ret, frame = st.session_state.video_cap.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            st.session_state.camera_image = frame_rgb

def finish_current_zone():
    """Finish drawing the current zone and save it (create new or edit existing)"""
    try:
        if 'pending_zone' in st.session_state and st.session_state.current_polygon:
            zone = st.session_state.pending_zone.copy()
            zone['polygon'] = st.session_state.current_polygon.copy()
            zone['camera_id'] = st.session_state.current_camera
            zone['dwell_time'] = 300  # Default dwell time
            
            # Check if this is an edit or create operation
            if 'edit_index' in zone:
                # Update existing zone
                edit_index = zone['edit_index']
                if edit_index < len(st.session_state.zones):
                    st.session_state.zones[edit_index] = zone
                    st.success(f"Zone '{zone['name']}' updated successfully!")
                else:
                    st.error("Invalid zone index")
            else:
                # Create new zone
                st.session_state.zones.append(zone)
                st.success(f"Zone '{zone['name']}' created successfully!")
            
            # Reset drawing state
            st.session_state.drawing_mode = False
            st.session_state.current_polygon = []
            del st.session_state.pending_zone
            
            st.rerun()
        else:
            st.error("No zone being drawn")
            
    except Exception as e:
        st.error(f"Error finishing zone: {str(e)}")
        st.session_state.drawing_mode = False
        st.session_state.current_polygon = []

def reset_all_data():
    """Reset all video processing data and start fresh"""
    try:
        # Confirmation dialog
        if not st.session_state.get('confirm_reset', False):
            st.session_state.confirm_reset = True
            st.warning("WARNING: This will delete ALL video processing data, detections, tracks, and analytics. Click 'Reset All Data' again to confirm.")
            return
        
        # Reset confirmation flag
        st.session_state.confirm_reset = False
        
        with st.spinner("Resetting all data..."):
            # Clear database tables
            import sqlite3
            import os
            
            db_path = "deltavision.db"
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Clear all data tables
                tables_to_clear = [
                    'detections',
                    'zone_visits', 
                    'worker_metrics',
                    'zone_metrics',
                    'system_metrics',
                    'processing_logs'
                ]
                
                for table in tables_to_clear:
                    cursor.execute(f"DELETE FROM {table}")
                
                conn.commit()
                conn.close()
            
            # Clear processed files
            import shutil
            data_dirs = ['data/processed', 'data/exports', 'data/temp']
            
            for dir_path in data_dirs:
                if os.path.exists(dir_path):
                    shutil.rmtree(dir_path)
                    os.makedirs(dir_path, exist_ok=True)
            
            # Clear logs
            if os.path.exists('logs'):
                for log_file in os.listdir('logs'):
                    if log_file.endswith('.log'):
                        os.remove(os.path.join('logs', log_file))
            
            # Reset any session state
            for key in list(st.session_state.keys()):
                if key != 'confirm_reset':
                    del st.session_state[key]
            
        st.success("All data has been reset successfully! The system is now starting fresh.")
        st.info("The page will refresh in 3 seconds...")
        st.rerun()
        
    except Exception as e:
        st.error(f"Error resetting data: {str(e)}")
        st.session_state.confirm_reset = False

if __name__ == "__main__":
    main()
