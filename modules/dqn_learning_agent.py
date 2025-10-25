"""
dqn_learning_agent.py
- Contains the full DDQNAgent and TrafficDQNManager for making traffic signal decisions.
- The agent uses a Double Deep Q-Network to learn optimal traffic control strategies.
- This file is for reference and testing, and is not connected to the main application.
"""

import random
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from collections import deque
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

# --- DQN Agent Configuration ---
MEMORY_SIZE = 10000  # Number of experiences to store
BATCH_SIZE = 64      # Number of experiences to learn from at once
GAMMA = 0.95         # Discount factor for future rewards
EPSILON_START = 1.0  # Starting exploration rate
EPSILON_DECAY = 0.9995 # Rate at which to reduce exploration
EPSILON_MIN = 0.01   # Minimum exploration rate
LEARNING_RATE = 0.001 # Learning rate for the optimizer
TARGET_UPDATE_FREQ = 10 # Update the target network every 10 learning steps

class QNetwork(nn.Module):
    """Neural Network for approximating the Q-function."""
    def __init__(self, state_size, action_size):
        super(QNetwork, self).__init__()
        self.layer1 = nn.Linear(state_size, 128)
        self.layer2 = nn.Linear(128, 128)
        self.layer3 = nn.Linear(128, action_size)

    def forward(self, x):
        x = F.relu(self.layer1(x))
        x = F.relu(self.layer2(x))
        return self.layer3(x)

