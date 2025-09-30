# Traffic Signal Backend Module - Integrated with existing app.py data
import random

# This will be populated from your existing lane feeds data
lanes_data = [
    [1, 0, 0, 0, 'red'],
    [2, 0, 0, 0, 'green'],
    [3, 0, 0, 0, 'red'],
    [4, 0, 0, 0, 'yellow']
]

def map_lane_data_to_signal_format(lane_feeds_data):
    """
    Converts your existing lane feeds data to traffic signal format
    Input: lane_feeds_data from get_lane_feeds_data()
    Output: [lane_no, total_vehicles, big_vehicles, small_vehicles, signal_color]
    """
    global lanes_data
    
    for i, lane in enumerate(lane_feeds_data):
        if i >= 4:  # We only handle 4 lanes
            break
            
        lane_no = lane['id']
        total_vehicles = lane['vehicles']
        
        # Distribute vehicles into big and small (you can adjust this logic)
        # Assuming 30% are big vehicles, 70% are small
        big_vehicles = int(total_vehicles * 0.3)
        small_vehicles = total_vehicles - big_vehicles
        
        # Determine signal color based on traffic level
        traffic_level = lane['traffic']
        if traffic_level > 70:
            signal_color = 'red'  # High traffic - stop
        elif traffic_level > 40:
            signal_color = 'yellow'  # Medium traffic - caution
        else:
            signal_color = 'green'  # Low traffic - go
            
        lanes_data[i] = [lane_no, total_vehicles, big_vehicles, small_vehicles, signal_color]
    
    return lanes_data

def get_lanes_data():
    """
    Returns lane data in format:
    [lane_no, total_count, big_vehicle_count, small_vehicle_count, signal_color]
    """
    return lanes_data

def update_signal_lights():
    """
    Simulates traffic signal changes
    Note: This is called but actual signal state comes from map_lane_data_to_signal_format
    """
    global lanes_data
    
    # Find current green light
    green_lane = -1
    for i, lane in enumerate(lanes_data):
        if lane[4] == 'green':
            green_lane = i
            break
    
    if green_lane != -1:
        lanes_data[green_lane][4] = 'yellow'
    else:
        for i, lane in enumerate(lanes_data):
            if lane[4] == 'yellow':
                lanes_data[i][4] = 'red'
                next_lane = (i + 1) % len(lanes_data)
                lanes_data[next_lane][4] = 'green'
                break

def update_vehicles():
    """
    This function is no longer needed since we get real data from app.py
    Kept for compatibility
    """
    pass