# Project AesculAI - Quick Reference Card

## 📱 Bot Information

**Bot Name:** AesculAI Helper Bot  
**Bot Username:** @AesculAI_helper_bot  
**Status:** ✅ Production Ready (100% Functional)

---

## 🚀 Quick Start (2 minutes)

### For Patients

```
1. Search @AesculAI_helper_bot in Telegram
2. Send: /registerpatient
3. Say: "Hello Aescul Helper"
4. Have a conversation!
```

### For Caregivers

```
1. Send: /registercaseworker
2. Send: /assign <patient_name>
3. Send: /listmed <patient_name>
4. Receive alerts automatically!
```

---

## 📋 Available Commands

### Everyone
- `/start` - Begin check-in
- `/end` - Complete check-in
- `/status` - View status
- `/registerpatient` - Register as patient
- `/registercaseworker` - Register as caregiver
- `/myrole` - View your roles

### Caregivers Only
- `/assign <patient>` - Assign patient to yourself
- `/addmed <patient> <med> <dosage> <time>` - Add medication
- `/listmed <patient>` - List medications
- `/delmed <patient> <med>` - Delete medication
- `/adherence <patient>` - View medication compliance
- `/weeklyreport <patient>` - Generate health report

---

## 🎯 Demo Scenarios

### Scenario 1: Normal Check-in
```
You: "Hello Aescul Helper"
Bot: "Hello! How are you feeling today?"
You: "I'm feeling okay, just a bit tired"
Bot: "Aiyo, tired ah? Did you sleep well last night?"
```

### Scenario 2: Trigger Alert
```
You: "I'm feeling very sad and lonely"
Bot: "I'm here with you, okay? 💙"
[Caregiver receives ORANGE alert]
```

### Scenario 3: Medication Reminder
```
Bot: "⏰ Time for your medicine:
     💊 Metformin (500mg)
     [✓ Taken] [⏭ Skip]"
You: [Tap ✓ Taken]
Bot: "Great! Keep it up! 💪"
```

---

## 🔔 Alert Levels

| Level | Score | Action |
|-------|-------|--------|
| 🟢 GREEN | 0-15 | Continue monitoring |
| 🟡 YELLOW | 15-30 | Daily digest |
| 🟠 ORANGE | 30-50 | Instant alert |
| 🔴 RED | 50+ | Emergency alert |

---

## 📊 Implementation Status

| Platform | Status | Completeness |
|----------|--------|--------------|
| Telegram Bot | ✅ Live | 100% |
| Web PWA | ⚠️ UI Only | 30% |
| Alexa Skill | 🚧 Designed | 40% |

---

## 🔗 Links

- **Bot:** https://t.me/AesculAI_helper_bot
- **Code:** https://github.com/eeeeeric21/project-ic-bot
- **Docs:** See README.md for full documentation

---

## 📞 Testing Tips

**Test Patient Experience:**
1. Register as patient
2. Say "Hello Aescul Helper"
3. Type "I'm feeling tired"
4. Type "My knee hurts"
5. Check /status

**Test Caregiver Experience:**
1. Register as caregiver
2. Assign yourself as patient
3. Add medication: `/addmed <your_name> VitaminC 1tab 08:00`
4. List medications: `/listmed <your_name>`
5. Trigger alert to see notification

**Test Alerts:**
1. Start new check-in
2. Type "I can't breathe properly" (RED alert)
3. Or type "I'm very sad and lonely" (ORANGE alert)
4. Check for notification on your phone

---

## 🎓 For Competition Judges

**What's Fully Working:**
- ✅ All Telegram bot commands
- ✅ MERaLiON AI conversations
- ✅ Medication reminders
- ✅ Health alerts
- ✅ Weekly reports
- ✅ Singapore timezone

**What's In Progress:**
- ⚠️ Web dashboard (UI only, not deployed)
- 🚧 Alexa skill (code ready, not deployed)

**Estimated Test Time:** 5-10 minutes

---

**Thank you for evaluating Project AesculAI!** 🙏

*Built with ❤️ for Singapore's elderly*
