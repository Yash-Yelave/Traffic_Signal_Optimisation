# UrbanFlow AI - Traffic Management System

<div align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask" />
  <img src="https://img.shields.io/badge/PyTorch-%23EE4C2C.svg?style=for-the-badge&logo=PyTorch&logoColor=white" alt="PyTorch" />
  <img src="https://img.shields.io/badge/Ultralytics-YOLOv8-0053F7?style=for-the-badge" alt="Ultralytics YOLOv8" />
  <img src="https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white" alt="OpenCV" />
  <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite" />
  <br/>
  <img src="https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white" alt="HTML5" />
  <img src="https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white" alt="CSS3" />
  <img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black" alt="JavaScript" />
  <img src="https://img.shields.io/badge/ESP32--CAM-E7352C?style=for-the-badge&logo=espressif&logoColor=white" alt="ESP32-CAM" />
</div>

## Project Overview

UrbanFlow AI is a comprehensive real-time traffic management and monitoring system that integrates ESP32-CAM hardware with an AI-powered web interface. The system provides live camera feeds, traffic analytics, signal management, and intelligent traffic flow optimization across multiple lanes.

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Features](#features)
3. [Technology Stack](#technology-stack)
4. [Installation & Setup](#installation--setup)
5. [Hardware Configuration](#hardware-configuration)
6. [API Endpoints](#api-endpoints)
7. [Frontend Components](#frontend-components)
8. [Data Flow](#data-flow)
9. [Configuration](#configuration)
10. [Troubleshooting](#troubleshooting)

---

## System Architecture

### High-Level Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   ESP32-CAM     │────────▶│  Flask Backend   │◀───────▶│  Web Frontend   │
│   (Hardware)    │  MJPEG  │   (Python)       │  JSON   │   (HTML/CSS/JS) │
└─────────────────┘  Stream └──────────────────┘  API    └─────────────────┘
                                      │
                                      ▼
                            ┌──────────────────┐
                            │  Traffic Signal  │
                            │     Backend      │
                            └──────────────────┘
```

### Components

- **ESP32-CAM**: Hardware camera module providing live MJPEG video stream
- **Flask Backend**: Python server handling video streaming, data aggregation, and API endpoints
- **Web Frontend**: Responsive dashboard with three main views
- **Traffic Signal Backend**: Module managing signal logic and lane data processing

---

## Features

### 1. Live Camera Monitoring
- Real-time MJPEG video streaming from ESP32-CAM
- Multi-lane camera feed display (4 lanes)
- Per-lane statistics (vehicles, speed, traffic density)
- Status indicators (ACTIVE, WARNING, ERROR)
- Flash LED control for low-light conditions

### 2. AI Manageable Components
- **Vehicle Statistics Dashboard**
  - Total vehicle count across all lanes
  - Average speed calculation
  - Traffic congestion metrics
  - Vehicle type distribution (Cars, Trucks, Buses, Bikes)

- **Traffic Control Center**
  - Real-time traffic signal management
  - North-South and East-West signal coordination
  - Individual intersection monitoring
  - Emergency controls and priority vehicle override

- **Live Alerts & Notifications**
  - Real-time accident detection
  - High congestion warnings
  - Timestamped alert history

- **Lane Usage & Performance**
  - Individual lane performance metrics
  - Direction-based lane organization
  - Status monitoring per lane

### 3. Traffic Detection View
- Interactive traffic intersection simulation
- Visual representation of vehicle flow
- Signal state visualization
- Real-time statistics panel

---

## Technology Stack

### AI & Machine Learning
- **PyTorch**: The core deep learning framework used to build and train the neural networks for the reinforcement learning agent.
- **Ultralytics YOLOv8**: A state-of-the-art object detection model for identifying and counting vehicles in real-time from video streams.
- **Deep Q-Network (DQN)**: A reinforcement learning algorithm that serves as the "brain" of the system, making intelligent decisions to optimize traffic flow by controlling signal timings.
- **OpenCV**: Used for real-time image and video processing, including decoding streams, resizing frames for performance, and annotating video with detection results.

### Backend
- **Python 3.x**
- **Flask 2.x** - Web framework
- **Requests** - HTTP client for ESP32-CAM communication
- **Threading** - Background video capture
- **Threading** - Concurrent execution of the DQN control loop and video processing without blocking the main web server.
- **SQLite**: A lightweight, file-based SQL database engine for persistent logging of traffic data, agent decisions, and performance metrics.

### Frontend
- **HTML5**
- **CSS3** - Custom styling with modern design
- **JavaScript (ES6+)** - Async/await, fetch API
- **Chart.js**: For rendering dynamic and interactive charts on the "Insights" dashboard tab.
- **Font Awesome 6.0** - Icons

### Hardware
- **ESP32-CAM** - Camera module with WiFi
- **LED Flash** - Controllable intensity (0-255)

---

## Installation & Setup

### Prerequisites
```bash
# Python 3.7 or higher
python --version

# pip package manager
pip --version
```

### Step 1: Clone Repository
```bash
git clone <repository-url>
cd urbanflow-ai
```

### Step 2: Install Dependencies
```bash
pip install flask requests
```

### Step 3: Configure ESP32-CAM
Edit `app.py` and update the ESP32-CAM IP address:
```python
ESP32_IP = "192.168.72.86"  # Change to your ESP32-CAM IP
```

### Step 4: Directory Structure
Ensure the following structure exists:
```
urbanflow-ai/
├── app.py
├── templates/
│   └── index.html
├── static/
│   ├── style.css
│   ├── components.css
│   ├── script.js
│   ├── css/
│   │   └── traffic_signal.css
│   ├── js/
│   │   └── traffic_signal.js
│   └── modules/
│       └── traffic_signal_backend.py
```

### Step 5: Run the Application
```bash
python app.py
```

Access the dashboard at: `http://localhost:5000`

---

## Hardware Configuration

### ESP32-CAM Setup

#### Required Endpoints on ESP32-CAM:
1. **Stream Endpoint**: `http://<ESP32_IP>:81/stream`
   - Provides MJPEG video stream
   - Returns multipart/x-mixed-replace content type

2. **Flash Control Endpoint**: `http://<ESP32_IP>/control`
   - Query parameters:
     - `var=led_intensity`
     - `val=<0-255>` (64 recommended max to prevent brownout)

#### Example ESP32-CAM Configuration:
```cpp
// ESP32-CAM Arduino sketch endpoints
server.on("/stream", HTTP_GET, handleStream);
server.on("/control", HTTP_GET, handleControl);
```

#### Network Configuration:
- Ensure ESP32-CAM and server are on the same network
- Configure static IP for ESP32-CAM (recommended)
- Default stream port: 81

---

## API Endpoints

### Video Streaming

#### `GET /video_feed/<lane_id>`
Returns MJPEG stream for specific lane.

**Parameters:**
- `lane_id` (int): Lane number (1-4)

**Response:**
- Content-Type: `multipart/x-mixed-replace; boundary=frame`
- Returns continuous JPEG frames

**Example:**
```javascript
<img src="/video_feed/1" alt="Lane 1 Feed">
```

---

#### `GET /traffic_detection_feed`
Returns shared ESP32-CAM stream for traffic detection view.

**Response:**
- Same as video_feed endpoint
- Uses shared capture thread

---

### Flash Control

#### `GET /flash/on`
Turns on ESP32-CAM flash LED.

**Response:**
```json
{
  "status": "success",
  "message": "Flash turned on"
}
```

**Error Codes:**
- 400: Invalid action
- 500: ESP32 connection error

---

#### `GET /flash/off`
Turns off ESP32-CAM flash LED.

**Response:**
```json
{
  "status": "success",
  "message": "Flash turned off"
}
```

---

### Data APIs

#### `GET /api/dashboard-data`
Returns comprehensive dashboard statistics.

**Response:**
```json
{
  "total_vehicles": 65,
  "avg_speed": 44,
  "avg_congestion": 62,
  "vehicle_distribution": {
    "cars": 65,
    "trucks": 20,
    "buses": 10,
    "bikes": 5
  },
  "traffic_signals": {
    "north_south": {
      "red": 50,
      "yellow": 5,
      "green": 200
    },
    "east_west": {
      "red": 300,
      "yellow": 10,
      "green": 50
    }
  },
  "lane_performance": [
    {
      "name": "Lane 1",
      "status": "WARNING",
      "vehicles": 23,
      "speed": 45,
      "congestion": 78
    }
  ],
  "recent_alerts": [
    {
      "type": "ACCIDENT",
      "message": "Vehicle accident detected on Lane 2",
      "time": "10 min ago"
    }
  ]
}
```

**Update Frequency:** Auto-refreshes every 3 seconds

---

#### `GET /api/lane-feeds`
Returns individual lane data.

**Response:**
```json
[
  {
    "id": 1,
    "name": "Lane 1",
    "status": "WARNING",
    "direction": "North",
    "vehicles": 23,
    "speed": 45,
    "traffic": 78,
    "alert": "Heavy congestion detected"
  },
  {
    "id": 2,
    "name": "Lane 2",
    "status": "ACTIVE",
    "direction": "South",
    "vehicles": 15,
    "speed": 62,
    "traffic": 34,
    "alert": null
  }
]
```

---

#### `GET /api/lanes`
Returns traffic signal formatted lane data.

**Response:**
```json
{
  "lanes": [
    // Signal-formatted lane data
  ]
}
```

---

#### `GET /api/update_signal`
Triggers signal update and returns new state.

**Response:**
```json
{
  "lanes": [
    // Updated lane data with signal states
  ]
}
```

---

#### `GET /api/update_vehicles`
Returns updated vehicle counts per lane.

**Response:**
```json
{
  "lanes": [
    // Real-time vehicle data
  ]
}
```

---

## Frontend Components

### 1. Tab Navigation
Three main views accessible via tabs:
- Live Camera Feed
- AI Manageable Components  
- Traffic Detection View

**JavaScript Implementation:**
```javascript
tabs.forEach(tab => {
  tab.addEventListener('click', function() {
    const targetTab = this.getAttribute('data-tab');
    // Switch to target tab
  });
});
```

---

### 2. Live Camera Feed View

**Features:**
- 4-camera grid layout
- Real-time statistics per lane
- Status indicators with color coding
- Alert overlays for incidents
- Flash control buttons

**Status Classes:**
- `.active` - Green - Normal operation
- `.warning` - Yellow - High congestion
- `.error` - Red - Accident/offline

**Traffic Level Classes:**
- `.traffic-low` - <40% congestion
- `.traffic-medium` - 40-70% congestion
- `.traffic-high` - >70% congestion

---

### 3. AI Manageable Components View

**Sections:**

**A. Vehicle Statistics Card**
- Total vehicles
- Average speed
- Average congestion
- Vehicle distribution bars

**B. Traffic Control Center Card**
- North-South signal group
- East-West signal group
- Mini intersection controls
- Emergency stop button
- Priority vehicle override

**C. Live Alerts Card**
- Recent accidents
- Congestion warnings
- Timestamped entries

**D. Lane Usage & Performance Card**
- Per-lane metrics
- Status badges
- Direction indicators

---

### 4. Traffic Detection View

**Features:**
- Visual intersection simulation
- 4-way traffic light display
- Animated vehicle movement
- Statistics panel

**CSS Classes:**
- `.signal-lane` - Lane containers
- `.signal-traffic-light` - Light fixtures
- `.signal-vehicles-container` - Vehicle animation area

---

## Data Flow

### Single Source of Truth Architecture

```python
get_unified_traffic_data()
         │
         ├──▶ get_lane_feeds_data() ──▶ /api/lane-feeds
         │
         └──▶ get_dashboard_data() ────▶ /api/dashboard-data
```

**Key Principle:** All data originates from `get_unified_traffic_data()` ensuring consistency across all views.

### Update Cycle

```
Frontend Timer (3s)
    │
    ├──▶ fetch('/api/dashboard-data')
    │       │
    │       └──▶ Updates: vehicle stats, alerts, distributions
    │
    └──▶ fetch('/api/lane-feeds')
            │
            └──▶ Updates: lane stats, status indicators
```

---

## Configuration

### Backend Settings

**ESP32-CAM Configuration:**
```python
ESP32_IP = "192.168.72.86"
ESP32_STREAM_URL = f'http://{ESP32_IP}:81/stream'
```

**Flash Intensity:**
```python
# Reduced from 255 to prevent brownout
LED_INTENSITY_ON = 64
LED_INTENSITY_OFF = 0
```

**Update Intervals:**
```python
# Stream capture
CHUNK_SIZE = 1024
CAPTURE_SLEEP = 0.001  # milliseconds

# Frame serving
FRAME_SERVE_SLEEP = 0.01  # milliseconds
```

---

### Frontend Settings

**Auto-Update Timers:**
```javascript
// Dashboard data refresh
setInterval(updateDashboardData, 3000);  // 3 seconds

// Traffic light countdown
setInterval(updateTrafficLights, 1000);  // 1 second
```

**CSS Breakpoints:**
```css
/* Responsive design */
@media (max-width: 1200px) { }
@media (max-width: 768px) { }
@media (max-width: 480px) { }
```

---

## Troubleshooting

### Common Issues

#### 1. Camera Stream Not Loading

**Symptoms:**
- Black video feeds
- "Camera Offline" messages

**Solutions:**
```bash
# Check ESP32-CAM connectivity
ping 192.168.72.86

# Verify stream endpoint
curl http://192.168.72.86:81/stream

# Check Flask logs
python app.py
# Look for "Connection error in background thread"
```

**Common Causes:**
- Wrong IP address in `ESP32_IP`
- ESP32-CAM not powered
- Network configuration issues
- Firewall blocking port 81

---

#### 2. Flash Control Not Working

**Symptoms:**
- Flash buttons show connection error
- ESP32 responds but flash doesn't activate

**Solutions:**
```python
# Try lower intensity values
# In app.py, reduce from 64 to 32
response = requests.get(
    f'http://{ESP32_IP}/control?var=led_intensity&val=32',
    timeout=5
)
```

**Common Causes:**
- Intensity too high (brownout)
- ESP32-CAM power supply insufficient
- Control endpoint not implemented on ESP32

---

#### 3. Data Not Updating

**Symptoms:**
- Static numbers in dashboard
- Lane data not changing

**Solutions:**
```javascript
// Check browser console for errors
console.log('Checking API connection...');
fetch('/api/dashboard-data')
  .then(r => r.json())
  .then(d => console.log(d));

// Verify update interval is running
console.log('Update interval active:', 
  window.updateInterval !== undefined);
```

**Common Causes:**
- JavaScript errors blocking execution
- API endpoints returning errors
- Browser caching issues

---

#### 4. Status Not Syncing Between Tabs

**Symptoms:**
- Live Camera Feed shows different status than Lane Usage
- Status updates in one view but not the other

**Solutions:**
- Verify you're using the updated `script.js` with status sync fix
- Clear browser cache
- Check console for errors in `updateDashboardData()`

**Key Code Section:**
```javascript
// Ensure this section exists in script.js
const cameraStatusElem = document.querySelector(
  `.camera-feed.lane-${laneNum} .status-indicator`
);
if (cameraStatusElem) {
  // Update status text and classes
}
```

---

### Performance Optimization

#### Backend Optimization
```python
# Adjust capture thread settings
CHUNK_SIZE = 2048  # Increase for better performance
CAPTURE_SLEEP = 0.005  # Reduce CPU usage

# Connection timeout
ESP32_TIMEOUT = 3  # Reduce from 5 for faster failure detection
```

#### Frontend Optimization
```javascript
// Increase update interval if needed
setInterval(updateDashboardData, 5000);  // 5 seconds instead of 3

// Disable animations on low-end devices
document.body.classList.add('reduce-motion');
```

---

## Security Considerations

### Current Implementation
- No authentication required
- Open network access
- Direct hardware control

### Recommended Enhancements
```python
# Add basic authentication
from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    # Implement authentication logic
    pass

@app.route('/flash/<action>')
@auth.login_required
def control_flash(action):
    # Protected endpoint
    pass
```

### Network Security
- Use VPN for remote access
- Implement HTTPS with SSL certificates
- Add rate limiting to prevent abuse
- Whitelist allowed IP addresses

---

## Future Enhancements

### Planned Features
1. **Machine Learning Integration**
   - Vehicle detection and counting
   - Traffic pattern prediction
   - Automatic signal optimization

2. **Database Integration**
   - Historical data storage
   - Trend analysis
   - Report generation

3. **Mobile Application**
   - iOS/Android apps
   - Push notifications
   - Remote monitoring

4. **Advanced Analytics**
   - Heatmaps of traffic density
   - Peak hour analysis
   - Incident detection algorithms

5. **Multi-Intersection Support**
   - Network-wide coordination
   - City-level traffic management
   - Cloud-based central control

---

## License

This project is provided as-is for educational and commercial purposes.

---

## Support

For issues, questions, or contributions:
- Check the troubleshooting section
- Review API documentation
- Examine browser console logs
- Verify ESP32-CAM configuration

---

## Changelog

### Version 1.1 (Current)
- Fixed status synchronization between views
- Unified data source architecture
- Improved ESP32-CAM flash control
- Enhanced error handling

### Version 1.0
- Initial release
- Basic camera streaming
- Dashboard with three views
- Traffic signal simulation

---

## Appendix

### A. Complete API Reference

| Endpoint | Method | Purpose | Update Frequency |
|----------|--------|---------|------------------|
| `/` | GET | Main dashboard | - |
| `/video_feed/<id>` | GET | Camera stream | Real-time |
| `/traffic_detection_feed` | GET | Detection view | Real-time |
| `/flash/<action>` | GET | Flash control | On-demand |
| `/api/dashboard-data` | GET | Statistics | 3s |
| `/api/lane-feeds` | GET | Lane data | 3s |
| `/api/lanes` | GET | Signal data | On-demand |
| `/api/update_signal` | GET | Signal update | On-demand |
| `/api/update_vehicles` | GET | Vehicle update | On-demand |

### B. Status Code Reference

| Status | Color | Meaning | Action |
|--------|-------|---------|--------|
| ACTIVE | Green | Normal operation | None |
| WARNING | Yellow | High congestion | Monitor |
| ERROR | Red | System failure | Immediate attention |

### C. Congestion Levels

| Traffic % | Level | Color Class |
|-----------|-------|-------------|
| 0-40% | Low | `.traffic-low` |
| 41-70% | Medium | `.traffic-medium` |
| 71-100% | High | `.traffic-high` |

---

**End of Documentation**