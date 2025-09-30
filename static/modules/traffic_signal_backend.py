# Traffic Signal Backend Module
import random

# Sample data structure for lanes
# Each lane: [lane_no, total_vehicles, big_vehicles, small_vehicles, signal_color]
lanes_data = [
    [1, 15, 5, 10, 'red'],
    [2, 8, 2, 6, 'green'],
    [3, 12, 4, 8, 'red'],
    [4, 6, 1, 5, 'yellow']
]

def get_lanes_data():
    """
    Returns lane data in format:
    [lane_no, total_count, big_vehicle_count, small_vehicle_count, signal_color]
    """
    return lanes_data

def update_signal_lights():
    """
    Simulates traffic signal changes
    Cycles through: green -> yellow -> red
    """
    global lanes_data
    
    # Find current green light
    green_lane = -1
    for i, lane in enumerate(lanes_data):
        if lane[4] == 'green':
            green_lane = i
            break
    
    if green_lane != -1:
        # Change green to yellow
        lanes_data[green_lane][4] = 'yellow'
    else:
        # Find yellow light and change to red, make next lane green
        for i, lane in enumerate(lanes_data):
            if lane[4] == 'yellow':
                lanes_data[i][4] = 'red'
                next_lane = (i + 1) % len(lanes_data)
                lanes_data[next_lane][4] = 'green'
                break

def update_vehicles():
    """
    Simulate vehicle count changes
    """
    global lanes_data
    
    # Randomly update vehicle counts
    for lane in lanes_data:
        lane[2] = max(0, lane[2] + random.randint(-1, 2))  # big vehicles
        lane[3] = max(0, lane[3] + random.randint(-2, 3))  # small vehicles
        lane[1] = lane[2] + lane[3]  # total vehicles