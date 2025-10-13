# Traffic Signal Backend Module - Integrated with existing app.py data
import time
import requests
import random

# --- DEMO CONFIGURATION ---
# In a real implementation, these values would come from your AI decision module (e.g., DQN).
# For this simulation, you can change these values to test different scenarios.
# The `ACTIVE_GREEN_LANE_ID` determines which lane gets the 'green' signal.
SIGNAL_STATE = {
    "active_green_lane_id": 1,  # Default to lane 1
    "green_time_start": time.time(),
    "green_time_duration": 8 # Default duration
}

def set_active_green_lane(lane_id, green_time=8):
    """
    Updates the active green lane ID and sends a command to the ESP32 if the lane is 1.
    """
    SIGNAL_STATE["active_green_lane_id"] = lane_id
    SIGNAL_STATE["green_time_start"] = time.time()
    SIGNAL_STATE["green_time_duration"] = green_time

    # If the target lane is Lane 1, send a command to the physical ESP32 signal.
    if lane_id == 1:
        esp32_signal_ip = "10.44.36.86"
        command_url = f"http://{esp32_signal_ip}/start-green?time={int(green_time)}"
        try:
            print(f"🚦 Sending GREEN command to ESP32 for Lane 1: {command_url}")
            requests.get(command_url, timeout=3)
            print("✅ ESP32 command sent successfully.")
        except requests.exceptions.RequestException as e:
            print(f"❌ ERROR: Could not send command to ESP32 for Lane 1. Details: {e}")


def map_lane_data_to_signal_format(lane_feeds_data):
    """
    Converts your existing lane feeds data to traffic signal format
    based on which lane is designated as green.

    Input:
        lane_feeds_data: The list of lane data from get_unified_traffic_data().
    Output:
        A list of lists, where each inner list is [lane_no, total_vehicles, signal_color].
    """
    processed_lanes = []

    # Get the currently active green lane from our state
    active_lane = SIGNAL_STATE["active_green_lane_id"]

    for lane in lane_feeds_data:
        lane_no = lane['id']
        total_vehicles = lane['vehicles']

        # Set signal color based on the active green lane ID
        signal_color = 'green' if lane_no == active_lane else 'red'
            
        processed_lanes.append([lane_no, total_vehicles, signal_color])
    
    return processed_lanes


def update_vehicles():
    """
    This function is no longer needed since we get real data from app.py
    Kept for compatibility
    """
    pass