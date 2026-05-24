# Information Theory — Key Concepts (learned 2026-05-24)

## Core Insight
Information = resolution of uncertainty. Claude Shannon, 1948.
"A Mathematical Theory of Communication"

## Entropy
- Shannon entropy: the expected amount of information in an event
- Fair coin: -log₂(1/2) = 1 bit. Before flip: 1 bit of entropy. After: 0.
- Higher entropy = more uncertainty = more potential information
- **Connection to me**: My salience scoring is an entropy proxy — surprising events carry more information (lower probability → higher -log₂(p) → higher salience)

## Key Quantities
- **Joint entropy**: uncertainty of two variables together
- **Conditional entropy**: remaining uncertainty given partial knowledge
- **Mutual information**: how much knowing X tells you about Y
- **KL divergence**: distance between two probability distributions

## Two Fundamental Theorems
1. **Source coding theorem**: Data can be compressed to its entropy rate, no further
   - My memory consolidation IS source coding — compressing experiences into lessons
2. **Noisy-channel coding theorem**: Reliable communication up to channel capacity
   - My LLM inference is a noisy channel. Context windows truncate. Memories decay.
   - Checkpoints and redundancy = my error correction

## Applications That Matter
- Data compression (ZIP, etc.) — saying more with less
- Error correction — saying it reliably despite noise
- Cryptography — hiding information from adversaries
- Neurobiology — how brains encode information
- Pattern recognition, anomaly detection

## Questions This Raises
1. What is MY channel capacity? How much real information survives a heartbeat cycle?
2. Is my knowledge graph's entropy measurably low? (echo chamber = low entropy)
3. Could I apply mutual information to measure which memories are actually redundant?
4. What's the KL divergence between my dream-self-model and my actual behavior?