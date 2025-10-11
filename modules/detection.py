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
    def __init__(self, model_path='modules/yolo11m.pt'):
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
            print(f"[Detection] Error loading YOLO model: {e}")
            # If the model fails to load, create a dummy model that does nothing
            self.model = None

        # Define the classes to be considered as vehicles.
        # Common YOLO class IDs: 2=car, 3=motorcycle, 5=bus, 7=truck
        self.vehicle_class_ids = [2, 3, 5, 7]
        self.confidence_threshold = 0.5

    def detect_vehicles(self, frame_bytes):
        """
        Detects vehicles in a single image frame provided as bytes.

        Args:
            frame_bytes (bytes): The raw JPEG bytes of the image frame.

        Returns:
            tuple: A tuple containing:
                - int: The number of detected vehicles.
                - bytes: The annotated frame with bounding boxes drawn on it (as JPEG bytes).
        """
        if not self.model or frame_bytes is None:
            return 0, frame_bytes # Return 0 count and the original frame if model isn't loaded

        try:
            # 1. Decode the JPEG byte stream into a NumPy array (OpenCV format)
            nparr = np.frombuffer(frame_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None:
                print("[Detection] Failed to decode frame.")
                return 0, frame_bytes
        except Exception as e:
            print(f"[Detection] Error decoding frame: {e}")
            return 0, frame_bytes

        vehicle_count = 0

        # 2. Run the YOLO model on the frame
        # The model expects a list of frames, so we pass [frame]
        results = self.model(frame, stream=False, verbose=False, device=self.device)
        
        # The result object contains detection information
        result = results[0] # We only process the first (and only) result

        # 3. Iterate through detected boxes
        for box in result.boxes:
            # Check if the detection confidence is above our threshold
            if box.conf > self.confidence_threshold:
                # Check if the detected class is in our list of vehicle classes
                class_id = int(box.cls[0])
                if class_id in self.vehicle_class_ids:
                    vehicle_count += 1
                    
                    # Get bounding box coordinates
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    
                    # Draw a green rectangle around the detected vehicle
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # 4. Encode the annotated frame back to JPEG bytes to be streamed
        try:
            ret, annotated_frame_bytes = cv2.imencode('.jpg', frame)
            if not ret:
                print("[Detection] Failed to encode annotated frame.")
                return vehicle_count, frame_bytes # Return original bytes on failure
            return vehicle_count, annotated_frame_bytes.tobytes()
        except Exception as e:
            print(f"[Detection] Error encoding frame: {e}")
            return vehicle_count, frame_bytes