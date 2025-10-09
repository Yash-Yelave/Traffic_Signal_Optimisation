from flask import Flask, render_template, jsonify, Response
# Removed 'import cv2' as we are no longer using it for stream capture due to compatibility issues
import json
import random
import time
import threading
from datetime import datetime
import requests 
from static.modules.traffic_signal_backend import map_lane_data_to_signal_format

app = Flask(__name__)

# Global variables for shared camera stream
# esp32_cap = None # Removed OpenCV VideoCapture object
esp32_frame = None # Holds raw JPEG bytes now
esp32_lock = threading.Lock()
capture_thread = None
is_capturing = False


# ESP32-CAM IP address
ESP32_IP = "192.168.72.86"
# Combined stream URL constant for requests
ESP32_STREAM_URL = f'http://{ESP32_IP}:81/stream'

# Flash control route for ESP32
@app.route('/flash/<action>')
def control_flash(action):
    """Control the ESP32-CAM flash LED"""
    try:
        if action == 'on':
            # FIX: Reduced intensity from 255 to 64. Max intensity often causes the camera to brown-out and freeze.
            response = requests.get(f'http://{ESP32_IP}/control?var=led_intensity&val=64', timeout=5)
        elif action == 'off':
            response = requests.get(f'http://{ESP32_IP}/control?var=led_intensity&val=0', timeout=5)
        else:
            return jsonify({'status': 'error', 'message': 'Invalid action'}), 400
        
        if response.status_code == 200:
            return jsonify({'status': 'success', 'message': f'Flash turned {action}'})
        else:
            return jsonify({'status': 'error', 'message': 'ESP32 responded with error'}), 500
            
    except requests.exceptions.RequestException as e:
        return jsonify({'status': 'error', 'message': f'Connection error: {str(e)}'}), 500


def capture_esp32_stream():
    """Background thread to continuously capture frames from ESP32 using requests to handle raw MJPEG stream."""
    global esp32_frame, is_capturing
    
    while is_capturing:
        try:
            # Open the stream connection using requests (robust against OpenCV issues)
            response = requests.get(ESP32_STREAM_URL, stream=True, timeout=5)
            
            if response.status_code == 200:
                # Buffer to hold incomplete JPEG data chunks
                bytes_buffer = b''
                
                # Iterate over the raw content chunks
                for chunk in response.iter_content(chunk_size=1024):
                    if not is_capturing: break

                    bytes_buffer += chunk
                    
                    # Look for JPEG Start of Image (SOI: 0xFFD8) and End of Image (EOI: 0xFFD9) markers
                    a = bytes_buffer.find(b'\xff\xd8')
                    b = bytes_buffer.find(b'\xff\xd9')
                    
                    if a != -1 and b != -1 and b > a:
                        # Found a complete JPEG frame
                        jpeg_data = bytes_buffer[a:b+2]
                        
                        with esp32_lock:
                            esp32_frame = jpeg_data
                        
                        # Discard the successfully processed frame data from the buffer
                        bytes_buffer = bytes_buffer[b+2:]
                        
                    time.sleep(0.001) # Minimal sleep to yield execution
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Stream failed with HTTP status: {response.status_code}. Retrying in 2s.")
                time.sleep(2)
                
        except requests.exceptions.RequestException as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Connection error in background thread: {e}. Retrying in 3s.")
            time.sleep(3)
            
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Background capture thread stopped.")


def start_capture_thread():
    """Start the background capture thread"""
    global capture_thread, is_capturing
    
    if capture_thread is None or not capture_thread.is_alive():
        is_capturing = True
        capture_thread = threading.Thread(target=capture_esp32_stream, daemon=True)
        capture_thread.start()

# Start capturing when app starts
start_capture_thread()


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
            'vehicles': random.randint(20, 30),
            'speed': random.randint(40, 50),
            'traffic': random.randint(70, 85),
            'alert': 'Heavy congestion detected'
        },
        {
            'id': 2,
            'name': 'Lane 2',
            'status': 'ACTIVE',
            'direction': 'South',
            'vehicles': random.randint(10, 20),
            'speed': random.randint(55, 70),
            'traffic': random.randint(30, 45),
            'alert': None
        },
        {
            'id': 3,
            'name': 'Lane 3',
            'status': 'ACTIVE',
            'direction': 'East',
            'vehicles': random.randint(5, 15),
            'speed': random.randint(25, 40),
            'traffic': random.randint(50, 65),
            'alert': 'Accident detected'
        },
        {
            'id': 4,
            'name': 'Lane 4',
            'status': 'ACTIVE',
            'direction': 'West',
            'vehicles': random.randint(15, 25),
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
    active_lanes = [lane for lane in lanes if lane['vehicles'] > 0]
    avg_speed = sum(lane['speed'] for lane in active_lanes) // len(active_lanes) if active_lanes else 0
    avg_congestion = sum(lane['traffic'] for lane in lanes) // len(lanes)
    
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
    
    # Build lane performance from actual data
    lane_performance = []
    for lane in lanes:
        lane_performance.append({
            'name': lane['name'],
            'status': lane['status'],
            'vehicles': lane['vehicles'],
            'speed': lane['speed'],
            'congestion': lane['traffic']
        })
    
    return {
        'lanes': lanes, # Add full lane data to the main dashboard endpoint
        'simulation_lanes': map_lane_data_to_signal_format(lanes), # Add pre-formatted data for the simulation
        'total_vehicles': total_vehicles,
        'avg_speed': avg_speed,
        'avg_congestion': avg_congestion,
        'vehicle_distribution': {
            'cars': random.randint(50, 70),
            'trucks': random.randint(15, 30),
            'buses': random.randint(5, 15),
            'bikes': random.randint(3, 8)
        },
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
        'lane_performance': lane_performance,
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
    # Get fresh data from the unified source
    lane_feeds = get_lane_feeds_data() # Get latest data
    signal_data = map_lane_data_to_signal_format(lane_feeds) # Convert it
    
    return jsonify({
        'lanes': signal_data
    })

@app.route('/api/update_vehicles')
def update_vehicles_api():
    """API endpoint to get updated vehicle data from lane feeds"""
    # Get real-time data from your existing system
    lane_feeds = get_lane_feeds_data()
    signal_data = map_lane_data_to_signal_format(lane_feeds) # Convert it
    
    return jsonify({
        'lanes': signal_data # Return the converted, fresh data
    })

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/dashboard-data')
def dashboard_data():
    return jsonify(get_dashboard_data())

@app.route('/api/lane-feeds')
def lane_feeds():
    return jsonify(get_lane_feeds_data())

def generate_frames():
    """Generate frames from shared ESP32 camera feed (raw JPEG data from requests)"""
    global esp32_frame
    
    while True:
        if esp32_frame is not None:
            with esp32_lock:
                frame_bytes = esp32_frame # Frame is already raw JPEG bytes from the requests stream
            
            # Yield the pre-encoded JPEG bytes for the MJPEG stream
            # We skip cv2.imencode and cv2.resize since we are delivering the raw bytes
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        else:
            # FIX: Minimized sleep to reduce client-side waiting latency.
            time.sleep(0.01)

@app.route('/video_feed/<int:lane_id>')
def video_feed(lane_id):
    """All lanes use the same ESP32 cam stream from shared capture"""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/traffic_detection_feed')
def traffic_detection_feed():
    """Traffic detection feed also uses shared ESP32 stream"""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

    #version 1.1