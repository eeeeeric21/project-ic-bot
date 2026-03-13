#!/usr/bin/env python3
"""
Quick setup script forRun this to register judges as patients or"""

import os
import sys
from pathlib import Path

# Add skill directory toskill_dir = Path(__file__).parent
sys.path.insert(0, str(skill_dir / "scripts"))

print("=" * 60)
print("🏥 PROJECT IC - Registration Commands Setup")
print("=" * 60)
print()
print("New commands added:")
print("  /registerpatient - Register as a patient for daily check-ins")
print("  /registercaseworker - Register as a case worker")
print("  /myrole - View your current role(s)")
print()
print("These commands allow judges to:")
print("  1. Test as a patient - receive check-ins,print("  2. Test as a case worker - manage medications")
print("  3. Test both roles simultaneously")
print()
print("=" * 60)
print("✅ Registration commands have been added to telegram_voice_bot.py")
print("=" * 60)
print()
print("Changes made:")
print("  • Added registerpatient_command()")
print("  • Added registercaseworker_command()")
print("  • Added myrole_command()")
print("  • Updated scheduler.py with case_workers support")
print("  • Added register_case_worker() method")
print("  • Added is_case_worker() method")
print("  • Added _save_case_workers() method")
print()
print("Next steps:")
print("  1. cd /Users/yuandongliu/clawd/skills/project-ic-checkin")
print("  2. python scripts/telegram_voice_bot.py")
print("  3. Test with judges!")
