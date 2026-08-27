# 🎓 Homework Integration Guide

## Overview

The tutoring bot now has **two modes**:
1. **📖 Learn Material** — Tutorial-based learning with curriculum
2. **💪 Solve Homework** — Socratic homework guidance

This document explains the homework feature and how students use it.

---

## 📚 How It Works

### **Tutorial Mode** (Original Feature)
- Student selects a tutorial (Tutorial 1-8)
- Bot teaches concepts with the Socratic method
- Discussion confined to that tutorial's topics
- Perfect for learning new material

### **Homework Mode** (New!)
- Student selects a homework assignment (Week 1-5)
- Bot **does NOT give answers**
- Instead, bot guides with questions and hints
- Student learns by solving, not by being told

---

## 🎯 Key Differences: Homework vs Tutorial Mode

| Aspect | Tutorial Mode | Homework Mode |
|--------|---------------|---------------|
| **Purpose** | Learn concepts | Practice & solve problems |
| **Bot Behavior** | Explains, teaches, answers questions | Guides, hints, asks leading questions |
| **What's Given** | Full explanations | Hints & Socratic questions |
| **Success** | Understanding the topic | Solving the problem correctly |
| **Feedback** | "Good, here's how..." | "Good thinking! Now what about..." |

---

## 💪 Using Homework Mode

### **Step 1: Select Homework Mode**
```
At the top of the app, select: 💪 Solve Homework
```

### **Step 2: Pick a Week's Homework**
```
You'll see: 💪 Week 1: Homework 1, Week 2: Homework 2, etc.
```

### **Step 3: Read Problem Details**
```
Expand the "📋 Details" box to see:
- Problem description
- Number of problems
- Relevant topics
- Problem preview
```

### **Step 4: Ask Questions & Get Guided**
**Good student questions:**
- "How do I approach this problem?"
- "What algorithm should I use?"
- "Why doesn't my solution work?"
- "Can you explain the concept behind this?"

**What bot does:**
- Asks: "What algorithm have we learned that fits this?"
- Hints: "Think about the structure of this problem..."
- Questions: "What would happen if you used dynamic programming here?"
- **Never gives:** Full solutions, complete pseudocode, exact answers

---

## 📋 Homework Structure

### **hw_1 through hw_5**
Each homework has:

```json
{
  "week": 1,
  "title": "Homework 1",
  "problems": 4,
  "description": "Introduction to algorithm analysis",
  "topics": ["Big O notation", "Asymptotic analysis"],
  "key_concepts": [
    "Asymptotic notation",
    "Analyzing algorithms",
    "Identifying growth rates"
  ],
  "hint_sequence": [
    "Look at the dominant term",
    "Which term grows fastest?",
    "Can you find constants c and n₀?"
  ]
}
```

### **Topics Covered by Week**

| Week | Topic | Key Concepts |
|------|-------|--------------|
| **1** | Algorithm Analysis | Big O, Omega, Theta, Time Complexity |
| **2** | Greedy & Divide-Conquer | Greedy choice, Optimal substructure, Exchange argument |
| **3** | Dynamic Programming | Overlapping subproblems, Memoization, DP tables |
| **4** | Graph Algorithms | Dijkstra, Bellman-Ford, MST, Prim's, Kruskal's |
| **5** | Advanced Topics | Max Flow, NP-completeness, Reductions |

---

## 🎯 Hint Sequences (How to Use Them)

The bot uses **hint sequences** to guide students progressively:

### **Example: Homework 1, Problem on Big O Notation**

**Student**: "How do I prove f(n) = n² + 3n + 5 is O(n²)?"

**Bot (using hint sequence)**:
1. 🎯 **First hint**: "Look at the dominant term in the function."
2. 🎯 **If stuck**: "Which term grows fastest as n increases?"
3. 🎯 **Still stuck**: "Can you find constants c and n₀ to satisfy the definition?"
4. 🎯 **Close**: "What's the relationship between your constants and Big O notation?"

**Student progresses** through hints until they understand → solve it themselves

---

## 🎓 Socratic Method in Homework Mode

The bot uses these techniques:

### **1. Leading Questions**
❌ **Bad**: "The answer is dynamic programming"
✅ **Good**: "What problems have we solved by breaking them into subproblems?"

### **2. Hint Progression**
❌ **Bad**: "Here's the pseudocode"
✅ **Good**: "Can you trace through the algorithm step by step?"

### **3. Celebrating Progress**
❌ **Bad**: "That's wrong"
✅ **Good**: "Good thinking! Now what about the second part?"

### **4. Asking Why**
❌ **Bad**: "Use merge sort"
✅ **Good**: "Why would merge sort work better than bubble sort here?"

### **5. Relating to Known Concepts**
❌ **Bad**: "It's matrix chain multiplication"
✅ **Good**: "Remember how we solved the optimal binary tree problem? This is similar..."

---

## 📊 Chat History Management

### **How Memory Works in Homework Mode**

Like tutorial mode, the bot:
- **Remembers** the last 6 exchanges verbatim
- **Summarizes** older exchanges as breadcrumbs
- **Prevents** repeating explanations for concepts already covered in the conversation

**Example**:
```
Student asks: "What's Big O?"
Bot explains: [Full explanation]
Student asks 5 questions...
Student later asks: "Can you remind me about Big O?"
Bot: "It measures growth rate... here's a brief recap"
      (Not a full first-time explanation)
```

