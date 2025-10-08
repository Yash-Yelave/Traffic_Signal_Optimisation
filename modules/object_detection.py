import cv2

def run_detection():
    cap = cv2.VideoCapture("videos/sample.mp4")  # path to your sample video

    while True:
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # loop video
            continue

        _, jpeg = cv2.imencode('.jpg', frame)
        yield jpeg.tobytes()
