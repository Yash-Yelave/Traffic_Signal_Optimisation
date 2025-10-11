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
LR = 1e-4
GAMMA = 0.99
EPSILON_START = 1.0
EPSILON_DECAY = 0.995
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
        self.optimizer.step()

        # Softly update the target network
        self._soft_update_target_network()

        # Decay epsilon
        self.epsilon = max(EPSILON_MIN, self.epsilon * EPSILON_DECAY)

    def _soft_update_target_network(self):
        """Soft update model parameters: θ_target = τ*θ_local + (1 - τ)*θ_target"""
        for target_param, local_param in zip(self.q_target.parameters(), self.q_local.parameters()):
            target_param.data.copy_(self.tau * local_param.data + (1.0 - self.tau) * target_param.data)

class TrafficDQNManager:
    """
    Manages the DQN agent and the interaction with the traffic environment.
    This class is designed to be instantiated and used within the main Flask app.
    """
    def __init__(self):
        self.agent = DDQNAgent(STATE_SIZE, N_ACTIONS)
        self.last_decision = None
        print("🧠 DQN Manager initialized.")

    def _calculate_reward(self, prev_counts, new_counts, lane_idx, amb_flags):
        """
        Calculates the reward.
        The reward is primarily based on the number of vehicles cleared from the selected lane.
        A large bonus is given for clearing a lane with an ambulance.
        """
        cleared_vehicles = max(prev_counts[lane_idx] - new_counts[lane_idx], 0)
        reward = cleared_vehicles * 2  # Base reward for each cleared vehicle
        
        # Bonus for prioritizing an ambulance
        if amb_flags[lane_idx] == 1:
            reward += 50
        
        return reward

    def make_decision(self, current_counts, ambulance_flags):
        """
        Takes the current traffic state, runs it through the DQN agent,
        and returns the chosen action (lane and green time).
        
        This method also handles the agent's learning cycle (remembering and learning).
        """
        # 1. Form the current state vector
        current_state = np.concatenate([current_counts, ambulance_flags]).astype(float)

        # 2. Get an action from the agent
        action_index = self.agent.act(current_state)
        lane_selected, green_time = ACTIONS[action_index]

        # 3. Simulate the result of this action to get the next state and reward
        # This is a simplified model of traffic flow for agent training purposes.
        simulated_next_counts = list(current_counts)
        
        # Estimate how many vehicles will clear in the given green time.
        # This is a very simple heuristic: roughly 1 vehicle every 4 seconds.
        cleared_vehicles = np.random.randint(1, max(2, int(green_time // 4) + 1))
        simulated_next_counts[lane_selected] = max(0, simulated_next_counts[lane_selected] - cleared_vehicles)
        
        # Assume ambulance clears if its lane is chosen
        simulated_next_amb_flags = list(ambulance_flags)
        if simulated_next_amb_flags[lane_selected] == 1:
            simulated_next_amb_flags[lane_selected] = 0

        # 4. Calculate the reward based on the simulation
        reward = self._calculate_reward(current_counts, simulated_next_counts, lane_selected, ambulance_flags)
        
        # 5. Form the next state vector
        next_state = np.concatenate([simulated_next_counts, simulated_next_amb_flags]).astype(float)

        # 6. Store this experience in the agent's memory and trigger learning
        # For this simulation, we assume the episode is never "done"
        self.agent.remember(current_state, action_index, reward, next_state, False)
        self.agent.learn()

        # 7. Store and return the decision
        self.last_decision = (int(lane_selected), float(green_time))
        print(f"🚦 DQN Decision: Lane {lane_selected} for {green_time}s | Reward: {reward:.2f} | Epsilon: {self.agent.epsilon:.3f}")
        
        return self.last_decision