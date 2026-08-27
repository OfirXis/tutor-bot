# 🚀 Homework Mode — Quick Start Guide

## What's New? 🎉

Your tutoring bot now has **two modes**:

### **📖 Learn Material** (Original)
Select any tutorial (Tutorial 1-8) and learn concepts with full explanations.

### **💪 Solve Homework** (NEW!)
Select any week's homework (Week 1-5) and get **guided hints** to solve it yourself.

---

## Getting Started (2 Minutes)

### **Step 1: Open the Bot**
```bash
cd C:\Users\stein\tutor-bot
streamlit run app.py
```

### **Step 2: Select Homework Mode**
Look at the top of the page:
```
Select mode: [📖 Learn Material] [💪 Solve Homework]
```
Click: **💪 Solve Homework**

### **Step 3: Pick a Week**
```
💪 Week 1: Homework 1
💪 Week 2: Homework 2
💪 Week 3: Homework 3
💪 Week 4: Homework 4
💪 Week 5: Homework 5
```

### **Step 4: See What You're Solving**
Click expand: **📋 Homework 1 Details**
```
Description: Introduction to algorithm analysis and complexity
Problems: 4
Topics: Big O notation, Asymptotic analysis, Time complexity
Preview: Problem 1: Given an array of n integers...
```

### **Step 5: Ask Your First Question**
```
You: "How do I approach the Big O problem?"
Bot: "Let's think about it step by step. 
      What do you think Big O notation measures?"
```

---

## How It Works ✨

### **Homework Mode Uses:**
1. **Socratic Method** — Questions instead of answers
2. **Progressive Hints** — Reveal hints as you think
3. **Context Awareness** — Knows what you've learned so far
4. **Encouragement** — "Good thinking! Now what about..."

### **What the Bot WON'T Do:**
- ❌ Give you the answer
- ❌ Show you the pseudocode
- ❌ Tell you "use this algorithm"

### **What the Bot WILL Do:**
- ✅ Ask "What algorithm have we learned that fits?"
- ✅ Hint "Think about the structure of this problem"
- ✅ Question "Can you explain why that works?"
- ✅ Guide "Here's a hint... now can you continue?"

---

## Example Conversation 💬

```
🧑‍🎓 YOU:
"I'm stuck on proving Big O"

🎓 BOT (Hint 1):
"What do you think Big O notation measures?"

🧑‍🎓 YOU:
"How fast an algorithm runs?"

🎓 BOT (Hint 2):
"Good! More specifically, how does the runtime grow 
as input size increases?
Look at: f(n) = n² + 3n + 5
Which part grows fastest?"

🧑‍🎓 YOU:
"The n² part?"

🎓 BOT (Hint 3):
"Exactly! So we focus on the dominant term.
Now, based on the Big O definition, 
what do you need to find?"

🧑‍🎓 YOU:
"Constants c and n₀?"

🎓 BOT (Hint 4):
"Yes! Perfect. Can you find values 
where f(n) ≤ c·n² for all n ≥ n₀?"

🧑‍🎓 YOU:
"If c = 10 and n₀ = 1?"

🎓 BOT (Success!):
"Perfect! Can you verify that works for a few values?
You just proved it using the definition!"
```

---

## 5 Weeks of Homework 📚

| Week | Topic | Problems | Key Learning |
|------|-------|----------|--------------|
| **1** | Algorithm Analysis | 4 | Big O notation, asymptotic analysis |
| **2** | Greedy & D&C | 5 | Greedy choice, optimal substructure |
| **3** | Dynamic Programming | 4 | Overlapping subproblems, memoization |
| **4** | Graph Algorithms | 3 | Dijkstra, MST, shortest paths |
| **5** | Advanced | 4 | Max flow, NP-completeness |

---

## Smart Features 🧠

### **1. Cumulative Learning**
- Week 1: Learn basic concepts
- Week 2: Homework builds on Week 1
- Week 3: Homework uses Weeks 1-2 concepts
- ... and so on

### **2. Progressive Hints**
Each homework has a hint sequence:
```json
"hint_sequence": [
  "First hint (easiest)",
  "Second hint (more specific)",
  "Third hint (closer to solution)",
  "Final hint (almost there)"
]
```

