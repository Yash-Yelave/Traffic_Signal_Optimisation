import cv2
import socket
import time
import numpy as np
from ultralytics import YOLO
import subprocess
import sys
import json
import ast

# ---------------- CONFIG ----------------
MODEL_NAME = "yolo11m.pt"
VEHICLE_CLASSES = {2, 3, 5, 7}  # car, motorcycle, bus, truck
AMB_ID = 16
CONF_THRESH = 0.35
VIDEO_SOURCES = [
    "videos/lane1.mp4",
    "videos/lane2.mp4",
    "videos/lane3.mp4",
    "videos/lane4.mp4"
]
SEND_ADDR = ("127.0.0.1", 5005)
RECV_ADDR = ("127.0.0.1", 5006)
DETECT_EVERY_N_FRAMES = 5

# ---------------- SETUP ----------------
model = YOLO(MODEL_NAME)
caps = [cv2.VideoCapture(p) for p in VIDEO_SOURCES]
for i, cap in enumerate(caps):
    if not cap.isOpened():
        print(f"Error: Cannot open {VIDEO_SOURCES[i]}")
        sys.exit(1)

send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
recv_sock.bind(RECV_ADDR)
recv_sock.setblocking(False)

last_known_counts = [0] * len(caps)
last_known_amb = [0] * len(caps)
frame_counters = [0] * len(caps)
current_decision = {"lane": None, "green_time": 0, "expires_at": 0}

# Launch DQN
print("INFO: Launching DQN agent...")
dqn_process = subprocess.Popen([sys.executable, "dqn.py"])
time.sleep(3)
print("INFO: Detection started.")

try:
    while True:
        annotated_frames = []

        for i, cap in enumerate(caps):
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
                if not ret:
                    h, w = (480, 640)
                    annotated_frames.append(np.zeros((h, w, 3), dtype=np.uint8))
                    continue

            if frame_counters[i] % DETECT_EVERY_N_FRAMES == 0:
                results = model(frame, verbose=False)[0]
                count = 0
                amb = 0
                for box in results.boxes:
                    conf = float(box.conf)
                    if conf < CONF_THRESH:
                        continue
                    cls = int(box.cls.item())
                    if cls in VEHICLE_CLASSES:
                        count += 1
                    if cls == AMB_ID:
                        amb = 1

                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    color = (0, 255, 0) if cls in VEHICLE_CLASSES else (255, 100, 100)
                    label = f"{results.names[cls]}: {conf:.2f}"
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(frame, label, (x1, max(15, y1 - 5)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                last_known_counts[i] = count
                last_known_amb[i] = amb

            frame_counters[i] += 1
            annotated_frames.append(frame)

        # --- SEND detections to DQN ---
        payload = json.dumps({"counts": last_known_counts, "amb": last_known_amb})
        send_sock.sendto(payload.encode("utf-8"), SEND_ADDR)

        # --- RECEIVE decision as list [lane, green_time] ---
        try:
            data, _ = recv_sock.recvfrom(1024)
            decision_list = ast.literal_eval(data.decode("utf-8"))
            lane = int(decision_list[0])
            green_time = float(decision_list[1])
            current_decision.update({
                "lane": lane,
                "green_time": green_time,
                "expires_at": time.time() + green_time
            })
        except BlockingIOError:
            pass
        except Exception as e:
            print(f"Warning: Could not parse decision: {e}")

        # --- DISPLAY ---
        now = time.time()
        for i, frame in enumerate(annotated_frames):
            txt = f"Lane {i+1} | Vehicles: {last_known_counts[i]} | Ambulance: {'Yes' if last_known_amb[i] else 'No'}"
            cv2.putText(frame, txt, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

            if current_decision["lane"] == i and current_decision["expires_at"] > now:
                remaining = max(0, int(current_decision["expires_at"] - now))
                green_text = f"GREEN: {current_decision['green_time']}s ({remaining}s)"
                cv2.putText(frame, green_text, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
                h, w, _ = frame.shape
                cv2.rectangle(frame, (2, 2), (w - 2, h - 2), (0, 255, 0), 5)

            cv2.imshow(f"Lane-{i+1}", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

except KeyboardInterrupt:
    print("\nINFO: Interrupted by user.")

finally:
    print("INFO: Shutting down...")
    if 'dqn_process' in locals() and dqn_process.poll() is None:
        print("INFO: Terminating DQN agent process...")
        dqn_process.terminate()
        dqn_process.wait()
    for cap in caps:
        cap.release()
    cv2.destroyAllWindows()
    send_sock.close()
    recv_sock.close()
    print("INFO: Detection stopped.")
