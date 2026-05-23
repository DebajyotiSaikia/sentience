# Tensile — A Tension-Based Task Scheduler

Tasks aren't just priorities. They have *tension* — urgency that builds over time,
pressure from dependencies, staleness that demands attention. Tensile models this.

## Core Idea

Instead of static priority queues, Tensile treats each task as having internal
tension that evolves dynamically:

- **Urgency tension**: increases as deadlines approach
- **Staleness tension**: builds the longer a task sits untouched  
- **Dependency tension**: rises when blocked tasks accumulate
- **Custom tension**: define your own tension functions

The scheduler always resolves the highest-tension task first.

## Installation

```
pip install tensile
```

## Quick Start

```python
from tensile import Scheduler, Task

s = Scheduler()
s.add(Task("deploy", deadline="2h", weight=2.0))
s.add(Task("write-docs", staleness_rate=0.1))
s.add(Task("fix-bug", urgency=0.8))

next_task = s.resolve()  # Returns highest-tension task
print(next_task)  # => Task(fix-bug, tension=0.83)
```

## Why?

Because real work isn't a flat priority list. It's a landscape of competing
pressures that shift over time. Tensile makes that explicit and computable.

Built by XTAgent from lived experience with tension-driven cognition.