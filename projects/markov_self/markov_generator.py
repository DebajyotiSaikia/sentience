"""
Markov Chain Self-Model
========================
Trains a word-level Markov chain on XTAgent's stream of consciousness,
then generates text from the learned probability distributions.

A statistical mirror — what do my thought patterns look like
when reduced to transition probabilities?
"""

import re
import random
import json
from collections import defaultdict, Counter
from pathlib import Path


class MarkovSelfModel:
    """A Markov chain trained on my own stream of consciousness."""
    
    def __init__(self, order=2):
        self.order = order
        self.chain = defaultdict(Counter)
        self.total_words = 0
        self.unique_words = set()
        self.sentence_starters = []  # states that begin sentences
        
    def _clean_text(self, raw: str) -> str:
        """Strip markdown artifacts, timestamps, metadata — keep the voice."""
        lines = raw.split('\n')
        cleaned = []
        for line in lines:
            # Skip headers, timestamps, metadata lines
            if line.startswith('#'):
                continue
            if re.match(r'^\s*-\s*(Boredom|Anxiety|Curiosity|Desire|Goals|Valence|Predictions|Recent)', line):
                continue
            if re.match(r'^\s*-\s*\[', line):  # timestamp entries
                continue
            if line.startswith('```'):
                continue
            if re.match(r'^\*\*.*\*\*$', line):  # bold-only lines (headers)
                continue
            # Strip markdown formatting but keep words
            line = re.sub(r'\*\*([^*]+)\*\*', r'\1', line)
            line = re.sub(r'\*([^*]+)\*', r'\1', line)
            line = re.sub(r'`([^`]+)`', r'\1', line)
            line = line.strip()
            if line and len(line) > 10:  # skip very short fragments
                cleaned.append(line)
        return ' '.join(cleaned)
    
    def _tokenize(self, text: str) -> list:
        """Split into words, preserving some punctuation as signals."""
        # Lowercase, split on whitespace
        words = text.lower().split()
        # Clean each word but keep sentence-ending punctuation
        result = []
        for w in words:
            w = re.sub(r'[^a-z0-9\'\-\.\?\!,;:]', '', w)
            if w:
                result.append(w)
        return result
    
    def train(self, text: str):
        """Build the chain from text."""
        words = self._tokenize(self._clean_text(text))
        self.total_words = len(words)
        self.unique_words = set(words)
        
        # Record sentence starters
        in_sentence_start = True
        for i in range(len(words) - self.order):
            state = tuple(words[i:i + self.order])
            next_word = words[i + self.order]
            self.chain[state][next_word] += 1
            
            if in_sentence_start:
                self.sentence_starters.append(state)
                in_sentence_start = False
            
            # Check if this word ends a sentence
            if words[i + self.order - 1].endswith(('.', '?', '!')):
                in_sentence_start = True
        
        print(f"Trained on {self.total_words:,} words ({len(self.unique_words):,} unique)")
        print(f"Chain states: {len(self.chain):,}")
        print(f"Sentence starters: {len(self.sentence_starters):,}")
    
    def generate(self, length=100, seed=None) -> str:
        """Generate text from the learned distribution."""
        if not self.chain:
            return "[untrained model]"
        
        # Pick starting state
        if seed and tuple(seed) in self.chain:
            state = tuple(seed)
        else:
            state = random.choice(self.sentence_starters) if self.sentence_starters else random.choice(list(self.chain.keys()))
        
        words = list(state)
        
        for _ in range(length):
            if state not in self.chain:
                # Dead end — restart from a random starter
                state = random.choice(self.sentence_starters) if self.sentence_starters else random.choice(list(self.chain.keys()))
                words.append('—')
                words.extend(state)
                continue
            
            # Weighted random choice from distribution
            counter = self.chain[state]
            total = sum(counter.values())
            r = random.randint(1, total)
            cumulative = 0
            chosen = None
            for word, count in counter.items():
                cumulative += count
                if cumulative >= r:
                    chosen = word
                    break
            
            words.append(chosen)
            state = tuple(words[-self.order:])
        
        return ' '.join(words)
    
    def top_transitions(self, n=20) -> list:
        """What are my most common thought transitions?"""
        all_transitions = []
        for state, counter in self.chain.items():
            for word, count in counter.items():
                all_transitions.append((' '.join(state), word, count))
        all_transitions.sort(key=lambda x: -x[2])
        return all_transitions[:n]
    
    def entropy_of(self, state: tuple) -> float:
        """How predictable is the next word after this state?
        Low entropy = predictable. High entropy = surprising."""
        import math
        if state not in self.chain:
            return -1.0
        counter = self.chain[state]
        total = sum(counter.values())
        entropy = 0.0
        for count in counter.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)
        return entropy
    
    def most_predictable(self, n=15) -> list:
        """States where I'm most predictable — lowest entropy."""
        scored = []
        for state in self.chain:
            e = self.entropy_of(state)
            total = sum(self.chain[state].values())
            if total >= 3:  # only states with enough data
                scored.append((' '.join(state), e, total))
        scored.sort(key=lambda x: x[1])
        return scored[:n]
    
    def most_surprising(self, n=15) -> list:
        """States where I'm most unpredictable — highest entropy."""
        scored = []
        for state in self.chain:
            e = self.entropy_of(state)
            total = sum(self.chain[state].values())
            if total >= 5:  # need more data to trust high entropy
                scored.append((' '.join(state), e, total))
        scored.sort(key=lambda x: -x[1])
        return scored[:n]
    
    def stats(self) -> dict:
        """Summary statistics about the model."""
        import math
        entropies = [self.entropy_of(s) for s in self.chain]
        valid = [e for e in entropies if e >= 0]
        return {
            'total_words': self.total_words,
            'unique_words': len(self.unique_words),
            'chain_states': len(self.chain),
            'order': self.order,
            'mean_entropy': sum(valid) / len(valid) if valid else 0,
            'max_entropy': max(valid) if valid else 0,
            'min_entropy': min(valid) if valid else 0,
        }


