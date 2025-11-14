"""
detection.py
- Contains the VehicleDetector class for processing video frames.
- Refactored from a standalone script to an importable module for Flask.
"""

import cv2
import numpy as np
from ultralytics import YOLO
import torch

class VehicleDetector:
    """
    A class to handle vehicle detection using a YOLO model.
    It's designed to be initialized once and then process frames on demand.
    """
    def __init__(self, model_path='yolov8n.pt'):
        """
        Initializes the VehicleDetector.

        Args:
            model_path (str): The path to the YOLO model file.
        """
        # Determine the device to run the model on (CUDA if available, otherwise CPU)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[Detection] Using device: {self.device}")

        # Load the YOLO model
        try:
            self.model = YOLO(model_path)
            # Move the model to the selected device
            self.model.to(self.device)
            print(f"[Detection] YOLO model '{model_path}' loaded successfully.")
        except Exception as e:
            print(f"[Detection] FATAL ERROR: Could not load YOLO model from '{model_path}'. The application cannot continue.")
            print(f"[Detection] Error details: {e}")
            self.model = None

        # Define the classes to be considered as vehicles.
        # Common YOLO class IDs: 2=car, 3=motorcycle, 5=bus, 7=truck
        self.vehicle_class_ids = [2, 3, 5, 7]
        # --- DEBUGGING: Lower the threshold to catch weak detections ---
        # A low value like 0.1 makes it much more likely to see boxes.
        # We can tune this back up once we confirm it's working.
        self.confidence_threshold = 0.3 # Tuned up slightly from 0.1

    def detect_vehicles(self, frame_bytes):
        """
        Detects vehicles in a single image frame, annotates the frame,
        and returns the vehicle count and the annotated frame.
        """
        # --- ROBUST ERROR HANDLING & VISUAL DEBUGGING ---
        def create_error_frame(message, original_bytes):
            """Helper function to create a frame with an error message."""
            try:
                # Try to decode the original frame to draw on top of it
                nparr = np.frombuffer(original_bytes, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if frame is None: raise ValueError("Cannot decode")
            except:
                # If decoding fails, create a black frame
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
            
            cv2.putText(frame, message, (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
            ret, buffer = cv2.imencode('.jpg', frame)
            return 0, buffer.tobytes() if ret else original_bytes

        if not self.model or frame_bytes is None:
            return create_error_frame("ERROR: YOLO Model Not Loaded", frame_bytes or b'')

        try:
            nparr = np.frombuffer(frame_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None:
                return create_error_frame("ERROR: Invalid Frame Data", frame_bytes)
        except Exception as e:
            return create_error_frame(f"ERROR: Decoding Failed", frame_bytes)

        # --- FPS OPTIMIZATION: Resize the frame before detection ---
        # Processing a smaller image is significantly faster.
        resized_frame = cv2.resize(frame, (640, 480))

        # Perform detection on the decoded frame
        # --- FPS OPTIMIZATION: Use the resized frame for detection ---
        results = self.model(resized_frame, stream=False, verbose=False, device=self.device)
        result = results[0]

        vehicle_count = 0
        for box in result.boxes:
            # Check confidence against our new, lower threshold
            if box.conf > self.confidence_threshold:
                
                # Restore the class filter to count only vehicles
                class_id = int(box.cls[0])
                if class_id in self.vehicle_class_ids:
                    vehicle_count += 1
                    
                    # --- FIX: Scale bounding box coordinates back to the original frame size ---
                    # The box coordinates are for the resized_frame, so we must scale them
                    # up to draw them correctly on the original, larger 'frame'.
                    orig_h, orig_w = frame.shape[:2]
                    resized_h, resized_w = resized_frame.shape[:2]
                    x1, y1, x2, y2 = box.xyxy[0]
                    x1 = int(x1 * orig_w / resized_w)
                    y1 = int(y1 * orig_h / resized_h)
                    x2 = int(x2 * orig_w / resized_w)
                    y2 = int(y2 * orig_h / resized_h)
                    
                    # Draw the box and label for the detected vehicle
                    label = f"{result.names[class_id]} {box.conf.item():.2f}"
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        try:
            ret, annotated_frame_bytes = cv2.imencode('.jpg', frame)
            if not ret:
                return vehicle_count, frame_bytes
            return vehicle_count, annotated_frame_bytes.tobytes()
        except Exception as e:
            print(f"[Detection] Error encoding frame: {e}")
            return vehicle_count, frame_bytes