import cv2
import numpy as np
from typing import Tuple, Optional, List
import logging

logger = logging.getLogger(__name__)

class VideoUtils:
    """Utility functions for video processing"""
    
    @staticmethod
    def get_video_info(video_path: str) -> dict:
        """Get video file information"""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        info = {
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'duration': cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)
        }
        
        cap.release()
        return info
    
    @staticmethod
    def resize_frame(frame: np.ndarray, target_size: Tuple[int, int], 
                   maintain_aspect_ratio: bool = True) -> np.ndarray:
        """Resize frame while optionally maintaining aspect ratio"""
        if maintain_aspect_ratio:
            h, w = frame.shape[:2]
            target_w, target_h = target_size
            
            # Calculate scaling factor
            scale = min(target_w / w, target_h / h)
            new_w, new_h = int(w * scale), int(h * scale)
            
            # Resize frame
            resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
            
            # Create black background and center the resized frame
            background = np.zeros((target_h, target_w, 3), dtype=np.uint8)
            y_offset = (target_h - new_h) // 2
            x_offset = (target_w - new_w) // 2
            background[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized
            
            return background
        else:
            return cv2.resize(frame, target_size, interpolation=cv2.INTER_LINEAR)
    
    @staticmethod
    def enhance_frame(frame: np.ndarray, brightness: float = 1.0, 
                    contrast: float = 1.0, saturation: float = 1.0) -> np.ndarray:
        """Enhance frame with brightness, contrast, and saturation adjustments"""
        # Convert to float for calculations
        enhanced = frame.astype(np.float32) / 255.0
        
        # Apply brightness and contrast
        enhanced = enhanced * contrast + brightness - 0.5
        
        # Apply saturation
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_BGR2HSV)
        enhanced[:, :, 1] *= saturation
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_HSV2BGR)
        
        # Clip values and convert back to uint8
        enhanced = np.clip(enhanced * 255, 0, 255).astype(np.uint8)
        
        return enhanced
    
    @staticmethod
    def apply_gaussian_blur(frame: np.ndarray, kernel_size: int = 5) -> np.ndarray:
        """Apply Gaussian blur to reduce noise"""
        return cv2.GaussianBlur(frame, (kernel_size, kernel_size), 0)
    
    @staticmethod
    def apply_morphological_operations(frame: np.ndarray, operation: str = 'open', 
                                   kernel_size: int = 5) -> np.ndarray:
        """Apply morphological operations"""
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
        
        if operation == 'open':
            return cv2.morphologyEx(frame, cv2.MORPH_OPEN, kernel)
        elif operation == 'close':
            return cv2.morphologyEx(frame, cv2.MORPH_CLOSE, kernel)
        elif operation == 'erode':
            return cv2.erode(frame, kernel)
        elif operation == 'dilate':
            return cv2.dilate(frame, kernel)
        else:
            return frame
    
    @staticmethod
    def calculate_optical_flow(prev_frame: np.ndarray, curr_frame: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate optical flow between two frames"""
        # Convert to grayscale
        prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)
        
        # Calculate optical flow using Farneback algorithm
        flow = cv2.calcOpticalFlowPyrLK(
            prev_gray, curr_gray, 
            None,  # Previous points
            **dict(
                winSize=(15, 15),
                maxLevel=2,
                criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)
            )
        )
        
        return flow
    
    @staticmethod
    def stabilize_frame(frame: np.ndarray, reference_frame: np.ndarray) -> np.ndarray:
        """Stabilize frame using reference frame"""
        # Convert to grayscale
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_ref = cv2.cvtColor(reference_frame, cv2.COLOR_BGR2GRAY)
        
        # Find features in reference frame
        orb = cv2.ORB_create()
        kp1, des1 = orb.detectAndCompute(gray_ref, None)
        kp2, des2 = orb.detectAndCompute(gray_frame, None)
        
        if des1 is None or des2 is None:
            return frame
        
        # Match features
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(des1, des2)
        matches = sorted(matches, key=lambda x: x.distance)
        
        if len(matches) < 10:
            return frame
        
        # Extract matched keypoints
        src_pts = np.float32([kp1[m.queryIdx].pt for m in matches[:50]]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in matches[:50]]).reshape(-1, 1, 2)
        
        # Calculate homography
        M, mask = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, 5.0)
        
        if M is not None:
            # Apply homography to stabilize frame
            h, w = frame.shape[:2]
            stabilized = cv2.warpPerspective(frame, M, (w, h))
            return stabilized
        
        return frame
    
    @staticmethod
    def detect_scene_changes(frames: List[np.ndarray], threshold: float = 0.3) -> List[int]:
        """Detect scene changes in video frames"""
        scene_changes = [0]  # First frame is always a scene start
        
        if len(frames) < 2:
            return scene_changes
        
        prev_hist = cv2.calcHist([frames[0]], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        
        for i in range(1, len(frames)):
            curr_hist = cv2.calcHist([frames[i]], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
            
            # Calculate histogram correlation
            correlation = cv2.compareHist(prev_hist, curr_hist, cv2.HISTCMP_CORREL)
            
            if correlation < threshold:
                scene_changes.append(i)
            
            prev_hist = curr_hist
        
        return scene_changes
    
    @staticmethod
    def create_video_writer(output_path: str, fps: float, frame_size: Tuple[int, int]) -> cv2.VideoWriter:
        """Create video writer for output"""
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        return cv2.VideoWriter(output_path, fourcc, fps, frame_size)
    
    @staticmethod
    def extract_frames_at_times(video_path: str, timestamps: List[float]) -> List[np.ndarray]:
        """Extract frames at specific timestamps"""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frames = []
        
        try:
            for timestamp in timestamps:
                frame_number = int(timestamp * fps)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                ret, frame = cap.read()
                if ret:
                    frames.append(frame)
                else:
                    logger.warning(f"Could not extract frame at timestamp {timestamp}")
        finally:
            cap.release()
        
        return frames
    
    @staticmethod
    def blend_frames(frame1: np.ndarray, frame2: np.ndarray, alpha: float = 0.5) -> np.ndarray:
        """Blend two frames with specified alpha"""
        return cv2.addWeighted(frame1, alpha, frame2, 1 - alpha, 0)
    
    @staticmethod
    def draw_text_with_background(frame: np.ndarray, text: str, position: Tuple[int, int],
                               font_scale: float = 1.0, color: Tuple[int, int, int] = (255, 255, 255),
                               bg_color: Tuple[int, int, int] = (0, 0, 0), thickness: int = 2) -> np.ndarray:
        """Draw text with background for better visibility"""
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Get text size
        (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
        
        # Draw background rectangle
        x, y = position
        cv2.rectangle(frame, 
                     (x, y - text_height - baseline),
                     (x + text_width, y + baseline),
                     bg_color, -1)
        
        # Draw text
        cv2.putText(frame, text, position, font, font_scale, color, thickness)
        
        return frame
