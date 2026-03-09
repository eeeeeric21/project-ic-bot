#!/usr/bin/env python3
"""
Signal Detection Engine for Daily Check-in
Analyzes patient responses for health signals and risk indicators.
"""

import re
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

class RiskLevel(Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    ORANGE = "ORANGE"
    RED = "RED"

@dataclass
class AnalysisResult:
    signals: Dict[str, int]
    risk_score: int
    risk_level: RiskLevel
    red_flags: List[str]
    sentiment: float
    detected_categories: List[str]

# Keyword definitions
PAIN_KEYWORDS = [
    "pain", "hurt", "ache", "aching", "sore", "stiff", "uncomfortable",
    "painful", "discomfort", "throbbing", "sharp", "dull", "cramp",
    "sakit", "ngilu", "pedih", "sengal",
    "can't move", "hard to walk", "hard to sleep", "bothering me",
]

COGNITIVE_KEYWORDS = [
    "forget", "forgot", "forgotten", "can't remember", "don't remember",
    "memory", "confused", "confusing", "don't understand", "not sure",
    "lost", "don't know where", "what day", "what time", "where am i",
]

DISTRESS_KEYWORDS = [
    "sad", "unhappy", "depressed", "down", "blue", "low",
    "crying", "tears", "lonely", "alone", "nobody", "no one",
    "scared", "afraid", "worried", "anxious", "nervous",
    "hopeless", "pointless", "sian", "bo liao",
]

RED_FLAG_KEYWORDS = [
    "can't breathe", "difficulty breathing", "chest pain", "heart attack",
    "fell down", "i fell", "can't get up", "fallen", "broken", "fracture",
    "want to die", "kill myself", "end it all", "suicide", "hurt myself",
    "emergency", "help me now", "dying", "passed out", "unconscious",
]

POSITIVE_KEYWORDS = [
    "good", "great", "fine", "well", "better", "excellent",
    "happy", "glad", "pleased", "energetic", "active", "rested",
    "shiok", "steady", "ho seh",
]

MEDICATION_POSITIVE = [
    "took my medicine", "took my pills", "medication taken",
    "already took", "just took", "took it",
]

MEDICATION_NEGATIVE = [
    "forgot to take", "didn't take", "haven't taken", "skipped", "missed dose",
]

# Weights
WEIGHTS = {
    "pain": 5,
    "cognitive": 3,
    "distress": 4,
    "positive": -2,
    "red_flag": 50,
}

def count_matches(text: str, keywords: List[str]) -> int:
    """Count keyword matches in text."""
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw in text_lower)

def find_red_flags(text: str) -> List[str]:
    """Find red flag keywords in text."""
    text_lower = text.lower()
    return [flag for flag in RED_FLAG_KEYWORDS if flag in text_lower]

def analyze_sentiment(text: str) -> float:
    """
    Simple sentiment analysis.
    Returns float between -1 (negative) and 1 (positive).
    """
    positive_count = count_matches(text, POSITIVE_KEYWORDS)
    negative_count = (
        count_matches(text, PAIN_KEYWORDS) +
        count_matches(text, DISTRESS_KEYWORDS) * 1.5
    )
    
    total = positive_count + negative_count
    if total == 0:
        return 0.0
    
    sentiment = (positive_count - negative_count) / total
    return max(-1.0, min(1.0, sentiment))

def calculate_risk_level(score: int, has_red_flags: bool) -> RiskLevel:
    """Determine risk level from score."""
    if has_red_flags or score >= 50:
        return RiskLevel.RED
    elif score >= 30:
        return RiskLevel.ORANGE
    elif score >= 15:
        return RiskLevel.YELLOW
    return RiskLevel.GREEN

def analyze_response(text: str) -> AnalysisResult:
    """
    Main analysis function.
    Takes patient response text, returns analysis result.
    """
    # Count signals
    pain_count = count_matches(text, PAIN_KEYWORDS)
    cognitive_count = count_matches(text, COGNITIVE_KEYWORDS)
    distress_count = count_matches(text, DISTRESS_KEYWORDS)
    positive_count = count_matches(text, POSITIVE_KEYWORDS)
    
    # Check for red flags
    red_flags = find_red_flags(text)
    
    # Calculate risk score
    risk_score = 0
    risk_score += pain_count * WEIGHTS["pain"]
    risk_score += cognitive_count * WEIGHTS["cognitive"]
    risk_score += distress_count * WEIGHTS["distress"]
    risk_score += positive_count * WEIGHTS["positive"]
    
    if red_flags:
        risk_score += WEIGHTS["red_flag"]
    
    risk_score = max(0, min(100, risk_score))
    
    # Determine risk level
    risk_level = calculate_risk_level(risk_score, len(red_flags) > 0)
    
    # Analyze sentiment
    sentiment = analyze_sentiment(text)
    
    # Build detected categories
    detected = []
    if pain_count > 0:
        detected.append("pain")
    if cognitive_count > 0:
        detected.append("cognitive")
    if distress_count > 0:
        detected.append("distress")
    if positive_count > positive_count:
        detected.append("positive")
    
    return AnalysisResult(
        signals={
            "pain": pain_count,
            "cognitive": cognitive_count,
            "distress": distress_count,
            "positive": positive_count,
            "medication_positive": count_matches(text, MEDICATION_POSITIVE),
            "medication_negative": count_matches(text, MEDICATION_NEGATIVE),
        },
        risk_score=risk_score,
        risk_level=risk_level,
        red_flags=red_flags,
        sentiment=sentiment,
        detected_categories=detected,
    )

def analyze_response_json(text: str) -> dict:
    """Return analysis as JSON-serializable dict."""
    result = analyze_response(text)
    return {
        "signals": result.signals,
        "risk_score": result.risk_score,
        "risk_level": result.risk_level.value,
        "red_flags": result.red_flags,
        "sentiment": result.sentiment,
        "detected_categories": result.detected_categories,
    }


if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python analyze.py \"patient response text\"")
        sys.exit(1)
    
    text = " ".join(sys.argv[1:])
    result = analyze_response_json(text)
    print(json.dumps(result, indent=2))
