"""
dqn.py
- Contains the DDQN agent and logic for making traffic signal decisions.
- Refactored from a standalone UDP server to an importable class for use with Flask.
"""

import random
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import os
from collections import deque

# ---------------- CONFIG ----------------
LANES = 4
# Available green light durations in seconds
ACTION_TIME_OPTIONS = [8, 12, 16]
# The action space is a combination of every lane and every possible green time
ACTIONS = [(lane, time) for lane in range(LANES) for time in ACTION_TIME_OPTIONS]
N_ACTIONS = len(ACTIONS)
# State is comprised of vehicle counts and ambulance flags for each lane
STATE_SIZE = LANES * 2

# Hyperparameters
# LR (Learning Rate) was too low (1e-4), causing the agent to get stuck on bad habits.
# Increasing it to 5e-4 will make the agent react more strongly to rewards and penalties,
# allowing it to break out of suboptimal strategies.
LR = 1e-3 # Increased further to make learning more aggressive.
GAMMA = 0.95 # Reduced to make the agent prioritize immediate rewards/penalties more.
EPSILON_START = 1.0 
# A higher decay rate (closer to 1) means slower learning (more exploration).
# A lower decay rate means faster learning (less exploration).
# Default was 0.995. Let's try 0.99 for faster convergence.
EPSILON_DECAY = 0.98 # Faster decay for quicker testing
EPSILON_MIN = 0.05
MEMORY_LIMIT = 5000
BATCH_SIZE = 32
TAU = 0.01 # For soft update of target network

class QNetwork(nn.Module):
    """Neural network for approximating the Q-function."""
    def __init__(self, state_size, action_size):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_size, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, action_size)
        )

    def forward(self, x):
        return self.net(x)

