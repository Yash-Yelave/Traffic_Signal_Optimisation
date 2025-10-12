from flask import Flask, render_template, jsonify, Response, request
import cv2
import json
import random
import time
import threading
from datetime import datetime
import requests 

# --- AI DETECTION INTEGRATION ---
from modules.detection import VehicleDetector
# --- END AI DETECTION INTEGRATION ---

from static.modules.traffic_signal_backend import map_lane_data_to_signal_format, set_active_green_lane, SIGNAL_STATE

app = Flask(__name__)

# --- AI DETECTION INTEGRATION ---
# Initialize the YOLO vehicle detector once when the application starts.
vehicle_detector = VehicleDetector()
# Global variable to store live counts for all lanes.
# Initialized with zeros.
REALTIME_DATA = {"vehicle_counts": {1: 0, 2: 0, 3: 0, 4: 0}}
# --- END AI DETECTION INTEGRATION ---

# ESP32-CAM IP address
ESP32_IP = "192.168.72.86" # Restored from README, please verify this is correct
# Combined stream URL constant for requests
ESP32_STREAM_URL = f'http://{ESP32_IP}:81/stream'

# --- VIDEO FILE INTEGRATION ---
# Define paths to the pre-recorded video files for other lanes.
# Please ensure these files exist at the specified paths.
VIDEO_FILES = {
    2: 'modules/videos/lane2.mp4',
    3: 'modules/videos/lane3.mp4',
    4: 'modules/videos/lane4.mp4',
}
# --- END VIDEO FILE INTEGRATION ---

# Flash control route for ESP32
@app.route('/flash/<action>')
def control_flash(action):
    """Control the ESP32-CAM flash LED"""
    try:
        control_url = f"http://{ESP32_IP}/control"
        if action == 'on':
            # FIX: Reduced intensity from 255 to 64. Max intensity often causes the camera to brown-out and freeze.
            response = requests.get(f'{control_url}?var=led_intensity&val=64', timeout=5)
        elif action == 'off':
            response = requests.get(f'{control_url}?var=led_intensity&val=0', timeout=5)
        else:
            return jsonify({'status': 'error', 'message': 'Invalid action'}), 400
        
        if response.status_code == 200:
            return jsonify({'status': 'success', 'message': f'Flash turned {action}'})
        else:
            return jsonify({'status': 'error', 'message': 'ESP32 responded with error'}), 500
            
    except requests.exceptions.RequestException as e:
        return jsonify({'status': 'error', 'message': f'Connection error: {str(e)}'}), 500

# ============================================================================
# UNIFIED DATA SOURCE - Single source of truth for all traffic data
# ============================================================================
def get_unified_traffic_data():
    """
    Single source of truth for all traffic data.
    This function generates the core lane data that is used by both
    dashboard and lane feeds endpoints.
    """
    # Generate base lane data
    lanes = [
        {
            'id': 1,
            'name': 'Lane 1',
            'status': 'ACTIVE',
            'direction': 'North',
            # --- AI DETECTION INTEGRATION ---
            # Use the real-time vehicle count from the YOLO detector for each lane.
            'vehicles': REALTIME_DATA["vehicle_counts"].get(1, 0),
            # --- END AI DETECTION INTEGRATION ---
            'speed': random.randint(40, 50),
            'traffic': random.randint(70, 85),
            'alert': 'Heavy congestion detected'
        },
        {
            'id': 2,
            'name': 'Lane 2',
            'status': 'ACTIVE',
            'direction': 'South',
            'vehicles': REALTIME_DATA["vehicle_counts"].get(2, 0),
            'speed': random.randint(55, 70),
            'traffic': random.randint(30, 45),
            'alert': None
        },
        {
            'id': 3,
            'name': 'Lane 3',
            'status': 'ACTIVE',
            'direction': 'East',
            'vehicles': REALTIME_DATA["vehicle_counts"].get(3, 0),
            'speed': random.randint(25, 40),
            'traffic': random.randint(50, 65),
            'alert': 'Accident detected'
        },
        {
            'id': 4,
            'name': 'Lane 4',
            'status': 'ACTIVE',
            'direction': 'West',
            'vehicles': REALTIME_DATA["vehicle_counts"].get(4, 0),
            'speed': random.randint(45, 60),
            'traffic': random.randint(40, 60),
            'alert': None
        }
    ]
    
    return lanes


def get_lane_feeds_data():
    """
    Backward compatible wrapper for lane feeds endpoint.
    Returns data in the exact format expected by existing frontend code.
    """
    return get_unified_traffic_data()


