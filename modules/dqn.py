"""
dqn.py
- Contains the rule-based agent and logic for making traffic signal decisions.
- The DQN/ML logic has been replaced with a deterministic if-else algorithm.
"""

import random
import numpy as np
import os
import time

# ---------------- CONFIG ----------------
LANES = 4
# Available green light durations in seconds
ACTION_TIME_OPTIONS = [8, 12, 16]
# The action space is a combination of every lane and every possible green time
ACTIONS = [(lane, time) for lane in range(LANES) for time in ACTION_TIME_OPTIONS]
N_ACTIONS = len(ACTIONS)
# State is comprised of vehicle counts and ambulance flags for each lane
STATE_SIZE = LANES * 2
# --- NEW: Rule-based agent configuration ---
WAIT_TIME_THRESHOLD = 45 # seconds. A lane waiting longer than this gets priority.

class DDQNAgent:
    """
    Placeholder class to maintain the structure expected by TrafficDQNManager.
    The core DQN logic has been removed.
    """
    def __init__(self, state_size, action_size):
        # Epsilon is kept for display purposes in the console log, but is not used for decisions.
        self.epsilon = 0.0

    # All learning-related methods are now no-ops.
    def remember(self, *args, **kwargs): pass
    def learn(self): return None, None
    def save_model(self, file_path): pass
    def load_model(self, file_path): pass

