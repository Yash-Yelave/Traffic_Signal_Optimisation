# modules/camera_manager.py
import threading
import time
import cv2
from collections import deque
from config import RTSP_TEMPLATE, DVR_IP, DVR_USER, DVR_PASS, NUM_LANES, CAP_PROP_BUFFERSIZE, USE_FFMPEG

class CameraWorker(threading.Thread):
    def __init__(self, lane_id, rtsp_url, max_queue=1):
        super().__init__(daemon=True)
        self.lane_id = lane_id
        self.rtsp_url = rtsp_url
        self.frame = None
        self.lock = threading.Lock()
        self.running = True
        self.max_queue = max_queue
        self._init_capture()

    def _init_capture(self):
        print(f"[CameraWorker] Connecting to {self.rtsp_url}")
        if USE_FFMPEG:
            cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
        else:
            cap = cv2.VideoCapture(self.rtsp_url)
        
        # add connection timeout safeguard
        start_time = time.time()
        while not cap.isOpened() and time.time() - start_time < 10:
            time.sleep(0.5)
        
        if not cap.isOpened():
            print(f"[CameraWorker] ⚠️ Could not connect to {self.rtsp_url} (timeout). Retrying later.")
            self.cap = None
            return
        
        print(f"[CameraWorker] ✅ Connected to {self.rtsp_url}")
        try:
            cap.set(cv2.CAP_PROP_BUFFERSIZE, CAP_PROP_BUFFERSIZE)
        except Exception:
            pass
        self.cap = cap

    def run(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                # attempt reconnect
                time.sleep(0.5)
                if self.cap:
                    self.cap.release()
                try:
                    self._init_capture()
                except Exception:
                    time.sleep(1)
                continue
            with self.lock:
                self.frame = frame

    def get_frame(self):
        with self.lock:
            return None if self.frame is None else self.frame.copy()

    def stop(self):
        self.running = False
        try:
            self.cap.release()
        except Exception:
            pass

class CameraManager:
    def __init__(self, num_lanes=NUM_LANES, rtsp_template=RTSP_TEMPLATE):
        self.workers = {}
        for ch in range(1, num_lanes+1):
            rtsp = rtsp_template.format(user=DVR_USER, pwd=DVR_PASS, ip=DVR_IP, ch=ch)
            w = CameraWorker(ch, rtsp)
            self.workers[ch] = w
            w.start()

    def get_frame(self, lane_id):
        w = self.workers.get(int(lane_id))
        if not w:
            return None
        return w.get_frame()

    def stop_all(self):
        for w in self.workers.values():
            w.stop()