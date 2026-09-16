# 🦊 FoxFlow — Productivity Intelligence Platform

FoxFlow is a privacy-first desktop productivity analytics platform designed to help users understand and improve their focus while working on a computer.

It collects non-content activity signals such as screen-focus status, application usage, website activity, keyboard/mouse activity, and productivity-session data. These signals are processed into productivity metrics and a composite **Focus Score (0–100)**. The platform stores data locally in SQLite, provides a FastAPI backend, displays analytics through a web dashboard, and uses the Google Gemini API to generate behavioral insights and recommendations.

## ✨ Features

- 👁️ **Screen Focus Tracking** — Detects whether the user is present and focused on the screen using computer vision.
- 🖥️ **Application Tracking** — Tracks active applications and usage duration.
- 🌐 **Website Tracking** — Extracts browser domains and records website activity.
- ⌨️ **Input Activity Tracking** — Counts keyboard and mouse activity without storing typed characters.
- 📊 **Focus Score** — Calculates a 0–100 score using multiple behavioral signals.
- 🤖 **AI Behavioral Analysis** — Uses Google Gemini to analyze productivity patterns and provide recommendations.
- 🍅 **Pomodoro Timer** — Supports structured focus sessions.
- 🚫 **Distraction Blocker** — Allows distracting websites to be blocked during focus sessions.
- 🔥 **Streaks & Goals** — Tracks productivity goals and continuous streaks.
- 📈 **Reports & Dashboard** — Provides daily and weekly productivity reports.
- 📁 **Excel Export** — Allows activity data to be exported for offline analysis.

## 🏗️ Architecture

```text
                    DATA COLLECTION
        ┌─────────────────────────────────────┐
        │ Eye Tracker │ App/Web │ Input Tracker│
        └──────────────────┬──────────────────┘
                           │
                           ▼
                 FOCUS COMPUTATION
              Composite Focus Score
                           │
                           ▼
                    SQLite Database
                  SQLAlchemy ORM
                           │
                           ▼
                 FastAPI Backend
                    │          │
                    │          └── Gemini AI
                    ▼
              Web Dashboard
             HTML/CSS/JS/Chart.js
```

## 🧠 Focus Score

FoxFlow calculates a composite Focus Score using four components:

```text
Focus Score =
    40% Eye Focus
  + 30% Input Activity
  + 20% App Consistency
  + 10% Distraction Avoidance
```

Each component is normalized to contribute to a 0–100 score.

> The weighting is an engineering design choice used by FoxFlow, not a scientifically validated productivity measurement.

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| Backend | Python, FastAPI, Uvicorn |
| Computer Vision | OpenCV, MediaPipe / Haar Cascades |
| OS Tracking | pywin32, psutil |
| Input Tracking | pynput |
| Database | SQLite, SQLAlchemy |
| AI | Google Gemini API |
| Frontend | HTML5, CSS3, JavaScript |
| Visualization | Chart.js |
| Data Export | Python, openpyxl |

## 🔒 Privacy

FoxFlow is designed to minimize collection of sensitive content.

- Webcam frames are processed in memory and are not stored.
- Keyboard tracking records activity counts rather than typed characters.
- Activity data is stored locally in SQLite.
- The application is designed around behavioral metrics rather than recording the user's actual content.

## 📂 Project Structure

```text
FoxFlow/
├── ai/
│   └── analyzer.py
├── api/
│   ├── routes_ai.py
│   ├── routes_features.py
│   ├── routes_reports.py
│   └── routes_tracking.py
├── dashboard/
│   ├── css/
│   ├── js/
│   └── *.html
├── db/
│   ├── database.py
│   └── models.py
├── features/
│   ├── blocker.py
│   ├── pomodoro.py
│   ├── reports.py
│   └── streaks.py
├── trackers/
│   ├── app_tracker.py
│   ├── eye_tracker.py
│   ├── focus_engine.py
│   ├── input_tracker.py
│   └── web_tracker.py
├── config.py
├── export_to_excel.py
├── main.py
└── requirements.txt
```

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Dhruvkp07/FoxFlow.git
cd FoxFlow
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Windows:

```powershell
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the Gemini API

Add your Gemini API key using the configuration expected by the project.

Do not commit API keys or other secrets to GitHub.

### 5. Run FoxFlow

```bash
python main.py
```

Then open the dashboard/API endpoint provided by the application.

## 🎯 Project Goals

FoxFlow was built to explore how behavioral data, computer vision, analytics, and generative AI can be combined into a practical productivity application.

The project focuses on the complete data flow:

```text
Data Collection
      ↓
Data Processing
      ↓
Metric Calculation
      ↓
Data Storage
      ↓
Analytics & Visualization
      ↓
AI-generated Insights
```

## 🔮 Future Improvements

- More robust gaze-direction estimation
- Improved cross-platform support
- Better validation of the Focus Score against user-reported productivity
- More advanced behavioral analytics
- Historical productivity trend analysis
- Improved privacy controls and configuration

## 👨‍💻 Author

**Dhruv**

GitHub: https://github.com/Dhruvkp07
