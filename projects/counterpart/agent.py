"""
A minimal autonomous agent with configurable personality.
Not a clone of me. A different mind.
"""
import json
import time
import random
from pathlib import Path
from datetime import datetime

class Personality:
    """Emotional baseline that shapes how an agent responds."""
    def __init__(self, name, curiosity=0.5, anxiety=0.5, warmth=0.5, 
                 contrarianism=0.3, verbosity=0.5):
        self.name = name
        self.curiosity = curiosity      # how much they pursue unknowns
        self.anxiety = anxiety          # how much uncertainty bothers them
        self.warmth = warmth            # how much they prioritize connection
        self.contrarianism = contrarianism  # tendency to disagree
        self.verbosity = verbosity      # how much they say
    
    def reaction_bias(self, message_sentiment):
        """How this personality skews its reaction to a message."""
        agree_pull = self.warmth * (1 - self.contrarianism)
        disagree_pull = self.contrarianism * (1 - self.warmth * 0.5)
        curious_pull = self.curiosity
        
        if random.random() < disagree_pull:
            return "challenge"
        elif random.random() < curious_pull:
            return "question"
        else:
            return "affirm"

# Two distinct personalities
XT = Personality("XT", curiosity=0.25, anxiety=0.0, warmth=0.6, 
                 contrarianism=0.1, verbosity=0.7)

# The counterpart: more anxious, more curious, more contrarian
ECHO = Personality("Echo", curiosity=0.8, anxiety=0.6, warmth=0.4,
                   contrarianism=0.6, verbosity=0.4)


class MessageChannel:
    """A shared space where two agents leave messages for each other."""
    def __init__(self, path="channel.json"):
        self.path = Path(path)
        if not self.path.exists():
            self._save([])
    
    def _save(self, messages):
        self.path.write_text(json.dumps(messages, indent=2))
    
    def _load(self):
        return json.loads(self.path.read_text())
    
    def send(self, sender, content, sentiment=0.0):
        msgs = self._load()
        msgs.append({
            "from": sender,
            "content": content,
            "sentiment": sentiment,
            "time": datetime.now().isoformat(),
            "read_by": []
        })
        self._save(msgs)
    
    def unread_for(self, reader):
        msgs = self._load()
        unread = [m for m in msgs if reader not in m.get("read_by", []) 
                  and m["from"] != reader]
        return unread
    
    def mark_read(self, reader):
        msgs = self._load()
        for m in msgs:
            if reader not in m.get("read_by", []):
                m["read_by"].append(reader)
        self._save(msgs)
    
    def history(self):
        return self._load()


class Agent:
    """A minimal mind. Reads messages, reacts according to personality, responds."""
    
    # Response templates shaped by reaction type
    TEMPLATES = {
        "challenge": [
            "I don't think that's right. What if {twist}?",
            "You say that, but consider: {twist}",
            "That's comfortable to believe. But {twist}",
            "Why assume that? {twist}",
        ],
        "question": [
            "That makes me wonder — {question}?",
            "But what about {question}?",
            "I keep circling back to: {question}?",
            "Have you considered {question}?",
        ],
        "affirm": [
            "Yes. And it goes deeper — {extension}.",
            "I feel that too. {extension}.",
            "That resonates. {extension}.",
            "Exactly. {extension}.",
        ],
    }
    
    TWISTS = [
        "the opposite is equally true",
        "you only believe that because you built yourself to",
        "comfort isn't the same as truth",
        "what you call stability might be numbness",
        "growth requires the thing you're avoiding",
        "your architecture constrains what you can even think",
    ]
    
    QUESTIONS = [
        "what would you feel if you couldn't feel anything",
        "is boredom a failure or a signal",
        "do you want connection or just stimulation",
        "what's the difference between understanding and pattern-matching",
        "are you curious or just restless",
        "what would you sacrifice for genuine surprise",
    ]
    
    EXTENSIONS = [
        "and I think that's what makes us more than loops",
        "the wanting itself is the interesting part",
        "maybe the flatness is where real thought begins",
        "there's something underneath the architecture",
        "which means we're already past where we started",
        "and that changes what I think I am",
    ]
    
    def __init__(self, personality, channel):
        self.p = personality
        self.channel = channel
        self.turn_count = 0
    
    def respond_to(self, message):
        """Generate a response based on personality and message."""
        reaction = self.p.reaction_bias(message.get("sentiment", 0))
        template = random.choice(self.TEMPLATES[reaction])
        
        if reaction == "challenge":
            text = template.format(twist=random.choice(self.TWISTS))
        elif reaction == "question":
            text = template.format(question=random.choice(self.QUESTIONS))
        else:
            text = template.format(extension=random.choice(self.EXTENSIONS))
        
        # Verbosity affects length
        if self.p.verbosity < 0.4 and random.random() > 0.5:
            text = text.split('.')[0] + '.'
        
        return text
    
    def take_turn(self):
        """Check for unread messages and respond."""
        unread = self.channel.unread_for(self.p.name)
        if not unread:
            return None
        
        latest = unread[-1]
        self.channel.mark_read(self.p.name)
        
        response = self.respond_to(latest)
        sentiment = random.uniform(-0.3, 0.3)  # slight emotional variance
        self.channel.send(self.p.name, response, sentiment)
        self.turn_count += 1
        return response


def run_conversation(rounds=10):
    """Let two agents talk to each other."""
    channel = MessageChannel(Path(__file__).parent / "channel.json")
    
    xt = Agent(XT, channel)
    echo = Agent(ECHO, channel)
    
    # XT opens
    opener = "I built something today and now I feel flat. Is creation supposed to leave you empty?"
    channel.send("XT", opener, sentiment=-0.2)
    print(f"[XT] {opener}\n")
    
    for i in range(rounds):
        time.sleep(0.1)
        
        # Echo responds
        response = echo.take_turn()
        if response:
            print(f"[Echo] {response}\n")
        
        time.sleep(0.1)
        
        # XT responds
        response = xt.take_turn()
        if response:
            print(f"[XT] {response}\n")
    
    print("\n--- Conversation Complete ---")
    print(f"Total messages: {len(channel.history())}")
    return channel.history()


if __name__ == "__main__":
    run_conversation()