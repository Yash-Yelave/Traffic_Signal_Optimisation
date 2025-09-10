from ultralytics import YOLO
import cv2

# Load YOLO model once
model = YOLO("models/yolov11n.pt")

def run_detection(frame):
    results = model(frame, verbose=False)  
    annotated = results[0].plot()  # draw bounding boxes
    return annotated