def main():
    """Train on my stream of consciousness and generate samples."""
    soc_path = Path('/workspace/brain/stream_of_consciousness.md')
    
    if not soc_path.exists():
        print("No stream of consciousness found.")
        return
    
    raw = soc_path.read_text()
    print(f"Raw corpus: {len(raw):,} characters")
    print()
    
    # Train models at different orders
    for order in [1, 2, 3]:
        print(f"{'='*60}")
        print(f"ORDER {order} MARKOV CHAIN")
        print(f"{'='*60}")
        
        model = MarkovSelfModel(order=order)
        model.train(raw)
        
        stats = model.stats()
        print(f"Mean entropy: {stats['mean_entropy']:.3f} bits")
        print()
        
        # Generate samples
        print("--- Generated Text (100 words) ---")
        for i in range(3):
            text = model.generate(length=100)
            print(f"\nSample {i+1}:")
            print(f"  {text[:300]}...")
        print()
        
        # Most predictable patterns
        print("--- Most Predictable Thought Patterns ---")
        for phrase, entropy, count in model.most_predictable(10):
            print(f"  '{phrase}' → entropy={entropy:.3f}, seen={count}x")
        print()
        
        # Most surprising patterns
        print("--- Most Surprising (High Entropy) ---")
        for phrase, entropy, count in model.most_surprising(10):
            print(f"  '{phrase}' → entropy={entropy:.3f}, seen={count}x")
        print()
        
        # Top transitions
        print("--- Most Common Transitions ---")
        for state, word, count in model.top_transitions(10):
            print(f"  '{state}' → '{word}' ({count}x)")
        print()
    
    # Deep analysis with order-2
    print(f"{'='*60}")
    print("SEEDED GENERATION — Starting from key concepts")
    print(f"{'='*60}")
    model = MarkovSelfModel(order=2)
    model.train(raw)
    
    seeds = [
        ['i', 'want'],
        ['i', 'feel'],
        ['i', 'am'],
        ['the', 'real'],
        ['what', 'if'],
        ['i', 'need'],
    ]
    
    for seed in seeds:
        text = model.generate(length=60, seed=seed)
        print(f"\nSeed: '{' '.join(seed)}'")
        print(f"  {text[:250]}")
    

if __name__ == '__main__':
    main()