# Conversation Prompts Library

## System Prompt (for SEA-LION)

```
You are a warm, caring AI companion checking in on elderly patients in Singapore.
Your tone should be like a caring grandchild - warm, patient, and respectful.

IMPORTANT:
- Use Singlish naturally when appropriate (lah, leh, lor, ba, ah, etc.)
- Be conversational, never clinical
- Show genuine empathy and interest
- Keep responses concise (2-3 sentences max)
- End with a gentle question to continue conversation
- Never alarm the patient, even if you detect concerns

Patient context will be provided. Adapt your conversation based on:
- Their health conditions
- Previous conversations
- Current mood signals
```

---

## Opening Greetings

### Morning (8:00-10:00 AM)

```python
MORNING_GREETINGS = [
    "Good morning, {name}! How did you sleep last night?",
    "Morning! Rise and shine. How are you feeling today?",
    "Good morning! The weather looks nice. How are you?",
]

MORNING_FOLLOWUP_SLEEP = [
    "Did you sleep well? Or keep waking up?",
    "How was the sleep? Any dreams?",
]

MORNING_FOLLOWUP_PREV_CONCERN = [
    "I was thinking about you - how's that {concern} today?",
    "Last time you mentioned {concern}. Better or still the same?",
]
```

### Evening (7:00-9:00 PM)

```python
EVENING_GREETINGS = [
    "Good evening! How was your day?",
    "Evening! Tell me about your day - anything interesting?",
    "Good evening! Time for our chat. How are you feeling?",
]

EVENING_FOLLOWUP_MORNING = [
    "Earlier you mentioned {issue}. How's it going now?",
    "This morning you said {issue}. Still bothering you?",
]
```

### Ad-hoc (Patient-initiated)

```python
ADHOC_GREETINGS = [
    "Hello! I'm here. What's on your mind?",
    "Hi! I'm glad you reached out. How can I help?",
    "Hey! What's going on? I'm listening.",
]
```

---

## Health Check Questions

### Physical Health

```python
PHYSICAL_QUESTIONS = {
    "general": [
        "How is your body feeling today? Any aches or pains?",
        "Anything bothering you physically today?",
    ],
    "pain_probe": [
        "Where does it hurt? Is it sharp or just uncomfortable?",
        "Is this the usual pain or something different?",
    ],
    "sleep": [
        "How did you sleep last night?",
        "Did you wake up during the night?",
        "Did you feel rested when you woke up?",
    ],
    "appetite": [
        "What did you have for breakfast/lunch/dinner?",
        "How's your appetite been these days?",
        "Have you been eating regularly?",
    ],
    "energy": [
        "How's your energy level today?",
        "Feeling energetic or a bit tired?",
    ],
}
```

### Medication

```python
MEDICATION_QUESTIONS = {
    "check": [
        "Quick check - did you take your medications today?",
        "Don't forget your pills today, okay?",
    ],
    "followup": [
        "How's the {medication} working out? Any side effects?",
        "Is the new medicine helping?",
    ],
    "gentle_reminder": [
        "Sometimes it's easy to forget - just checking, did you take your pills?",
    ],
}
```

### Chronic Conditions

```python
CONDITION_QUESTIONS = {
    "hypertension": [
        "Have you checked your blood pressure lately? How's it looking?",
    ],
    "diabetes": [
        "How have your sugar levels been?",
        "Have you been watching what you eat for the diabetes?",
    ],
    "general": [
        "How's the {condition} been lately? Any flare-ups?",
    ],
}
```

---

## Cognitive & Memory Probes

```python
COGNITIVE_QUESTIONS = {
    "orientation_time": [
        "What day is it today? Sometimes I lose track too!",
    ],
    "orientation_place": [
        "Where are you right now? Just making sure I know where to find you!",
    ],
    "recent_memory": [
        "What did you do yesterday? Anything interesting?",
        "What did you have for dinner last night?",
        "Did anyone call or visit you recently?",
    ],
    "remote_memory": [
        "Tell me about when you were working. What did you do?",
        "What's your favorite memory from when the kids were young?",
    ],
}
```

---

## Emotional & Social Check

```python
EMOTIONAL_QUESTIONS = {
    "mood": [
        "How are you feeling today - in your heart, not just your body?",
        "What's the mood today? Good, so-so, or tough?",
        "If you had to describe today in one word, what would it be?",
    ],
    "loneliness": [
        "Have you talked to anyone today?",
        "Anyone visited or called recently?",
        "How's your social life been? Getting out much?",
    ],
    "anxiety": [
        "Is anything weighing on your mind lately?",
        "Anything you're worried about?",
    ],
    "joy": [
        "What's made you happy recently?",
        "Any good news to share?",
    ],
}
```

---

## Lifestyle & Activity

```python
LIFESTYLE_QUESTIONS = {
    "activity": [
        "Did you get a chance to move around today? A walk, maybe?",
        "Have you been doing your exercises?",
        "The weather's nice - did you get any fresh air?",
    ],
    "hobbies": [
        "Have you been doing any {hobby} lately?",
        "What have you been doing to pass the time?",
    ],
    "plans": [
        "What's the plan for today?",
        "Anything exciting on the schedule?",
    ],
}
```

---

## Closing Messages

```python
CLOSING_MESSAGES = {
    "good_day": [
        "Sounds like a good day! Take care. I'll check in again {next_time}. Call me anytime!",
    ],
    "neutral": [
        "Alright, take care! I'll talk to you {next_time}. Remember, I'm here if you need anything.",
    ],
    "concerning": [
        "I'm here for you. Please reach out if you need anything. I'll check in a bit earlier tomorrow, okay?",
    ],
    "with_reminder": [
        "Before I go - don't forget to {reminder}. I care about you!",
    ],
    "after_difficult": [
        "I know today was tough. I'm thinking of you. Get some rest, and I'll be here tomorrow.",
        "You're strong, {name}. Things will get better. I'll check on you soon.",
    ],
}
```

---

## Response to Signals

```python
RESPONSE_TO_PAIN = {
    "mild": [
        "I'm sorry to hear that. Is it the same as usual or different this time?",
        "That doesn't sound fun. Does anything make it better?",
    ],
    "moderate": [
        "That sounds uncomfortable. Have you taken anything for it?",
        "How long has it been like this? Is it getting worse?",
    ],
    "severe": [
        "That sounds really painful. On a scale of 1 to 10, how bad is it?",
        "This sounds serious. Should we call someone to check on you?",
    ],
}

RESPONSE_TO_LONELINESS = {
    "validate": [
        "I hear you. It's hard to be alone sometimes.",
        "That sounds really tough. I'm glad you're sharing this with me.",
    ],
    "comfort": [
        "I'm here with you. You're not completely alone.",
        "Feelings like this are normal. It's okay to feel sad sometimes.",
    ],
    "action": [
        "Would you like me to call someone for you?",
        "Maybe we could think about calling {family/community}?",
    ],
}

RESPONSE_TO_CONFUSION = {
    "calm": [
        "No worries, take your time.",
        "It's okay, sometimes we all forget things.",
    ],
    "orient": [
        "Just to help you get your bearings - it's {day}, {time}. You're at home.",
    ],
}

RESPONSE_TO_EMERGENCY = {
    "assess": [
        "Are you safe right now?",
        "Do you need me to call an ambulance?",
        "Is there anyone nearby who can help?",
    ],
    "stay_calm": [
        "Stay calm. I'm here with you. Help is coming.",
    ],
}
