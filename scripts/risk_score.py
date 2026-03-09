#!/usr/bin/env python3
"""
Risk Score Calculator
Calculates aggregate risk scores from multiple analysis results.
"""

from typing import List, Dict
from dataclasses import dataclass
from datetime import datetime

@dataclass
class SessionRisk:
    session_id: str
    timestamp: datetime
    risk_score: int
    risk_level: str
    signals: Dict[str, int]

def calculate_trend(recent_sessions: List[SessionRisk]) -> str:
    """
    Calculate risk trend from recent sessions.
    Returns: 'improving', 'stable', 'declining'
    """
    if len(recent_sessions) < 2:
        return 'stable'
    
    scores = [s.risk_score for s in sorted(recent_sessions, key=lambda x: x.timestamp)]
    
    # Compare first half average to second half average
    mid = len(scores) // 2
    early_avg = sum(scores[:mid]) / mid if mid > 0 else scores[0]
    late_avg = sum(scores[mid:]) / (len(scores) - mid)
    
    diff = late_avg - early_avg
    
    if diff < -5:
        return 'improving'
    elif diff > 5:
        return 'declining'
    return 'stable'

def calculate_weekly_risk(sessions: List[SessionRisk]) -> Dict:
    """
    Calculate weekly risk summary.
    """
    if not sessions:
        return {
            "average_score": 0,
            "max_score": 0,
            "sessions_count": 0,
            "high_risk_count": 0,
            "trend": "stable",
        }
    
    scores = [s.risk_score for s in sessions]
    high_risk = [s for s in sessions if s.risk_level in ['ORANGE', 'RED']]
    
    return {
        "average_score": round(sum(scores) / len(scores), 1),
        "max_score": max(scores),
        "sessions_count": len(sessions),
        "high_risk_count": len(high_risk),
        "trend": calculate_trend(sessions),
    }

def should_escalate(current_score: int, trend: str, consecutive_high: int) -> bool:
    """
    Determine if patient should be escalated based on multiple factors.
    """
    if current_score >= 50:
        return True
    if consecutive_high >= 3:
        return True
    if trend == 'declining' and current_score >= 30:
        return True
    return False


if __name__ == "__main__":
    # Demo
    from datetime import timedelta
    
    sessions = [
        SessionRisk("1", datetime.now() - timedelta(days=6), 15, "YELLOW", {"pain": 1}),
        SessionRisk("2", datetime.now() - timedelta(days=5), 18, "YELLOW", {"pain": 2}),
        SessionRisk("3", datetime.now() - timedelta(days=4), 22, "YELLOW", {"pain": 2, "distress": 1}),
        SessionRisk("4", datetime.now() - timedelta(days=3), 25, "YELLOW", {"pain": 2, "distress": 1}),
        SessionRisk("5", datetime.now() - timedelta(days=2), 28, "YELLOW", {"pain": 3, "distress": 1}),
        SessionRisk("6", datetime.now() - timedelta(days=1), 32, "ORANGE", {"pain": 3, "distress": 2}),
    ]
    
    import json
    print("Weekly Summary:")
    print(json.dumps(calculate_weekly_risk(sessions), indent=2))
    print(f"\nTrend: {calculate_trend(sessions)}")
    print(f"Should escalate: {should_escalate(32, 'declining', 3)}")
