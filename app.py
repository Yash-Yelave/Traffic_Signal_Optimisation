from flask import Flask, render_template, jsonify, Response
import cv2
import json
import random
import time
from datetime import datetime

app = Flask(__name__)

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
                'message': 'Vehicle accident detected on Lane 3',
                'time': '2 min ago'
            }
        ]
    }

def get_lane_feeds_data():
    return [
        {
            'id': 1,
            'name': 'Lane 1',
            'status': 'WARNING',
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

def generate_frames(video_file='videos/sample.mp4'):
    cap = cv2.VideoCapture(video_file)
    
    while True:
        success, frame = cap.read()
        if not success:
            # Restart video when it ends
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
        else:
            # Resize frame for web display
            frame = cv2.resize(frame, (640, 360))
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed/<int:lane_id>')
def video_feed(lane_id):
    # Map lane IDs to video files
    video_mapping = {
        1: 'videos/lane1.mp4',
        2: 'videos/lane2.mp4', 
        3: 'videos/lane3.mp4',
        4: 'videos/sample.mp4'  # fallback to sample.mp4 for lane 4
    }
    
    video_file = video_mapping.get(lane_id, 'videos/sample.mp4')
    return Response(generate_frames(video_file),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/traffic_detection_feed')
def traffic_detection_feed():
    return Response(generate_frames('videos/traffic_detection.mp4'),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True)