def get_dashboard_data():
    """
    Backward compatible wrapper for dashboard endpoint.
    Transforms unified data into dashboard-specific format.
    """
    # Get the single source of truth
    lanes = get_unified_traffic_data()

    # Calculate aggregated metrics from actual lane data
    total_vehicles = sum(lane.get('vehicles', 0) for lane in lanes)
    
    # Calculate a more realistic average congestion based on total vehicle count.
    # Let's assume a max capacity for the intersection (e.g., 100 vehicles).
    MAX_INTERSECTION_CAPACITY = 100 
    avg_congestion = min(100, int((total_vehicles / MAX_INTERSECTION_CAPACITY) * 100))

    # Collect recent alerts from lanes
    recent_alerts = []
    for lane in lanes:
        if lane['alert']:
            alert_type = 'ACCIDENT' if 'accident' in lane['alert'].lower() else 'HIGH CONGESTION'
            recent_alerts.append({
                'type': alert_type,
                'message': f"{lane['alert']} on {lane['name']}",
                'time': '2 min ago'
            })
    
    return {
        'lanes': lanes, # Add full lane data to the main dashboard endpoint
        'simulation_lanes': map_lane_data_to_signal_format(lanes), # Add pre-formatted data for the simulation
        'signal_state': SIGNAL_STATE, # Expose the full signal state for the countdown UI
        'total_vehicles': total_vehicles,
        'avg_congestion': avg_congestion,
        'traffic_signals': {
            'north_south': {
                'red': random.randint(0, 100),
                'yellow': random.randint(0, 50),
                'green': random.randint(100, 300)
            },
            'east_west': {
                'red': random.randint(200, 400),
                'yellow': random.randint(0, 50),
                'green': random.randint(0, 100)
            },
            'main_st': {
                'red': random.randint(0, 50),
                'yellow': random.randint(50, 100),
                'green': random.randint(0, 50)
            },
            'park_ave': {
                'red': random.randint(0, 100),
                'yellow': random.randint(0, 50),
                'green': random.randint(200, 400)
            }
        }, 
        'recent_alerts': recent_alerts
    }


# ============================================================================
# ROUTES
# ============================================================================

#traffic signal routes with these:
@app.route('/api/lanes')
def get_lanes():
    """API endpoint to get current lane data - uses real data from lane feeds"""
    # Get your existing lane feeds data
    lane_feeds = get_lane_feeds_data()
    
    # Convert to traffic signal format
    signal_data = map_lane_data_to_signal_format(lane_feeds)
    
    return jsonify({ # This endpoint is now the single source for the simulation
        'lanes': signal_data
    })

@app.route('/api/update_signal')
def update_signal():
    """API endpoint to update traffic signals"""
    # This endpoint now relies on the main dashboard data for consistency
    lane_feeds = get_lane_feeds_data() # Get latest data
    signal_data = map_lane_data_to_signal_format(lane_feeds) # Convert it
    
    return jsonify({
        'lanes': signal_data
    })

@app.route('/api/update_vehicles')
def update_vehicles_api():
    """API endpoint to get updated vehicle data from lane feeds"""
    # This endpoint now relies on the main dashboard data for consistency
    lane_feeds = get_lane_feeds_data()
    signal_data = map_lane_data_to_signal_format(lane_feeds) # Convert it
    
    return jsonify({
        'lanes': signal_data # Return the converted, fresh data
    })

@app.route('/')
def index():
    return render_template('index.html', now=time.time())

@app.route('/api/dashboard-data')
def dashboard_data():
    return jsonify(get_dashboard_data())

@app.route('/api/lane-feeds')
def lane_feeds():
    return jsonify(get_lane_feeds_data())

def generate_frames_on_demand():
    """
    Establishes a connection to the ESP32-CAM stream only when a client is connected.
    This prevents the Flask app from hogging the camera resource.
    The connection is automatically closed when the client disconnects.
    """
    response = None
    is_esp_stream_successful = False
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Client connected. Connecting to ESP32 stream...")
        response = requests.get(ESP32_STREAM_URL, stream=True, timeout=10)
        
        if response.status_code == 200:
            is_esp_stream_successful = True
            bytes_buffer = b''
            # Using response.iter_content to stream data
            for chunk in response.iter_content(chunk_size=1024):
                bytes_buffer += chunk
                a = bytes_buffer.find(b'\xff\xd8') # JPEG start
                b = bytes_buffer.find(b'\xff\xd9') # JPEG end
                if a != -1 and b != -1 and b > a:
                    jpeg_data = bytes_buffer[a:b+2]
                    bytes_buffer = bytes_buffer[b+2:]
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + jpeg_data + b'\r\n')
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Stream failed with HTTP status: {response.status_code}")
    
    except requests.exceptions.RequestException as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Stream connection error: {e}")

    finally:
        if response:
            response.close() # Ensure the connection is closed
        if is_esp_stream_successful:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Client disconnected. ESP32 stream connection closed.")

    # --- WEBCAM FALLBACK ---
    if not is_esp_stream_successful:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ESP32 stream failed. Attempting to fall back to webcam for raw feed.")
        yield from generate_frames_from_webcam()