class DDQNAgent:
    """
    Double Deep Q-Network Agent.
    """
    def __init__(self, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.q_network = QNetwork(state_size, action_size).to(self.device)
        self.target_network = QNetwork(state_size, action_size).to(self.device)
        self.target_network.load_state_dict(self.q_network.state_dict())
        self.target_network.eval()

        self.optimizer = optim.Adam(self.q_network.parameters(), lr=LEARNING_RATE)
        self.memory = deque(maxlen=MEMORY_SIZE)
        self.epsilon = EPSILON_START
        self.learn_step_counter = 0

    def remember(self, state, action, reward, next_state):
        """Store experience in replay memory."""
        self.memory.append((state, action, reward, next_state))

    def choose_action(self, state):
        """Choose an action using an epsilon-greedy policy."""
        if random.random() <= self.epsilon:
            return random.randrange(self.action_size)  # Explore
        
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        with torch.no_grad():
            action_values = self.q_network(state_tensor)
        return np.argmax(action_values.cpu().data.numpy()) # Exploit

    def learn(self):
        """Learn from a batch of experiences in memory."""
        if len(self.memory) < BATCH_SIZE:
            return None, None # Not enough memory to learn

        experiences = random.sample(self.memory, BATCH_SIZE)
        states, actions, rewards, next_states = zip(*experiences)

        states = torch.FloatTensor(np.array(states)).to(self.device)
        actions = torch.LongTensor(actions).unsqueeze(1).to(self.device)
        rewards = torch.FloatTensor(rewards).unsqueeze(1).to(self.device)
        next_states = torch.FloatTensor(np.array(next_states)).to(self.device)

        # Get Q-values for current states from the main network
        q_values = self.q_network(states).gather(1, actions)

        # Get best action for next states from the main network
        next_actions = self.q_network(next_states).detach().max(1)[1].unsqueeze(1)
        # Get Q-values for next states from the target network
        next_q_values = self.target_network(next_states).detach().gather(1, next_actions)

        # Compute the expected Q-values (Bellman equation)
        expected_q_values = rewards + (GAMMA * next_q_values)

        # Compute loss
        loss = F.smooth_l1_loss(q_values, expected_q_values)

        # Optimize the model
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        return loss.item(), torch.mean(q_values).item()

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

        # Small penalty for waiting vehicles to encourage clearing traffic
        total_waiting = sum(new_counts)
        reward -= total_waiting * 0.1

        return reward

    def get_action(self, current_counts, ambulance_flags):
        """
        Decides the next action using the DDQN agent.
        It overrides the agent's decision if an ambulance is present.
        """
        # --- Rule 1: Ambulance Priority (Hard-coded override) ---
        if any(ambulance_flags):
            lane_to_activate_idx = np.argmax(ambulance_flags)
            green_time = 16 # Give max time for ambulance
            reason = "Priority (Ambulance)"
            # Find a corresponding action_index
            action_index = next(i for i, (l, t) in enumerate(ACTIONS) if l == lane_to_activate_idx and t == green_time)
        else:
            # --- AI-Based Action ---
            state = np.concatenate([current_counts, ambulance_flags])
            action_index = self.agent.choose_action(state)
            reason = f"DQN Decision (e={self.agent.epsilon:.2f})"

        lane_to_activate_idx, green_time = ACTIONS[action_index]

        self.last_decision = (int(lane_to_activate_idx) + 1, float(green_time)) # Use 1-based lane index
        print(f"🚦 AI Action: Lane {self.last_decision[0]} for {self.last_decision[1]}s | Reason: {reason}")
        
        return self.last_decision, action_index, reason

    def remember_experience(self, prev_counts, ambulance_flags, action_index, next_counts):
        """
        Calculates reward and stores the experience tuple in the agent's memory.
        """
        prev_state = np.concatenate([prev_counts, ambulance_flags])
        next_state = np.concatenate([next_counts, [0]*LANES]) # Assume ambulance is gone

        lane_selected, _ = ACTIONS[action_index]
        reward = self._calculate_reward(prev_counts, next_counts, lane_selected, ambulance_flags)
        self.cycle_rewards.append(reward)

        self.agent.remember(prev_state, action_index, reward, next_state)
        print(f"🧠 Cycle Stats: Action on Lane {lane_selected+1} -> Cleared: {max(0, prev_counts[lane_selected] - next_counts[lane_selected])} vehicles. Reward: {reward:.2f}")

    def learn_from_memory(self):
        """
        Triggers the agent to learn from its experience replay memory.
        """
        loss, q_value = self.agent.learn()
        if loss is not None:
            self.cycle_losses.append(loss)
            self.cycle_q_values.append(q_value)
            self.agent.learn_step_counter += 1
            # Update target network periodically
            if self.agent.learn_step_counter % TARGET_UPDATE_FREQ == 0:
                self.agent.target_network.load_state_dict(self.agent.q_network.state_dict())
                print("🎯 Target network updated.")

    def get_and_reset_cycle_metrics(self):
        """Returns the average metrics for the completed cycle and resets the logs."""
        avg_reward = np.mean(self.cycle_rewards) if self.cycle_rewards else 0
        avg_loss = np.mean(self.cycle_losses) if self.cycle_losses else 0
        avg_q = np.mean(self.cycle_q_values) if self.cycle_q_values else 0
        self.cycle_rewards, self.cycle_losses, self.cycle_q_values = [], [], []
        return avg_reward, avg_loss, avg_q

    def save_agent_state(self):
        """Saves the full agent state, including the model and epsilon value."""
        print("\n💾 Saving agent state...")
        try:
            torch.save(self.agent.q_network.state_dict(), self.model_path)
            with open(self.model_path + ".epsilon", "w") as f:
                f.write(str(self.agent.epsilon))
            print("✅ Agent state saved successfully.")
        except Exception as e:
            print(f"❌ Error saving agent state: {e}")

    def load_agent_state(self):
        """Loads the agent state if saved files exist."""
        if os.path.exists(self.model_path):
            print(f"🧠 Loading model weights from {self.model_path}...")
            try:
                self.agent.q_network.load_state_dict(torch.load(self.model_path))
                self.agent.target_network.load_state_dict(self.agent.q_network.state_dict())
                print("✅ Model loaded successfully.")
            except Exception as e:
                print(f"❌ Error loading model: {e}. Starting with a fresh model.")
        else:
            print("No pre-trained model found. Starting with a fresh model.")

        if os.path.exists(self.model_path + ".epsilon"):
            try:
                with open(self.model_path + ".epsilon", "r") as f:
                    self.agent.epsilon = float(f.read())
                print(f"✅ Epsilon loaded: {self.agent.epsilon:.4f}")
            except Exception as e:
                print(f"❌ Error loading epsilon: {e}. Using default start value.")