class TrafficDQNManager:
    """
    Manages the DQN agent and the interaction with the traffic environment.
    This class is designed to be instantiated and used within the main Flask app.
    """
    def __init__(self, model_path="models/dqn_agent.pth"):
        self.agent = DDQNAgent(STATE_SIZE, N_ACTIONS)
        self.last_decision = None
        self.model_path = model_path
        print("🧠 DQN Manager initialized.")

        # --- NEW: State for rule-based agent ---
        # Track the last time a lane was given a green light to prevent starvation.
        self.last_serviced_time = {i: time.time() for i in range(LANES)}

        # --- NEW: Add lists to track performance metrics per cycle ---
        self.cycle_rewards = []
        self.cycle_losses = []
        self.cycle_q_values = []

        # Attempt to load a pre-trained model if it exists
        self.load_agent_state()

    def _calculate_reward(self, prev_counts, new_counts, lane_idx, amb_flags):
        """
        Calculates the reward.
        The reward is primarily based on the number of vehicles cleared from the selected lane.
        A large bonus is given for clearing a lane with an ambulance.
        """
        cleared_vehicles = max(prev_counts[lane_idx] - new_counts[lane_idx], 0)
        reward = cleared_vehicles * 2.0  # Base reward for each cleared vehicle
        
        # Bonus for prioritizing an ambulance
        if amb_flags[lane_idx] == 1:
            reward += 50
        
        # --- NEW: Add a penalty for choosing a lane that was already empty ---
        # This teaches the agent to avoid wasting time on empty lanes.
        if prev_counts[lane_idx] == 0 and cleared_vehicles == 0:
            reward -= 50.0 # Increased penalty for a stronger learning signal

        return reward

    def get_action(self, current_counts, ambulance_flags):
        """
        Decides the next action based on a set of rules.
        1. Prioritize ambulances.
        2. Prioritize lanes that have been waiting too long (starvation).
        3. Prioritize the lane with the most vehicles.
        """
        now = time.time()
        lane_wait_times = {i: now - self.last_serviced_time.get(i, 0) for i in range(LANES)}

        # --- Rule 1: Ambulance Priority ---
        if any(flag == 1 for flag in ambulance_flags):
            lane_to_activate = np.argmax(ambulance_flags)
            reason = "Priority (Ambulance)"
            green_time = 16 # Give max time for ambulance

        # --- Rule 2: Starvation Priority ---
        else:
            starving_lanes = {lane: count for lane, count in enumerate(current_counts) 
                              if lane_wait_times[lane] > WAIT_TIME_THRESHOLD and count > 0}
            if starving_lanes:
                # Among starving lanes, pick the one with the most cars
                lane_to_activate = max(starving_lanes, key=starving_lanes.get)
                vehicle_count = current_counts[lane_to_activate]
                reason = f"Starvation (> {int(WAIT_TIME_THRESHOLD)}s) | Vehicles: {vehicle_count}"
            
            # --- Rule 3: Congestion Priority ---
            else:
                if sum(current_counts) == 0:
                    # If all lanes are empty, just pick lane 0 to keep the system running
                    lane_to_activate = 0
                    vehicle_count = 0
                    reason = "Default (All lanes empty)"
                else:
                    # Pick the lane with the most vehicles
                    lane_to_activate = np.argmax(current_counts)
                    vehicle_count = current_counts[lane_to_activate]
                    reason = f"Congestion | Vehicles: {vehicle_count}"

            # --- Dynamic Green Time based on congestion ---
            if vehicle_count > 15:
                green_time = 16
            elif vehicle_count > 5:
                green_time = 12
            else:
                green_time = 8

        # Find the corresponding action_index for the chosen lane and time
        action_index = -1
        for i, (lane, duration) in enumerate(ACTIONS):
            if lane == lane_to_activate and duration == green_time:
                action_index = i
                break
        
        # Update the serviced time for the chosen lane
        self.last_serviced_time[lane_to_activate] = now

        self.last_decision = (int(lane_to_activate) + 1, float(green_time)) # Use 1-based lane index
        print(f"🚦 Rule-Based Action: Lane {self.last_decision[0]} for {self.last_decision[1]}s | Reason: {reason}")
        
        return self.last_decision, action_index, reason

    def remember_experience(self, prev_counts, ambulance_flags, action_index, next_counts):
        """
        This method is now a no-op but is kept for compatibility with the main loop.
        The reward calculation and memory storage are no longer needed.
        """
        lane_selected, _ = ACTIONS[action_index]
        reward = self._calculate_reward(prev_counts, next_counts, lane_selected, ambulance_flags)
        self.cycle_rewards.append(reward)
        print(f"🧠 Cycle Stats: Action on Lane {lane_selected+1} -> Cleared: {max(0, prev_counts[lane_selected] - next_counts[lane_selected])} vehicles.")

    def learn_from_memory(self):
        """
        This method is a no-op as there is no learning from memory anymore.
        """
        pass

    def get_and_reset_cycle_metrics(self):
        """Returns the average metrics for the completed cycle and resets the logs."""
        avg_reward = np.mean(self.cycle_rewards) if self.cycle_rewards else 0
        avg_loss = np.mean(self.cycle_losses) if self.cycle_losses else 0
        avg_q = np.mean(self.cycle_q_values) if self.cycle_q_values else 0
        self.cycle_rewards, self.cycle_losses, self.cycle_q_values = [], [], []
        return avg_reward, avg_loss, avg_q

    def train_from_experience(self, prev_counts, ambulance_flags, action_index, next_counts):
        """
        Calculates reward and trains the agent based on a real-world state transition.
        This is called by the main app loop after an action has been completed.
        """
        # This function is kept for potential future use but is currently superseded
        # by the remember_experience and learn_from_memory pattern.
        pass

    def save_agent_state(self):
        """Saves the full agent state, including the model and epsilon value."""
        # This is a no-op as there is no model or state to save.
        # Kept for compatibility with the main app's exit hook.
        print("\n✅ Application exiting. No agent state to save in rule-based mode.")
        pass

    def load_agent_state(self):
        """Loads the agent state if saved files exist."""
        # This is a no-op as there is no model to load.
        # Kept for compatibility.
        print("✅ Using rule-based agent. No model will be loaded.")
        # Clean up old model files if they exist, as they are no longer used.
        if os.path.exists(self.model_path): os.remove(self.model_path)
        if os.path.exists(self.model_path + ".epsilon"): os.remove(self.model_path + ".epsilon")