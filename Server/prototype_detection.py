import cv2
from ultralytics import YOLO
import torch

# --- CONFIGURATION ---
# Use the lightweight and fast 'nano' model. It's excellent for this task.
# The model will be downloaded automatically on the first run.
MODEL_NAME = 'yolo11m.pt'

# Set the index of your camera. 0 is usually the default built-in webcam.
# If you have multiple cameras, you might need to try 1, 2, etc.
CAMERA_INDEX = 0 
# To use your ESP32-CAM instead, comment out the line above and uncomment the one below:
# CAMERA_INDEX = 'http://192.168.1.10/stream' # <-- Replace with your ESP32-CAM's stream URL

# Confidence threshold: only show detections with a confidence > 50%
CONFIDENCE_THRESHOLD = 0.5

# The class ID for "car" in the COCO dataset, which YOLO was trained on.
CAR_CLASS_ID = 2

# --- INITIALIZATION ---
# Check for GPU and print the device being used
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# Load the YOLO model
model = YOLO(MODEL_NAME)

# Open the camera feed
cap = cv2.VideoCapture(CAMERA_INDEX)
if not cap.isOpened():
    print(f"Error: Could not open camera at index {CAMERA_INDEX}")
    exit()

# Create a resizable window for the display
window_name = "Toy Car Detection Prototype"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

# --- MAIN DETECTION LOOP ---
while True:
    # Read a frame from the camera
    success, frame = cap.read()
    if not success:
        print("Failed to grab frame. Exiting...")
        break

    # Run YOLO inference on the frame
    results = model(frame, stream=True, verbose=False) # Set verbose=False to hide console output

    # Process the results
    for result in results:
        # Loop through each detected object
        for box in result.boxes:
            # Check if the detected object is a 'car' and has high confidence
            if int(box.cls) == CAR_CLASS_ID and box.conf > CONFIDENCE_THRESHOLD:
                
                # Get the bounding box coordinates
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                
                # Get the confidence score
                confidence = box.conf.item()
                
                # --- VISUALIZATION ---
                # Draw the bounding box on the frame (in green)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # Create the label text
                label = f"Car {confidence:.2f}"
                
                # Put the label above the bounding box
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # Display the final frame
    cv2.imshow(window_name, frame)

    # Break the loop if the 'q' key is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# --- CLEANUP ---
# Release the camera and destroy all windows
cap.release()
cv2.destroyAllWindows()
print("Script finished.") 