class DDQNAgent:
    """Double Deep Q-Network Agent."""
    def __init__(self, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size

        self.q_local = QNetwork(state_size, action_size)
        self.q_target = QNetwork(state_size, action_size)
        self.optimizer = optim.Adam(self.q_local.parameters(), lr=LR)
        
        # Replay memory
        self.memory = deque(maxlen=MEMORY_LIMIT)
        
        self.gamma = GAMMA
        self.epsilon = EPSILON_START
        self.tau = TAU

    def remember(self, state, action, reward, next_state, done):
        """Store experience in replay memory."""
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state):
        """
        Selects an action using an epsilon-greedy policy.
        With probability epsilon, it takes a random action.
        Otherwise, it takes the action with the highest Q-value.
        """
        if random.random() < self.epsilon:
            return random.randrange(self.action_size)
        
        state_t = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
        with torch.no_grad():
            q_values = self.q_local(state_t)
        return int(torch.argmax(q_values).item())

    def learn(self):
        """
        Trains the Q-network using a batch of experiences from memory.
        Implements the Double DQN algorithm for calculating the target Q-value.
        """
        if len(self.memory) < BATCH_SIZE:
            return

        # Sample a random batch of experiences
        batch = random.sample(self.memory, BATCH_SIZE)
        states, actions, rewards, next_states, dones = zip(*batch)

        states = torch.tensor(np.array(states), dtype=torch.float32)
        next_states = torch.tensor(np.array(next_states), dtype=torch.float32)
        actions = torch.tensor(actions, dtype=torch.int64).unsqueeze(1)
        rewards = torch.tensor(rewards, dtype=torch.float32).unsqueeze(1)
        dones = torch.tensor(dones, dtype=torch.float32).unsqueeze(1)

        # --- Double DQN Update ---
        # 1. Get the expected Q values from the local model
        q_expected = self.q_local(states).gather(1, actions)

        # 2. Get the best action from the local model for the next state
        next_actions = self.q_local(next_states).argmax(1, keepdim=True)
        
        # 3. Get the Q value for that action from the target model
        q_target_next = self.q_target(next_states).gather(1, next_actions)

        # 4. Compute the target Q value
        q_target = rewards + self.gamma * q_target_next * (1 - dones)

        # --- Standard DQN update (for comparison) ---
        # q_target_next = self.q_target(next_states).detach().max(1)[0].unsqueeze(1)
        # q_target = rewards + self.gamma * q_target_next * (1 - dones)

        # Compute loss and perform a gradient descent step
        loss = nn.MSELoss()(q_expected, q_target.detach())
        self.optimizer.zero_grad()
        loss.backward()
        # Optional: Print loss to monitor training progress
        # if random.random() < 0.01: # Print loss occasionally
        #     print(f"Training Loss: {loss.item():.4f}")
        self.optimizer.step()

        # Softly update the target network
        self._soft_update_target_network()

        # Decay epsilon
        self.epsilon = max(EPSILON_MIN, self.epsilon * EPSILON_DECAY)

    def save_model(self, file_path):
        """Saves the state of the model and optimizer."""
        torch.save({
            'q_local_state_dict': self.q_local.state_dict(),
            'q_target_state_dict': self.q_target.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
        }, file_path)

    def load_model(self, file_path):
        """Loads the state of the model and optimizer."""
        # It's best practice to load onto CPU first, then move to the correct device
        # This avoids GPU memory issues if the model was saved on a different device.
        # We set weights_only=False explicitly because we are loading an optimizer state
        # as well as model weights. This is safe as we are loading our own saved model.
        # This also resolves the FutureWarning.
        checkpoint = torch.load(file_path, map_location=torch.device('cpu'), weights_only=False)

        # Load model weights securely
        self.q_local.load_state_dict(checkpoint['q_local_state_dict'])
        self.q_target.load_state_dict(checkpoint['q_target_state_dict'])

        # Load optimizer state
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])

    def _soft_update_target_network(self):
        """Soft update model parameters: θ_target = τ*θ_local + (1 - τ)*θ_target"""
        for target_param, local_param in zip(self.q_target.parameters(), self.q_local.parameters()):
            target_param.data.copy_(self.tau * local_param.data + (1.0 - self.tau) * target_param.data)

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
        Takes the current traffic state and asks the agent for the best action.
        This is for INFERENCE only. The learning step is handled separately.
        """
        reason = "" # To explain the decision
        # 1. Form the current state vector
        current_state = np.concatenate([current_counts, ambulance_flags]).astype(float)

        # 2. Get an action from the agent
        if random.random() < self.agent.epsilon:
            reason = "Exploration (random action)"
            
            # --- NEW: Smarter Exploration ---
            # Find lanes that actually have vehicles.
            congested_lanes = [i for i, count in enumerate(current_counts) if count > 0]
            
            if congested_lanes:
                # Create a list of valid actions (only for lanes with cars).
                valid_actions = [i for i, (lane, time) in enumerate(ACTIONS) if lane in congested_lanes]
                if valid_actions:
                    action_index = random.choice(valid_actions)
                else: # Fallback if something goes wrong
                    action_index = random.randrange(self.agent.action_size)
            else: # If all lanes are empty, just pick any random action.
                action_index = random.randrange(self.agent.action_size)
        else:
            state_t = torch.tensor(current_state, dtype=torch.float32).unsqueeze(0)
            with torch.no_grad():
                q_values = self.agent.q_local(state_t)
            action_index = int(torch.argmax(q_values).item())
            reason = "Exploitation (best action)"

        lane_selected, green_time = ACTIONS[action_index] # Unpack the action

        # 3. Store and return the decision
        self.last_decision = (int(lane_selected) + 1, float(green_time)) # Use 1-based lane index
        print(f"🚦 DQN Action: Lane {self.last_decision[0]} for {self.last_decision[1]}s | Reason: {reason} | Epsilon: {self.agent.epsilon:.3f}")
        
        return self.last_decision, action_index, reason

    def remember_experience(self, prev_counts, ambulance_flags, action_index, next_counts):
        """
        Calculates reward for a completed action and stores it in the agent's memory.
        This does NOT trigger the learning step.
        """
        # 1. Reconstruct the states
        prev_state = np.concatenate([prev_counts, ambulance_flags]).astype(float)
        next_ambulance_flags = list(ambulance_flags)
        lane_selected, _ = ACTIONS[action_index]
        if next_ambulance_flags[lane_selected] == 1:
            next_ambulance_flags[lane_selected] = 0
        next_state = np.concatenate([next_counts, next_ambulance_flags]).astype(float)

        # 2. Calculate the real reward
        reward = self._calculate_reward(prev_counts, next_counts, lane_selected, ambulance_flags)

        # 3. Store this real experience in the agent's memory
        self.agent.remember(prev_state, action_index, reward, next_state, False)
        print(f"🧠 Experience Stored: Action on Lane {lane_selected+1} -> Reward: {reward:.2f}")

    def learn_from_memory(self):
        """
        Triggers the agent to learn from a batch of experiences in its memory.
        This can be called at any time, e.g., during a waiting period.
        """
        self.agent.learn()

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
        print(f"\n💾 Saving agent state to {self.model_path}...")
        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        # Save the model weights
        self.agent.save_model(self.model_path)
        
        # Save epsilon value in a separate file
        with open(self.model_path + ".epsilon", "w") as f:
            f.write(str(self.agent.epsilon))
        print("✅ Agent state saved successfully.")

    def load_agent_state(self):
        """Loads the agent state if saved files exist."""
        if os.path.exists(self.model_path) and os.path.exists(self.model_path + ".epsilon"):
            print(f"✅ Found pre-trained model. Loading state from {self.model_path}...")
            self.agent.load_model(self.model_path)
            with open(self.model_path + ".epsilon", "r") as f:
                self.agent.epsilon = float(f.read())
            print(f"🧠 Agent state loaded. Resuming with Epsilon: {self.agent.epsilon:.3f}")