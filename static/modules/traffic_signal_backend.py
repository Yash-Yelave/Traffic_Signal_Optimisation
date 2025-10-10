# Traffic Signal Backend Module - Integrated with existing app.py data
import time
import random



# --- DEMO CONFIGURATION ---
# In a real implementation, these values would come from your AI decision module (e.g., DQN).
# For this simulation, you can change these values to test different scenarios.
# The `ACTIVE_GREEN_LANE_ID` determines which lane gets the 'green' signal.
ACTIVE_GREEN_LANE_ID = 1   # Example: Lane 1 is c  urrently green.


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

    # This logic now simulates a decision from an external AI module.
    # The lane with the ID matching ACTIVE_GREEN_LANE_ID will be 'green',
    # and all other lanes will be 'red'.
    for lane in lane_feeds_data:
        lane_no = lane['id']
        total_vehicles = lane['vehicles']

        # Set signal color based on the active green lane ID
        signal_color = 'green' if lane_no == ACTIVE_GREEN_LANE_ID else 'red'
            
        processed_lanes.append([lane_no, total_vehicles, signal_color])
    
    return processed_lanes


def update_vehicles():
    """
    This function is no longer needed since we get real data from app.py
    Kept for compatibility
    """
    pass