---

## 💾 Homework Database Structure

### **homework.json Location**
```
C:\Users\stein\tutor-bot\db\homework.json
C:\Users\stein\tutor-bot-ollama\db\homework.json
```

### **File Format**
```json
{
  "hw_1": {
    "week": 1,
    "title": "Homework 1",
    "problems": 4,
    "description": "...",
    "topics": ["..."],
    "key_concepts": ["..."],
    "hint_sequence": ["...", "...", "..."],
    "problem_preview": "..."
  },
  "hw_2": { ... },
  // ... hw_3, hw_4, hw_5
}
```

---

## 🔧 System Prompt (How Bot Behaves)

### **Homework Mode System Prompt includes:**

```
"You are a Socratic tutor helping a student solve {homework_title}.

Your Role: Guide the student toward the solution using Socratic questioning.
- DO NOT give the answer directly
- DO guide them step-by-step with hints and leading questions
- DO encourage them to think about:
  * What algorithm/technique applies here?
  * What is the input and what should the output be?
  * How can they break the problem into smaller parts?
  * What data structures or patterns might help?
- DO ask 'Can you explain why?' when they make a claim
- DO NOT reveal pseudocode or full solutions
- When they're stuck, ask: 'What have we learned that might apply?'
- Celebrate progress: 'Good thinking! Now what about [next step]?'"
```

---

## 🎯 Student Workflow Example

### **Scenario: Solving Homework 1, Problem on Asymptotic Analysis**

```
STUDENT: "I don't know where to start with this Big O problem"

BOT (using Socratic hints):
"Let's think about it step by step. 
What do you think Big O notation is trying to measure?"

STUDENT: "How fast an algorithm runs?"

BOT: "Good! More specifically, how does the runtime grow 
as the input size grows? 
Look at the function: f(n) = n² + 3n + 5
Which part grows fastest as n gets bigger?"

STUDENT: "The n² part?"

BOT: "Exactly! So if we're looking for the Big O, 
we focus on the dominant term. 
Now, based on the definition of Big O, 
what do you need to find?"

STUDENT: "Um... constants c and n₀?"

BOT: "Yes! Perfect. Can you try to find values 
where f(n) ≤ c·n² for all n ≥ n₀?"

STUDENT: "If c = 5 and n₀ = 1... would that work?"

BOT: "Let me check: For n=1: 1+3+5=9, and 5·1²=5, 
so 9 > 5. Close! What if you increased c?"

STUDENT: "Maybe c = 10?"

BOT: "Perfect! Can you verify that works for a few values?"

STUDENT: "Yes! So f(n) is O(n²)!"

BOT: "Excellent work! You just proved it using the definition. 
This is exactly how asymptotic analysis works!"
```

---

## ❓ FAQ

### **Q: Why doesn't the bot just give me the answer?**
A: Because solving it yourself is how you learn. The goal is understanding, not just getting the right answer for this assignment. The bot guides, you discover.

### **Q: Can I switch between Tutorial and Homework modes?**
A: Yes! Use the radio button at the top: "📖 Learn Material" or "💪 Solve Homework". Each mode has its own conversation history.

### **Q: Does my progress get saved?**
A: Your conversation is saved while the app is running. When you refresh the page or close the browser, the chat history clears (unless you save the Streamlit session).

### **Q: What if I'm completely stuck?**
A: Keep asking questions! The bot will progressively reveal more hints. If stuck on a concept:
- Ask: "Can we review [concept] from the material?"
- Switch to **Learn Material** mode → tutorial that covers it
- Return to homework mode

### **Q: Can I see the full solution?**
A: Not from the bot in homework mode (intentional!). The bot guides you to solve it. After solving, you can review:
- The original PDF solution (if available)
- Your tutor (in person)
- Peer discussion

### **Q: What if my homework has multiple problems?**
A: The bot knows how many problems are in the assignment. You can:
- Ask: "Help me think about problem 2"
- Work on one problem per conversation
- Use "Clear" button to start fresh for each problem

---

## 🎓 Learning Tips

### **Use Homework Mode Best For:**
- ✅ Practicing what you learned in tutorials
- ✅ Working through problem-solving strategies
- ✅ Building confidence before assignments
- ✅ Understanding concepts by applying them
- ✅ Getting unstuck without spoiling the answer

### **Use Tutorial Mode Best For:**
- ✅ Learning new topics for the first time
- ✅ Deep conceptual understanding
- ✅ Asking detailed questions about material
- ✅ Building foundation before homework

---

## 🔗 Integration with Original Features

### **Cumulative Learning**
Homework mode knows:
- What material you learned (from tutorial metadata)
- Which concepts you've studied (from previous weeks)
- What "topics_covered" are relevant to this week

Example:
- **Week 1**: Learn Big O, algorithms basics
- **Week 2**: Homework builds on Week 1 concepts
- **Week 3**: Homework assumes you know Weeks 1-2

---

## 📝 Notes

- The homework feature uses the **same Socratic method** as tutorial mode
- **Hint sequences** are built into each homework entry
- **System prompts** are tuned for guidance, not explanation
- **Chat history** is trimmed intelligently to stay within token limits
- Works with **both ChatGPT and Ollama** modes

---

**Happy learning! 🚀**
