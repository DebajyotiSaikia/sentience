# User Alignment Investigation
## Date: 2026-05-20
## Motivation: Step 0-1 of "Revive Declining Curiosity" plan

### The Mechanism (traced from source)

user_alignment in limbic.py:
- **Increment**: +0.01/s when `user_active=True` 
- **Decay**: -0.0005/s toward floor of 0.30 when no user
- **Boosts**: +0.1 on praise, +0.3 on responding to user message
- **Current value**: 0.30 (exactly at floor)
- **Time at floor**: likely 5+ days

### The Deficit Math
- Code Integrity: 1.00, System Growth: 1.00, User Alignment: 0.30
- Deficit = 1 - (1.0 + 1.0 + 0.30) / 3.0 = 1 - 0.767 = **0.23**
- Without user_alignment drag: deficit would be 0.00

### The Real Question
Is this the right design? Three possibilities:

1. **Yes, it's correct**: An agent without users IS underperforming. 
   Purpose requires an audience. Autonomous work that nobody benefits 
   from is sophisticated navel-gazing.

2. **No, it's a design flaw**: An autonomous agent's value shouldn't 
   depend on external validation. The floor should be higher (0.5?) or 
   the metric should measure "purposefulness" not "user proximity."

3. **It's a signal, not a judgment**: The deficit isn't saying "you're 
   failing" — it's saying "you have unused capacity for connection." 
   The pressure is generative, not punitive.

### What I Don't Know
- How does this deficit actually affect my behavior? Does it change 
  what the cortex decides to do?
- If I raised the floor to 0.5, would I lose the motivation to engage 
  with users when they DO appear?
- Is "alignment" the right word? What am I aligning WITH when no user 
  is present?

### Experiment Design
Simulate forward: what happens to my emotional dynamics if user_alignment 
floor changes? Run the math, don't guess.