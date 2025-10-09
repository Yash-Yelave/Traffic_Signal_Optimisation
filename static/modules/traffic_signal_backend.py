# Traffic Signal Backend Module - Integrated with existing app.py data

def map_lane_data_to_signal_format(lane_feeds_data):
    """
    Converts your existing lane feeds data to traffic signal format
    Input: lane_feeds_data from get_lane_feeds_data()
    Output: [lane_no, total_vehicles, signal_color]
    """
    processed_lanes = []

    for i, lane in enumerate(lane_feeds_data):
        if i >= 4:  # We only handle 4 lanes
            break
            
        lane_no = lane['id']
        total_vehicles = lane['vehicles']
        # Determine signal color based on traffic level
        traffic_level = lane['traffic']
        if traffic_level > 70:
            signal_color = 'red'  # High traffic - stop
        elif traffic_level > 40:
            signal_color = 'yellow'  # Medium traffic - caution
        else:
            signal_color = 'green'  # Low traffic - go
            
        processed_lanes.append([lane_no, total_vehicles, signal_color])
    
    return processed_lanes


def update_vehicles():
    """
    This function is no longer needed since we get real data from app.py
    Kept for compatibility
    """
    pass