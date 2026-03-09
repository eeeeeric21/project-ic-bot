# Detection Keywords

## Pain Signals (Weight: 5)

```python
PAIN_KEYWORDS = [
    # English
    "pain", "hurt", "ache", "aching", "sore", "stiff", "uncomfortable",
    "painful", "discomfort", "throbbing", "sharp", "dull", "cramp",
    "spasm", "tender", "swollen", "inflammation",
    
    # Singlish/Local
    "sakit", "ngilu", "pedih", "sengal",
    
    # Common expressions
    "can't move", "hard to walk", "hard to sleep", "bothering me",
]
```

## Cognitive Signals (Weight: 3)

```python
COGNITIVE_KEYWORDS = [
    # Memory issues
    "forget", "forgot", "forgotten", "can't remember", "don't remember",
    "memory", "slipped my mind",
    
    # Confusion
    "confused", "confusing", "don't understand", "not sure",
    "lost", "don't know where",
    
    # Disorientation
    "what day", "what time", "where am i", "how did i get here",
    
    # Word finding (observe, don't trigger)
    "the thing", "you know", "what do you call it",
]
```

## Distress Signals (Weight: 4)

```python
DISTRESS_KEYWORDS = [
    # Sadness
    "sad", "unhappy", "depressed", "down", "blue", "low",
    "crying", "tears", "weepy",
    
    # Loneliness
    "lonely", "alone", "nobody", "no one", "isolated",
    "miss", "missed", "wish someone",
    
    # Anxiety
    "scared", "afraid", "worried", "anxious", "nervous",
    "panic", "stress", "stressed",
    
    # Hopelessness
    "hopeless", "pointless", "meaningless", "give up",
    "can't go on", "tired of living",
    
    # Singlish expressions
    "sian", "bo liao", "damn sad",
]
```

## Red Flags (Instant Escalation: +50)

```python
RED_FLAG_KEYWORDS = [
    # Medical emergencies
    "can't breathe", "difficulty breathing", "shortness of breath",
    "chest pain", "heart attack", "stroke",
    "severe bleeding", "coughing blood", "vomiting blood",
    
    # Falls/injury
    "fell down", "i fell", "can't get up", "fallen",
    "broken", "fracture",
    
    # Self-harm indicators
    "want to die", "kill myself", "end it all", "suicide",
    "hurt myself", "not worth living",
    
    # Immediate danger
    "emergency", "help me now", "dying",
    "unconscious", "passed out", "blackout",
]
```

## Positive Signals (Weight: -2, reduces risk)

```python
POSITIVE_KEYWORDS = [
    # General positive
    "good", "great", "fine", "well", "better", "excellent",
    "happy", "glad", "pleased", "content",
    
    # Energy/activity
    "energetic", "active", "walking", "exercising", "out and about",
    
    # Social
    "visited", "visiting", "family came", "friends", "talking to",
    "going out", "meeting",
    
    # Singlish positive
    "shiok", "steady", "song", "ho seh",
]
```

## Medication Keywords (for adherence tracking)

```python
MEDICATION_KEYWORDS_POSITIVE = [
    "took my medicine", "took my pills", "medication taken",
    "already took", "just took", "took it",
]

MEDICATION_KEYWORDS_NEGATIVE = [
    "forgot to take", "didn't take", "haven't taken",
    "skipped", "missed dose",
]
```

## Appetite Keywords

```python
APPETITE_KEYWORDS_GOOD = [
    "ate already", "had breakfast", "had lunch", "had dinner",
    "hungry", "appetite good",
]

APPETITE_KEYWORDS_POOR = [
    "no appetite", "not hungry", "can't eat", "don't feel like eating",
    "only ate a little", "just drank water",
]
```

## Sleep Keywords

```python
SLEEP_KEYWORDS_GOOD = [
    "slept well", "good sleep", "slept through the night",
    "rested", "feel fresh",
]

SLEEP_KEYWORDS_POOR = [
    "couldn't sleep", "insomnia", "woke up many times",
    "tossed and turned", "restless", "bad sleep",
    "nightmare", "bad dream",
]