@app.route('/video_feed/<int:lane_id>')
def video_feed(lane_id):
    """All lanes use the same ESP32 cam stream from shared capture"""
    # --- VIDEO FILE INTEGRATION ---
    if lane_id == 1:
        # Lane 1 uses the live ESP32 camera stream
        return Response(generate_frames_on_demand(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
    elif lane_id in VIDEO_FILES:
        # Other lanes use pre-recorded video files
        video_path = VIDEO_FILES[lane_id]
        return Response(generate_frames_from_file(video_path, lane_id),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        # Handle case where lane_id is not found
        return "Video feed not found for this lane.", 404
    # --- END VIDEO FILE INTEGRATION ---


@app.route('/traffic_detection_feed')
def traffic_detection_feed():
    """
    This feed connects to the ESP32, passes each frame to the YOLO detector,
    and streams the annotated video (with bounding boxes) to the client.
    """
    # --- AI DETECTION INTEGRATION ---
    return Response(generate_detection_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
    # --- END AI DETECTION INTEGRATION ---

def generate_frames_from_file(video_path, lane_id):
    """
    Generator function that reads frames from a video file, encodes them as JPEG,
    and yields them for streaming. It also performs vehicle detection.
    """
    while True: # Loop to make the video replay
        cap = None
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                print(f"[Video File] Error: Could not open video file {video_path}")
                break # Exit the loop if file can't be opened

            while True:
                ret, frame = cap.read()
                if not ret:
                    break # End of video, will restart due to outer loop
                
                # Encode frame to JPEG bytes to pass to the detector
                (flag, encoded_image) = cv2.imencode(".jpg", frame)
                if not flag:
                    continue
                
                # Process the frame with YOLO
                vehicle_count, annotated_frame = vehicle_detector.detect_vehicles(encoded_image.tobytes())
                REALTIME_DATA["vehicle_counts"][lane_id] = vehicle_count # Update global count for the specific lane

                yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + annotated_frame + b'\r\n')
        except Exception as e:
            print(f"[Video File] Error streaming from {video_path}: {e}")
        finally:
            if cap: cap.release()

def generate_detection_frames():
    """
    Generator function that captures frames from the ESP32 stream,
    processes them with the VehicleDetector, and yields the annotated frames.
    """
    response = None
    is_esp_stream_successful = False
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Detection client connected. Connecting to ESP32 stream...")
        response = requests.get(ESP32_STREAM_URL, stream=True, timeout=5) # Reduced timeout
        if response.status_code == 200:
            is_esp_stream_successful = True
            bytes_buffer = b''
            for chunk in response.iter_content(chunk_size=4096): # Increased chunk size
                bytes_buffer += chunk
                start = bytes_buffer.find(b'\xff\xd8') # JPEG start
                end = bytes_buffer.find(b'\xff\xd9')   # JPEG end
                if start != -1 and end != -1 and end > start:
                    jpeg_bytes = bytes_buffer[start:end+2]
                    bytes_buffer = bytes_buffer[end+2:]

                    # Process the frame with YOLO
                    vehicle_count, annotated_frame = vehicle_detector.detect_vehicles(jpeg_bytes)
                    REALTIME_DATA["vehicle_counts"][1] = vehicle_count # Update global count for Lane 1

                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + annotated_frame + b'\r\n')
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Detection stream failed with HTTP status: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"[Detection Feed] Stream connection error: {e}")
    finally:
        if response:
            response.close()
        if is_esp_stream_successful:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Detection client disconnected. ESP32 stream closed.")

    # --- WEBCAM FALLBACK ---
    if not is_esp_stream_successful:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ESP32 detection stream failed. Attempting to fall back to webcam.")
        yield from generate_detection_frames_from_webcam()

def generate_frames_from_webcam():
    """Generator for streaming raw frames from the local webcam."""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[Webcam] Error: Could not open webcam for raw feed.")
        return
    try:
        while True:
            ret, frame = cap.read()
            if not ret: break
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret: continue
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    finally:
        cap.release()
        print("[Webcam] Raw feed webcam released.")

def generate_detection_frames_from_webcam():
    """Generator for streaming YOLO-processed frames from the local webcam."""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[Webcam] Error: Could not open webcam for detection.")
        return
    try:
        while True:
            ret, frame = cap.read()
            if not ret: break
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret: continue
            
            vehicle_count, annotated_frame = vehicle_detector.detect_vehicles(buffer.tobytes())
            REALTIME_DATA["vehicle_counts"][1] = vehicle_count

            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + annotated_frame + b'\r\n')
    finally:
        cap.release()
        print("[Webcam] Detection feed webcam released.")

@app.route('/api/set_signal', methods=['POST'])
def set_signal_from_ai():
    """
    API endpoint for the DQN agent to set the active green light.
    Expects JSON: {"lane": <int>, "green_time": <float>}
    """
    data = request.get_json()
    if not data or 'lane' not in data:
        return jsonify({'status': 'error', 'message': 'Invalid payload. "lane" key is required.'}), 400

    lane_id = data['lane']
    green_time = data.get('green_time', 8) # Default to 8s if not provided
    set_active_green_lane(lane_id, green_time) # Update the backend module's state
    # print(f"Signal Updated by AI: Lane {lane_id} is now GREEN") # Optional: for debugging
    return jsonify({'status': 'success', 'message': f'Signal for lane {lane_id} set to green.'})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

    #version 1.1