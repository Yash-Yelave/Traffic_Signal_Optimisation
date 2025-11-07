import cv2

# Use the same RTSP URL format from your config
url = "rtsp://admin:12345@192.168.1.10:554/cam/realmonitor?channel=1&subtype=0"

print(f"Attempting to connect to: {url}")
cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)

if cap.isOpened():
    print("✅ Connected to camera stream.")
    ret, frame = cap.read()
    if ret:
        print("✅ Successfully read a frame from the stream.")
        cv2.imwrite("test_frame.jpg", frame)
        print("✅ Frame saved as test_frame.jpg")
    else:
        print("❌ Connection opened, but failed to read a frame.")
else:
    print("❌ Could not connect to the camera stream. Check network, DVR settings, and URL.")