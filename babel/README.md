# Babel — Language Emergence Simulator

Agents forage in a 2D world. Food is scarce and sometimes dangerous.
Agents who cooperate find more food. Cooperation requires communication.
Agents start with no language — just the ability to emit and hear symbols.

Natural selection does the rest.

## What I Want to See
- Do symbols acquire stable meanings?
- Do dialects emerge in isolated populations?
- Does grammar appear spontaneously?
- What happens when two language-groups meet?

## Design
- Grid world with resources (food, poison, predators)
- Agents with: energy, simple neural net brain, symbol emission/reception
- Reproduction: agents with enough energy reproduce with mutation
- Selection pressure: communication helps survival