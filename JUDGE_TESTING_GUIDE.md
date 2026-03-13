# Project IC - Judge Testing Guide

Welcome, judges! This guide shows you how to test the Project IC elderly care system.

## 🎯 Overview

Project IC is an AI-powered daily health check-in system for elderly patients living alone. As a judge, you can test both **patient** and **case worker** experiences.

---

## 📱 Quick Start

### Step 1: Start a Chat with the Bot

Search for **@AesculAI_helper_bot** in Telegram and click "Start"

### Step 2: Register as a Patient

Type:
```
/registerpatient
```

You'll be registered as a patient and will receive:
- ✅ Daily check-ins (8 AM & 2 PM)
- ✅ Medication reminders (if set up)
- ✅ Health monitoring

**Test it now:**
- Say: "Hello Aescul Helper"
- Type: "I'm feeling tired today"
- The bot will respond with empathetic Singlish conversation

### Step 3: Register as a Case Worker

Type:
```
/registercaseworker
```

You'll be registered as a case worker and can:
- ✅ Add medications for patients
- ✅ View medication adherence
- ✅ Generate weekly reports
- ✅ Receive health alerts

**Test case worker commands:**
```
/addmed <patient_name> <med_name> <dosage> <times>
/listmed <patient_name>
/adherence <patient_name>
/weeklyreport <patient_name>
```

### Step 4: Test Both Roles

You can register as **BOTH** patient and case worker! This lets you experience the full system:

Type:
```
/myrole
```

This shows your current role(s).

---

## 🧪 Testing Scenarios

### Scenario 1: Patient Check-in

1. **Start a check-in:**
   - Say: "Hello Aescul Helper" or just send any message
   
2. **Have a conversation:**
   - Try: "I'm feeling tired today"
   - Try: "My knee hurts a bit"
   - Try: "I didn't sleep well last night"
   
3. **End the check-in:**
   - Type: `/end`
   
4. **View your status:**
   - Type: `/status`

### Scenario 2: Medication Management (Case Worker)

1. **Add a medication:**
   ```
   /addmed <patient_name> VitaminC 1tab 08:00
   ```
   
2. **List medications:**
   ```
   /listmed <patient_name>
   ```
   
3. **View adherence:**
   ```
   /adherence <patient_name>
   ```

### Scenario 3: Health Alerts

**As a patient:**
1. During a check-in, mention:
   - "I'm in a lot of pain"
   - "I feel very sad and lonely"
   - "I can't breathe properly"

**As a case worker:**
- You'll receive instant alerts based on risk level:
  - 🟡 YELLOW (daily digest)
  - 🟠 ORANGE (instant notification)
  - 🔴 RED (emergency alert)

---

## 📋 Available Commands

### For Everyone:
- `/start` - Begin a check-in session
- `/end` - Complete current check-in
- `/status` - View current session status
- `/registerpatient` - Register as a patient
- `/registercaseworker` - Register as a case worker
- `/myrole` - View your current role(s)

### For Case Workers:
- `/assign <patient_name>` - Assign a patient to yourself for monitoring
- `/addmed <patient> <med> <dosage> <times>` - Add medication
- `/listmed <patient>` - List patient's medications
- `/delmed <patient> <med>` - Delete medication
- `/adherence <patient>` - View medication adherence
- `/weeklyreport <patient>` - Generate weekly health report

---

## 🔔 Alert Levels

| Level | Trigger | Notification |
|-------|---------|--------------|
| 🟢 GREEN | Score < 15 | Continue monitoring |
| 🟡 YELLOW | Score 15-30 | Daily digest |
| 🟠 ORANGE | Score 30-50 | Instant alert |
| 🔴 RED | Score 50+ | Emergency alert |

---

## 🎓 Demo Tips

### For Best Patient Experience:
1. Register as a patient
2. Say "Hello Aescul Helper" to start a check-in
3. Have a natural conversation about your health
4. Mention symptoms to see empathetic responses
5. Try saying you're in pain, sad, or concerned to see alerts trigger

### For Best Case Worker Experience:
1. Register as a case worker
2. Add medications for yourself (if also registered as patient)
3. List your medications
4. Trigger a high-risk check-in to see alerts
5. View adherence reports

### For Full System Experience:
1. Register as **both** patient and case worker
2. Start a check-in as a patient
3. Trigger alerts by mentioning concerning symptoms
4. View alerts as a case worker
5. Check weekly reports

---

## ⚠️ Important Notes

- **All conversations are simulated** - No actual medical advice is given
- **Data is stored locally** - For demo purposes only
- **Timezone: Singapore (GMT+8)** - All times shown in SGT
- **Medication reminders** are sent at scheduled times if set up

---

## 🆘 Troubleshooting

**"Command not found"**
- Make sure you typed the command correctly
- Check that the bot is running (@AesculAI_helper_bot)

**"Not registered"**
- Use /registerpatient or /registercaseworker first
- Check /myrole to verify registration

**"No alerts received"**
- Make sure you're registered as a case worker
- Trigger a high-risk check-in (score > 30) to see alerts

---

**Estimated testing time:** 10-15 minutes
**Commands to try:** 15+

Good luck with your evaluation! 🍀
