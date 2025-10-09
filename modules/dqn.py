"""
dqn.py
- Receives detection data via UDP from detection.py.
- Runs a DDQN agent to select (lane, green_time).
- Sends decision back as a list [lane, green_time].
"""

import socket
import json
import time
import random
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

# ---------------- CONFIG ----------------
LANES = 4
ACTION_TIME_OPTIONS = [8, 12, 16]               # green signal durations in seconds
ACTIONS = [(l, t) for l in range(LANES) for t in ACTION_TIME_OPTIONS]
N_ACTIONS = len(ACTIONS)
STATE_SIZE = LANES * 2
LR = 1e-4
GAMMA = 0.99
EPSILON = 1.0
EPS_DECAY = 0.995
EPS_MIN = 0.05
MEMORY_LIMIT = 5000
BATCH_SIZE = 32
TAU = 0.01

# UDP addresses
RECV_ADDR = ("127.0.0.1", 5005)   # receives detections
SEND_ADDR = ("127.0.0.1", 5006)   # sends decisions to detection.py

# ---------------- NETWORKS / AGENT ----------------
class QNetwork(nn.Module):
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
    def __init__(self):
        self.q_local = QNetwork(STATE_SIZE, N_ACTIONS)
        self.q_target = QNetwork(STATE_SIZE, N_ACTIONS)
        self.optimizer = optim.Adam(self.q_local.parameters(), lr=LR)
        self.memory = []
        self.gamma = GAMMA
        self.eps = EPSILON
        self.tau = TAU

    def remember(self, exp):
        self.memory.append(exp)
        if len(self.memory) > MEMORY_LIMIT:
            self.memory.pop(0)

    def act(self, state):
        # ε-greedy action selection
        if random.random() < self.eps:
            return random.randrange(N_ACTIONS)
        state_t = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
        with torch.no_grad():
            qvals = self.q_local(state_t)
        return int(torch.argmax(qvals).item())

    def learn(self):
        if len(self.memory) < BATCH_SIZE:
            return
        batch = random.sample(self.memory, BATCH_SIZE)
        s, a, r, s2, done = zip(*batch)
        s = torch.tensor(np.array(s), dtype=torch.float32)
        s2 = torch.tensor(np.array(s2), dtype=torch.float32)
        a = torch.tensor(a, dtype=torch.int64).unsqueeze(1)
        r = torch.tensor(r, dtype=torch.float32).unsqueeze(1)
        done = torch.tensor(done, dtype=torch.float32).unsqueeze(1)

        q_expected = self.q_local(s).gather(1, a)
        next_actions = self.q_local(s2).argmax(1, keepdim=True)
        q_target_next = self.q_target(s2).gather(1, next_actions)
        q_target = r + self.gamma * q_target_next * (1 - done)

        loss = nn.MSELoss()(q_expected, q_target.detach())
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        # soft update target network
        for t, l in zip(self.q_target.parameters(), self.q_local.parameters()):
            t.data.copy_(self.tau * l.data + (1.0 - self.tau) * t.data)

        self.eps = max(EPS_MIN, self.eps * EPS_DECAY)

# ---------------- Reward ----------------
def reward_fn(prev_counts, new_counts, lane_idx, amb_flags):
    """
    Reward is based on vehicles cleared + ambulance priority
    """
    cleared = max(prev_counts[lane_idx] - new_counts[lane_idx], 0)
    reward = cleared * 2
    if amb_flags[lane_idx] == 1:
        reward += 10
    return reward

# ---------------- Networking ----------------
recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
recv_sock.bind(RECV_ADDR)
send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# ---------------- MAIN ----------------
def main():
    agent = DDQNAgent()
    last_action_time = 0
    action_cooldown = 2  # seconds between decisions

    print(f"🧠 DQN listening on {RECV_ADDR} and will send decisions to {SEND_ADDR}")

    try:
        while True:
            data, _ = recv_sock.recvfrom(4096)
            det = json.loads(data.decode("utf-8"))
            counts = np.array(det.get("counts", [0]*LANES), dtype=int)
            amb = np.array(det.get("amb", [0]*LANES), dtype=int)
            state = np.concatenate([counts, amb]).astype(float)

            # Pick action
            action_idx = agent.act(state)
            lane_selected, green_time = ACTIONS[action_idx]

            # Simulate state transition (simple clearance model)
            simulated = counts.copy()
            cleared = np.random.randint(1, max(2, int(green_time // 4) + 1))
            simulated[lane_selected] = max(0, simulated[lane_selected] - cleared)

            # Compute reward
            reward = reward_fn(counts, simulated, lane_selected, amb)
            next_state = np.concatenate([simulated, amb]).astype(float)

            # Store experience & learn
            agent.remember((state, action_idx, reward, next_state, False))
            agent.learn()

            # Send decision as LIST
            now = time.time()
            if now - last_action_time >= action_cooldown:
                decision_list = [int(lane_selected), float(green_time)]
                send_sock.sendto(str(decision_list).encode("utf-8"), SEND_ADDR)
                last_action_time = now
                print(f"🚦 Decision sent: {decision_list} | reward={reward:.2f}")

    except KeyboardInterrupt:
        print("🛑 DQN stopped by user")

    finally:
        recv_sock.close()
        send_sock.close()

if __name__ == "__main__":
    main()
