"""
Agent — A neural-network creature that perceives, moves, and signals.

Each agent has a small feedforward network:
  Input: [dx_resource, dy_resource, nearby_agents, heard_signals..., energy_level]
  Hidden: 16 neurons (tanh)
  Output: 4 move directions + N signal outputs (softmax each)
"""

import numpy as np
import random


class Agent:
    """A single agent in the Babel world."""

    HIDDEN_SIZE = 16

    def __init__(self, x=0, y=0, id=0, SYMBOL_SPACE=8):
        self.x = x
        self.y = y
        self.id = id
        self.symbol_space = SYMBOL_SPACE
        self.energy = 50.0
        self.age = 0
        self.generation = 0
        self.resources_collected = 0
        self.signals_emitted = 0
        self.current_signal = 0

        # Perception: dx, dy to nearest resource, n_nearby, heard_signal (one-hot),
        #             energy_normalized = 3 + SYMBOL_SPACE + 1
        self.input_size = 3 + SYMBOL_SPACE + 1

        # Neural weights — randomly initialized
        scale = 0.5
        self.W_hidden = np.random.randn(self.input_size, self.HIDDEN_SIZE) * scale
        self.b_hidden = np.zeros((1, self.HIDDEN_SIZE))
        self.W_move = np.random.randn(self.HIDDEN_SIZE, 4) * scale
        self.b_move = np.zeros((1, 4))
        self.W_signal = np.random.randn(self.HIDDEN_SIZE, SYMBOL_SPACE) * scale
        self.b_signal = np.zeros((1, SYMBOL_SPACE))

        # Memory of last heard signal
        self.last_heard = -1

    def perceive(self, world):
        """Build input vector from world state."""
        inp = np.zeros((1, self.input_size))

        # Nearest resource direction
        nearby = world.nearby_resources(self.x, self.y, radius=8)
        if nearby:
            closest = min(nearby, key=lambda r: abs(r.x - self.x) + abs(r.y - self.y))
            inp[0, 0] = (closest.x - self.x) / world.width
            inp[0, 1] = (closest.y - self.y) / world.height
        
        # Nearby agent count
        n_nearby = sum(1 for a in world.agents if a.id != self.id
                       and abs(a.x - self.x) <= 4 and abs(a.y - self.y) <= 4
                       and a.energy > 0)
        inp[0, 2] = min(n_nearby / 5.0, 1.0)

        # Heard signal (one-hot)
        heard = world.get_signal_at(self.x, self.y, exclude_id=self.id)
        if heard >= 0:
            self.last_heard = heard
            inp[0, 3 + heard] = 1.0

        # Energy level
        inp[0, 3 + self.symbol_space] = min(self.energy / 100.0, 1.0)

        return inp

    def think(self, perception):
        """Forward pass through neural network. Returns (move_dir, signal)."""
        # Hidden layer
        hidden = np.tanh(perception @ self.W_hidden + self.b_hidden)

        # Move output (softmax → sample)
        move_logits = (hidden @ self.W_move + self.b_move).flatten()
        move_probs = self._softmax(move_logits)
        move_dir = np.random.choice(4, p=move_probs)

        # Signal output (softmax → sample)
        sig_logits = (hidden @ self.W_signal + self.b_signal).flatten()
        sig_probs = self._softmax(sig_logits)
        signal = np.random.choice(self.symbol_space, p=sig_probs)

        return int(move_dir), int(signal)

    def _softmax(self, x):
        e = np.exp(x - np.max(x))
        return e / e.sum()