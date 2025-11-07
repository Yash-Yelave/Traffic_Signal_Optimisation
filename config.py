# config.py
# DVR / Camera configuration
DVR_IP = "192.168.1.10"             # <-- set to your DVR IP
DVR_USER = "admin"
DVR_PASS = "12345"
NUM_LANES = 4

# RTSP template (Dahua/CP Plus / DVR typical)
RTSP_TEMPLATE = "rtsp://{user}:{pwd}@{ip}:554/cam/realmonitor?channel={ch}&subtype=0"

# Capture tuning
CAP_PROP_BUFFERSIZE = 1             # smallest buffer for low-latency
RTSP_TRANSPORT = "tcp"              # tcp is more reliable for LAN
USE_FFMPEG = True                   # True => prefer ffmpeg backend on OpenCV

# Detection model (Ultralytics YOLOv8 - change if needed)
YOLO_MODEL = "yolov8n.pt"           # lightweight; change to yolov8s/m/l as needed

# Database / persistence
DATABASE = "traffic.db"

# Flask network
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000