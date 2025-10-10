# Traffic Signal Backend Module - Integrated with existing app.py data
import time
import random

# --- DEMO CONFIGURATION ---
# In a real implementation, these values would come from your AI decision module (e.g., DQN).
# For this simulation, you can change these values to test different scenarios.
# The `ACTIVE_GREEN_LANE_ID` determines which lane gets the 'green' signal.
SIGNAL_STATE = {
    "active_green_lane_id": 1  # Default to lane 1
}

def set_active_green_lane(lane_id):
    """Updates the active green lane ID from an external source (like an API call)."""
    SIGNAL_STATE["active_green_lane_id"] = lane_id


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