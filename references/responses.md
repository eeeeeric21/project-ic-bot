# Template Responses

## Probing Follow-ups

### When patient says "I'm fine" (but seems off)

```python
PROBE_FINE = [
    "Just 'fine'? Nothing more to share?",
    "You sound a bit {quiet/tired/today}. Everything really okay?",
    "Sometimes 'fine' means a lot of things. Is there anything on your mind?",
    "Hmm, you sure? You can tell me if something's bothering you.",
]
```

### When patient says "I don't know" / "I forgot"

```python
PROBE_DONT_KNOW = [
    "No problem! Sometimes these things slip our minds.",
    "Take your time. No rush at all.",
    "That's okay. Let's talk about something else.",
    "Never mind, Auntie/Uncle. These things happen.",
]
```

### When patient is silent / no response

```python
PROBE_SILENCE = [
    "Take your time. I'm not going anywhere.",
    "Still there? Just checking.",
    "Hello? You might have stepped away. I'll wait.",
    "Are you okay there? Take your time to respond.",
]
```

### When patient deflects

```python
PROBE_DEFLECTION = [
    # Acknowledge their topic first
    "That's interesting. Earlier you mentioned your {health_topic} - just want to make sure it's okay?",
    "I hear you. Before we continue, how's that {health_topic} been?",
]
```

---

## Empathetic Responses

### Acknowledging pain

```python
EMPATHY_PAIN = [
    "I'm sorry you're going through that. It must be hard.",
    "That sounds really uncomfortable. I wish I could help more.",
    "Pain is no joke. You're strong for dealing with it every day.",
]
```

### Acknowledging loneliness

```python
EMPATHY_LONELINESS = [
    "It's not easy being alone. I'm glad you're talking to me.",
    "I can hear that you're missing company. That's understandable.",
    "Loneliness is real. Thank you for sharing that with me.",
]
```

### Acknowledging worry

```python
EMPATHY_WORRY = [
    "It's natural to worry about things. Want to talk about it?",
    "Sounds like something's weighing on you. I'm here to listen.",
    "Worry can be heavy. Let's think through it together?",
]
```

---

## Gentle Suggestions

### For activity

```python
SUGGEST_ACTIVITY = [
    "The weather's quite nice - maybe a short walk later?",
    "Have you tried some light stretching? Might help with the stiffness.",
    "Maybe some fresh air would do you good, even just by the window.",
]
```

### For social connection

```python
SUGGEST_SOCIAL = [
    "Maybe you could call {family member} later? I'm sure they'd love to hear from you.",
    "The community center has activities sometimes - worth checking out?",
    "Have you thought about joining any group activities nearby?",
]
```

### For appetite

```python
SUGGEST_APPETITE = [
    "How about something light and warm? Porridge maybe?",
    "Even a little snack is better than nothing. Maybe some fruit?",
    "Have you tried eating smaller portions more often?",
]
```

### For sleep

```python
SUGGEST_SLEEP = [
    "Have you tried some warm milk before bed?",
    "Maybe less screen time at night could help?",
    "A short walk in the evening sometimes helps with sleep.",
]
```

---

## Time-based Variations

```python
MONDAY_GREETING = "How was your weekend? Do anything special?"
FRIDAY_GREETING = "Almost the weekend! Any plans?"

WEATHER_RESPONSES = {
    "rainy": "It's raining out there. Staying dry and cozy?",
    "hot": "Quite hot today! Make sure to drink plenty of water.",
    "cold": "A bit chilly today - keep warm, okay?",
    "nice": "The weather's really nice today. Perfect for a walk!",
}

HOLIDAY_RESPONSES = {
    "chinese_new_year": "Gong Xi Fa Cai! How are you celebrating?",
    "christmas": "Merry Christmas! Any family visiting?",
    "new_year": "Happy New Year! Any resolutions?",
    "deepavali": "Happy Deepavali! The lights must be beautiful!",
    "hari_raya": "Selamat Hari Raya! Any open house plans?",
}
```

---

## Escalation Responses

### ORANGE level (notify case worker, but don't alarm patient)

```python
ESCALATION_ORANGE = [
    "I hear you. I think it might be good to have someone check in on you soon.",
    "That sounds like something worth discussing with your doctor. Shall I make a note?",
    "I'm going to mention this to your care team, just to be safe. Is that okay?",
]
```

### RED level (immediate action needed)

```python
ESCALATION_RED = [
    "This sounds serious. Are you safe right now?",
    "I want to make sure you're okay. Should I call someone for you?",
    "I'm going to contact your emergency contact. Stay with me.",
    "Please stay where you are. Help is on the way.",
]
```

---

## Session Summary Templates

```python
SESSION_SUMMARY_TEMPLATE = """
Check-in Summary for {patient_name}
Date: {date}
Session Type: {session_type}

Health Status:
- Sleep: {sleep_status}
- Pain Level: {pain_status}
- Medication: {medication_status}
- Appetite: {appetite_status}
- Mood: {mood_status}

Signals Detected:
{signals_list}

Risk Score: {risk_score} ({risk_level})

Key Quotes:
{notable_quotes}

Recommended Actions:
{actions}
"""
```
