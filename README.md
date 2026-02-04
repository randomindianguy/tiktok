# 🎤 Confidence Coach — Practice Mode

**AI-powered coaching for first-time TikTok creators who freeze mid-recording.**

Built for TikTok AI PM OA | [Demo Script](#demo-script) | [Setup](#setup)

---

## 🎯 The Problem

**95% of TikTok users never post.** They scroll, like, comment — but don't create.

The blocker isn't motivation. People *want* to post. It's **ability** — in the moment of freeze, they literally don't know what to say next.

---

## 👤 Target Segment

Using the **Segmentation Framework** (Fixed + Behavior + Mindset):

| Dimension | Definition |
|-----------|------------|
| **Fixed (Who)** | TikTok users, 0-1K followers, age 18-35 |
| **Behavior (What)** | Watch >30 min/day, save sounds/ideas, start recordings but delete them |
| **Mindset (Why)** | Want to express themselves, fear judgment, don't know what to say next |

**Core Insight:** High motivation, low ability at the critical moment.

---

## 💡 The Solution

**Confidence Coach** detects when you freeze (pauses >3 seconds) and generates context-aware prompts to help you continue.

### How It Works

1. **Record** a practice video (30-60 seconds)
2. **Analyze** with AI (Whisper transcription + pause detection)
3. **Get prompts** specific to what you were saying

### Example

You say: *"So I've been thinking about what makes content go viral on TikTok. I think the biggest thing is..."*

*[4 second pause]*

AI Prompt: **"What's one viral TikTok you've seen that proves your point?"**

That's not generic encouragement. It read your context and gave you a specific direction.

---

## 🔄 Growth Loops

### 1. Confidence Flywheel (Reinforcing Loop)
```
Practice with Coach → Prompt helps → Complete video → Post →
Get engagement → Confidence increases → More attempts →
Graduate to power creator
```

### 2. Content Quality Loop
```
Coach helps completion → Videos are more coherent →
Algorithm rewards watch-time → More views →
More followers → Higher motivation
```

### 3. Social Proof Loop
```
First-time creator posts → "Finally posted my first TikTok!" →
Friends ask how → Word-of-mouth → More first-time creators
```

### 4. Data Flywheel
```
More users → More prompt/completion data →
ML improves prompt quality → Higher completion rate →
More users trust Coach
```

---

## 🧠 B=MAT Framework Application

| Component | Application |
|-----------|-------------|
| **Motivation** | Hope (I can become a creator) + Fear (missing out, friends are posting) |
| **Ability** | Coach reduces mental effort — prompt tells you what to say |
| **Trigger** | The pause itself triggers the prompt (facilitator) |

---

## 📊 Metrics

| Metric | Definition | Why |
|--------|------------|-----|
| **FaT** | First prompt acted upon in first session | Activation signal |
| **NaT** | 3+ videos completed in first week | Habit formation |
| **NSM** | First-time creator posts per week | Ties to TikTok's mission |
| **Goal** | 2x completion rate for first-time creators | Success metric |

---

## 🏗️ Technical Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Record    │────▶│   Whisper   │────▶│   Pause     │
│   Audio     │     │   API       │     │   Detection │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                                               ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Display   │◀────│   GPT-4     │◀────│   Context   │
│   Results   │     │   Prompts   │     │   Extract   │
└─────────────┘     └─────────────┘     └─────────────┘
```

### Stack
- **Frontend:** HTML/CSS/JS (TikTok-inspired dark theme)
- **Backend:** Python Flask
- **AI:** OpenAI Whisper (transcription) + GPT-4 (prompts)

### Why Practice Mode First?
Real-time coaching needs streaming audio, sub-second latency, interrupt handling — weeks of engineering.

Practice Mode validates the core hypothesis: **Do context-aware prompts actually help creators continue?**

If they don't act on prompts in Practice Mode, they won't act on them in real-time either.

---

## 🔒 Privacy Design

| Principle | Implementation |
|-----------|----------------|
| Minimal data | Only send audio for analysis |
| Encrypted transit | HTTPS to Whisper API |
| Immediate deletion | Audio deleted after processing |
| Nothing stored | No recordings saved |
| Clear indicator | Visual status when processing |

---

## 🚀 Setup

### Prerequisites
- Python 3.8+
- Node.js (optional, for serving frontend)
- OpenAI API key

### Backend Setup

```bash
cd backend

# Create virtual environment (optional)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and add your OpenAI API key

# Run server
python app.py
```

Server runs at `http://localhost:5001`

### Frontend Setup

```bash
cd frontend

# Option 1: Python simple server
python -m http.server 3000

# Option 2: Node.js
npx serve -p 3000

# Option 3: Just open index.html in browser
```

Open `http://localhost:3000`

---

## 🛣️ Roadmap

| Phase | Feature | Status |
|-------|---------|--------|
| **Now** | Practice Mode (post-recording analysis) | ✅ Built |
| **Next** | Real-time coaching (prompts during recording) | Planned |
| **Later** | Niche finder (watch history → content ideas) | Concept |
| **Later** | Camera presence feedback | Concept |
| **Later** | Content structure suggestions | Concept |

---

## 📁 Project Structure

```
confidence-coach/
├── backend/
│   ├── app.py              # Flask API server
│   ├── requirements.txt    # Python dependencies
│   ├── .env.example        # API key template
│   └── .env                # Your API key (not committed)
├── frontend/
│   ├── index.html          # Main HTML
│   ├── style.css           # TikTok-inspired styles
│   └── app.js              # Recording + API logic
└── README.md               # This file
```

---

## 🔗 TikTok Strategic Alignment

| TikTok Goal | How Confidence Coach Helps |
|-------------|---------------------------|
| Democratize creation | Makes creation accessible beyond confident 5% |
| More creators = more content | Converts passive viewers to active creators |
| Better content quality | Completed videos > abandoned recordings |
| Creator retention | Success → confidence → more attempts |

**Team Fit:** Social & Creation — turning passive consumers into active creators.

---

Built for TikTok AI PM Internship OA
