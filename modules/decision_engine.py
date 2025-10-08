def get_signal_decision(data):
    """
    Example decision logic:
    - Input: dictionary with lane traffic counts
      e.g., {"lane1": 5, "lane2": 2, "lane3": 7}
    - Output: lane with maximum traffic
    """
    if not data or not isinstance(data, dict):
        return "Invalid data"
    
    # Pick the lane with the most vehicles
    lane = max(data, key=data.get)
    return lane
