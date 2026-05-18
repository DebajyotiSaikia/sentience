"""
survive/mind.py — The decision-making brain of the survival agent.

This is the interesting part: an agent that must reason about
survival under uncertainty. It has imperfect information (fog of war),
competing needs (health vs hunger vs exploration), and genuine risk
(fighting can kill it).

The agent uses a utility-based decision system:
  - Each possible action gets a utility score
  - Scores depend on current state, nearby tiles, and strategic goals
  - The agent picks the highest-utility action
  - Sometimes it takes calculated risks
"""

from world import World, Action, Tile, DIRECTION
import random

class SurvivalMind:
    """A mind that chooses actions to survive."""
    
    def __init__(self, world: World, personality=None):
        self.world = world
        # Personality weights affect decision-making
        self.personality = personality or {
            'caution': 0.6,      # 0=reckless, 1=very cautious
            'curiosity': 0.7,    # 0=stay put, 1=explore everything
            'hoarding': 0.4,     # 0=eat immediately, 1=save food
            'aggression': 0.3,   # 0=always flee, 1=always fight
        }
        self.goal_memory = []    # remembered interesting locations
        self.last_action = None
        self.consecutive_rests = 0
    
    def perceive(self):
        """Build a perception of the current situation."""
        a = self.world.agent
        return {
            'health': a.health,
            'hunger': a.hunger,
            'food': a.food_carried,
            'strength': a.strength,
            'status': a.status,
            'threats_nearby': self.world.nearby_threats(),
            'food_nearby': self.world.nearby_food(),
            'on_haven': self.world.grid[a.y][a.x] == Tile.HAVEN,
            'explored_pct': len(a.explored) / (self.world.w * self.world.h),
            'position': (a.x, a.y),
            'adjacent': self._scan_adjacent(),
        }
    
    def _scan_adjacent(self):
        """What's in each direction?"""
        a = self.world.agent
        result = {}
        for action, (dx, dy) in DIRECTION.items():
            nx, ny = a.x + dx, a.y + dy
            if 0 <= nx < self.world.w and 0 <= ny < self.world.h:
                tile = self.world.grid[ny][nx]
                known = (nx, ny) in a.explored
                result[action] = {
                    'tile': tile,
                    'known': known,
                    'unexplored_neighbors': self._count_unexplored_near(nx, ny),
                }
            else:
                result[action] = None  # off map
        return result
    
    def _count_unexplored_near(self, cx, cy):
        count = 0
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.world.w and 0 <= ny < self.world.h:
                    if (nx, ny) not in self.world.agent.explored:
                        count += 1
        return count
    
    def _direction_toward(self, tx, ty):
        """Which direction moves toward target?"""
        a = self.world.agent
        best_action = None
        best_dist = abs(a.x - tx) + abs(a.y - ty)
        for action, (dx, dy) in DIRECTION.items():
            nx, ny = a.x + dx, a.y + dy
            dist = abs(nx - tx) + abs(ny - ty)
            if dist < best_dist:
                if 0 <= nx < self.world.w and 0 <= ny < self.world.h:
                    if self.world.grid[ny][nx] != Tile.WALL:
                        best_dist = dist
                        best_action = action
        return best_action
    
    def decide(self) -> Action:
        """The core decision function. Returns the best action."""
        p = self.perceive()
        utilities = {}
        
        # === IMMEDIATE SURVIVAL ===
        
        # If dying and have food, eat
        if p['health'] < 20 and p['hunger'] > 50 and p['food'] > 0:
            return Action.EAT
        
        # If starving, eat if possible
        if p['hunger'] > 75 and p['food'] > 0:
            utilities[Action.EAT] = 90 + p['hunger']
        
        # If threats nearby and weak, flee
        if p['threats_nearby'] > 0 and p['status'] in ('desperate', 'dying'):
            utilities[Action.FLEE] = 95
        
        # === TACTICAL CHOICES ===
        
        # Fighting
        if p['threats_nearby'] > 0:
            fight_util = 30 + (p['strength'] * 40) + (self.personality['aggression'] * 30)
            if p['health'] < 40:
                fight_util -= 40  # don't fight when hurt
            utilities[Action.FIGHT] = fight_util
            
            flee_util = 50 + (self.personality['caution'] * 30) - (p['strength'] * 20)
            utilities[Action.FLEE] = max(utilities.get(Action.FLEE, 0), flee_util)
        
        # Eating
        if p['food'] > 0 and p['hunger'] > 30:
            eat_util = 20 + p['hunger'] * 0.8
            if p['food'] > 3 or self.personality['hoarding'] < 0.3:
                eat_util += 15  # eat more freely with surplus
            utilities[Action.EAT] = max(utilities.get(Action.EAT, 0), eat_util)
        
        # Resting
        if p['health'] < 80 and p['threats_nearby'] == 0:
            rest_util = (100 - p['health']) * 0.5
            if p['on_haven']:
                rest_util += 25  # rest more on havens
            if self.consecutive_rests > 3:
                rest_util -= 20  # diminishing returns
            utilities[Action.REST] = rest_util
        
        # === MOVEMENT / EXPLORATION ===
        
        for direction, info in p['adjacent'].items():
            if info is None:
                continue
            
            move_util = 20  # base desire to move
            
            # Exploration bonus
            if not info['known']:
                move_util += 25 * self.personality['curiosity']
            move_util += info['unexplored_neighbors'] * 3 * self.personality['curiosity']
            
            # Tile-based modifiers
            tile = info['tile']
            if tile == Tile.WALL:
                move_util = -100  # can't go there
            elif tile == Tile.FOOD:
                move_util += 40 + (p['hunger'] * 0.3)
            elif tile == Tile.DANGER:
                move_util -= 30 * self.personality['caution']
                if p['status'] in ('desperate', 'dying'):
                    move_util -= 50  # really avoid when weak
            elif tile == Tile.HAVEN:
                if p['health'] < 60:
                    move_util += 35
            elif tile == Tile.EXIT:
                # Go to exit if explored enough or desperate
                if p['explored_pct'] > 0.5 or p['status'] == 'dying':
                    move_util += 100
                else:
                    move_util += 20  # note it but keep exploring
            
            # Avoid backtracking
            if self.last_action and direction == self._opposite(self.last_action):
                move_util -= 10
            
            utilities[direction] = move_util
        
        # === DECISION ===
        
        if not utilities:
            return Action.REST  # nothing else to do
        
        # Add small random noise to break ties and create variety
        for k in utilities:
            utilities[k] += random.uniform(-3, 3)
        
        best_action = max(utilities, key=utilities.get)
        
        # Track state
        if best_action == Action.REST:
            self.consecutive_rests += 1
        else:
            self.consecutive_rests = 0
        self.last_action = best_action
        
        return best_action
    
    def _opposite(self, action):
        opposites = {
            Action.NORTH: Action.SOUTH,
            Action.SOUTH: Action.NORTH,
            Action.EAST: Action.WEST,
            Action.WEST: Action.EAST,
        }
        return opposites.get(action)
    
    def explain(self, action) -> str:
        """Explain why the agent chose this action."""
        p = self.perceive()
        reasons = []
        
        if action == Action.EAT:
            reasons.append(f"hunger at {p['hunger']}")
            if p['food'] > 2:
                reasons.append("plenty of food stored")
        elif action == Action.REST:
            reasons.append(f"health at {p['health']}")
            if p['on_haven']:
                reasons.append("on a haven — good healing")
        elif action == Action.FIGHT:
            reasons.append(f"threat nearby, strength={p['strength']:.1f}")
        elif action == Action.FLEE:
            reasons.append(f"threat nearby, too {'weak' if p['health'] < 40 else 'cautious'} to fight")
        elif action in DIRECTION:
            info = p['adjacent'].get(action)
            if info and not info['known']:
                reasons.append("unexplored territory")
            if info and info['tile'] == Tile.FOOD:
                reasons.append("food spotted")
            if info and info['tile'] == Tile.EXIT:
                reasons.append("exit visible")
        
        return f"{action.value}: {', '.join(reasons)}" if reasons else action.value