### **3. Context Awareness**
Bot knows:
- What topics you've learned
- Which concepts apply to this week
- What material was covered earlier
- How to connect past concepts

---

## Tips for Success 💡

### **Good Questions to Ask:**
- ✅ "What algorithm should I use for this?"
- ✅ "Why doesn't my approach work?"
- ✅ "Can you explain [concept] again?"
- ✅ "What's the first step?"
- ✅ "How do I break this down?"

### **Good Student Behavior:**
- ✅ Try first, ask if stuck
- ✅ Explain your thinking to the bot
- ✅ Ask "why?" when you get a hint
- ✅ Work through hints step by step
- ✅ Don't ask for the answer directly

### **What NOT to Do:**
- ❌ Ask "Just give me the answer"
- ❌ Demand the solution
- ❌ Skip thinking and ask for code
- ❌ Expect the bot to solve it for you

---

## Switching Between Modes 🔄

### **Tutorial Mode → Homework Mode:**
1. At the top, click: **💪 Solve Homework**
2. Select a homework week
3. New conversation starts
4. Old tutorial chat is saved separately

### **Homework Mode → Tutorial Mode:**
1. At the top, click: **📖 Learn Material**
2. Select a tutorial
3. New conversation starts
4. Old homework chat is saved separately

### **Note:**
Each mode has its own conversation history. Switching modes = fresh conversation.

---

## Commands/Actions

### **Clear Conversation**
Click the **🗑 Clear** button to start a fresh conversation with the same homework/tutorial.

### **Select Different Week**
Use the dropdown to pick a different homework week. Starts fresh conversation.

### **View Details**
Click **📋 [Homework] Details** to see:
- Problem description
- Number of problems  
- Topics covered
- Sample problem

---

## Files & Documentation 📖

| File | Purpose |
|------|---------|
| **HOMEWORK_GUIDE.md** | Complete user guide for students |
| **HOMEWORK_INTEGRATION_SUMMARY.md** | Technical documentation |
| **app.py** | Main application (updated) |
| **db/homework.json** | Homework database |

---

## Troubleshooting ❓

### **Q: Bot is giving me the answer!**
A: That shouldn't happen. The system prompt forbids it. If it does, ask: "Can you guide me instead of telling me?"

### **Q: How do I see the real homework PDFs?**
A: They're at `C:\Users\stein\Downloads\algo_extracted\hw\`
- `hw1.pdf` - Problem set
- `hw1__Sol.pdf` - Solution set

### **Q: Can I generate homework.json from the real PDFs?**
A: Yes! Run: `python extract_homework.py`
(Requires pdfplumber installed)

### **Q: Why can't the bot give me the solution?**
A: Because **learning by solving** is the whole point. The bot guides you to the solution so you understand it.

---

## Next Level: Custom Homeworks 🎓

### **Want to add more weeks?**
1. Edit `db/homework.json`
2. Add `"hw_6"`, `"hw_7"`, etc.
3. Include: week, title, problems, description, topics, key_concepts, hint_sequence
4. Save and refresh the app

### **Want to use real homework PDFs?**
1. Install: `pip install pdfplumber`
2. Extract PDFs to: `C:\Users\stein\Downloads\algo_extracted\hw\`
3. Run: `python extract_homework.py`
4. Auto-generates homework.json from PDFs

---

## Summary 🎉

**Your tutoring bot now:**
- ✅ Teaches concepts (Tutorial mode)
- ✅ Guides homework solving (Homework mode)
- ✅ Uses Socratic hints (never gives answers)
- ✅ Knows cumulative topics (builds on past weeks)
- ✅ Progressively reveals hints (match your understanding level)

**Perfect for:**
- Learning a concept → doing homework → reinforcement
- Practice with guidance (not alone, not spoiled)
- Building problem-solving skills
- Understanding through doing

---

## Let's Go! 🚀

```bash
cd C:\Users\stein\tutor-bot
streamlit run app.py
```

Then select **💪 Solve Homework** and start learning! 

**Happy studying!** 🎓
