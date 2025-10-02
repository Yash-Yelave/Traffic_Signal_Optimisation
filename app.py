from flask import Flask, render_template, jsonify, Response
# Removed 'import cv2' as we are no longer using it for stream capture due to compatibility issues
import json
import random
import time
import threading
from datetime import datetime
import requests
from static.modules.traffic_signal_backend import get_lanes_data, update_signal_lights, map_lane_data_to_signal_format
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

#traffic signal routes with these:
@app.route('/api/lanes')
def get_lanes():
    """API endpoint to get current lane data - uses real data from lane feeds"""
    # Get your existing lane feeds data
    lane_feeds = get_lane_feeds_data()
    
    # Convert to traffic signal format
    signal_data = map_lane_data_to_signal_format(lane_feeds)
    
    return jsonify({
        'lanes': signal_data
    })

@app.route('/api/update_signal')
def update_signal():
    """API endpoint to update traffic signals"""
    # Get fresh data from your existing lane feeds
    lane_feeds = get_lane_feeds_data()
    signal_data = map_lane_data_to_signal_format(lane_feeds)
    
    # Optionally apply signal cycling logic
    update_signal_lights()
    
    return jsonify({
        'lanes': get_lanes_data()
    })

@app.route('/api/update_vehicles')
def update_vehicles_api():
    """API endpoint to get updated vehicle data from lane feeds"""
    # Get real-time data from your existing system
    lane_feeds = get_lane_feeds_data()
    signal_data = map_lane_data_to_signal_format(lane_feeds)
    
    return jsonify({
        'lanes': signal_data
    })

# Sample data for the dashboard
def get_dashboard_data():
    return {
        'total_vehicles': random.randint(50, 100),
        'avg_speed': random.randint(35, 55),
        'avg_congestion': random.randint(40, 80),
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
        'lane_performance': [
            {
                'name': 'Lane 1',
                'status': 'WARNING',
                'vehicles': random.randint(20, 30),
                'speed': random.randint(40, 50),
                'congestion': random.randint(70, 85)
            },
            {
                'name': 'Lane 2',
                'status': 'ACTIVE',
                'vehicles': random.randint(10, 20),
                'speed': random.randint(55, 70),
                'congestion': random.randint(30, 45)
            }
        ],
        'recent_alerts': [
            {
                'type': 'ACCIDENT',
                'message': 'Vehicle accident detected on Lane 2',
                'time': '10 min ago'
            },
            {
                'type': 'HIGH CONGESTION',
                'message': 'Heavy traffic detected on Lane 1',
                'time' : '5 min ago'
            }
        ]
    }

def get_lane_feeds_data():
    return [
        {
            'id': 1,
            'name': 'Lane 1',
            'status': 'WARNING',
            'direction': 'so',
            'vehicles': random.randint(20, 30),
            'speed': random.randint(40, 50),
            'traffic': random.randint(70, 85),
            'alert': 'Heavy congestion detected'
        },
        {
            'id': 2,
            'name': 'Lane 2',
            'status': 'Yash',
            'direction': 'South',
            'vehicles': random.randint(10, 20),
            'speed': random.randint(55, 70),
            'traffic': random.randint(30, 45),
            'alert': None
        },
        {
            'id': 3,
            'name': 'Lane 3',
            'status': 'ERROR',
            'direction': 'East',
            'vehicles': 0,
            'speed': 0,
            'traffic': 0,
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
