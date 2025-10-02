# from flask import Flask, render_template, request, jsonify
# import requests

# app = Flask(__name__)

# # Replace with your ESP32-CAM IP address
# ESP32_IP = "192.168.72.86"  # Your ESP32-CAM's IP address

# @app.route('/')
# def index():
#     return render_template('index.html', esp32_ip=ESP32_IP)

# @app.route('/flash/<action>')
# def control_flash(action):
#     """Control the ESP32-CAM flash LED"""
#     try:
#         if action == 'on':
#             # Send request to turn flash on
#             response = requests.get(f'http://{ESP32_IP}/control?var=led_intensity&val=255', timeout=5)
#         elif action == 'off':
#             # Send request to turn flash off
#             response = requests.get(f'http://{ESP32_IP}/control?var=led_intensity&val=0', timeout=5)
#         else:
#             return jsonify({'status': 'error', 'message': 'Invalid action'}), 400
        
#         if response.status_code == 200:
#             return jsonify({'status': 'success', 'message': f'Flash turned {action}'})
#         else:
#             return jsonify({'status': 'error', 'message': 'ESP32 responded with error'}), 500
            
#     except requests.exceptions.RequestException as e:
#         return jsonify({'status': 'error', 'message': f'Connection error: {str(e)}'}), 500

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000, debug=True)