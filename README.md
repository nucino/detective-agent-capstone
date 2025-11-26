# 🕵️ Detective Agent Ed D. - Financial Investigation System (For educational purposes only, Not finantial advice!)

*"I've been investigating companies since before the dot-com bubble..." - Ed D.*

A multi-agent financial investigation system built with **Google ADK** (Agent Development Kit) using the **A2A protocol** for distributed agent communication.

## 📋 Project Overview

Detective Agent Ed D. is a grumpy but thorough financial detective with 40 years of experience. This capstone project demonstrates:

- **Multi-agent architecture** with specialized sub-agents
- **A2A (Agent-to-Agent) protocol** for remote agent communication
- **Google ADK** framework with Gemini 2.5-Flash model
- **Web interface** built with Gradio
- **Session persistence** with SQLite database with event compaction
- **Automatic retry logic** with exponential backoff
- **PDF report generation** with goog looking style or so I think!

## 🏗️ Architecture

### Components

1. **remote_agent.py** - A2A Server
   - Exposes Detective Agent via A2A protocol
   - Runs on port 8001
   - Contains three agents:
     - `Detective_Agent` (LlmAgent) - Coordinator with grumpy personality
     - `Agent_Search` - Google search specialist
     - `Agent_Code` - Python code execution specialist

2. **local_agent.py** - Gradio Web Client
   - Consumes remote agent via A2A protocol
   - Web interface on port 7860
   - Features:
     - Real-time progress tracking
     - Automatic investigation retry (up to 3 attempts)
     - PDF report generation with download button
     - Session management with DatabaseSessionService

### Multi-Agent Pattern

```
┌─────────────────────────────────────────┐
│       Detective Agent (Coordinator)      │
│         "Ed D." - LlmAgent              │
└─────────────┬───────────────────────────┘
              │
      ┌───────┴───────┐
      │               │
┌─────▼─────┐   ┌────▼──────┐
│   Search  │   │   Code    │
│   Agent   │   │   Agent   │
└───────────┘   └───────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.13
- Google API Key (for Gemini model)
- Conda or pip

### Installation

1. **Clone the repository:**
```bash
git clone <your-repo-url>
cd Capstone_proyect
```

2. **Create environment:**
```bash
conda env create -f environment_minimal.yaml
conda activate detective_agent
```

Or with pip:
```bash
pip install google-adk google-genai gradio python-dotenv reportlab aiohttp
```

3. **Create `.env` file:**
```bash
GOOGLE_API_KEY=your_google_api_key_here
DETECTIVE_SERVER_URL=http://localhost:8001
```

### Running the Application

1. **Start the A2A server:**
```bash
python remote_agent.py
```

2. **In a new terminal, start the web interface:**
```bash
python local_agent.py
```

3. **Open browser:**
```
http://localhost:7860
```

## 🎯 Features

### Investigation Process

1. **Company Query** - Enter company name (e.g., "Tesla", "Microsoft")
2. **Automated Research**:
   - Google search for company information
   - CEO profile and photo search
   - Financial data analysis with Python code execution
   - Red flags and green lights identification
3. **Report Generation** - Comprehensive markdown report
4. **PDF Export** - One-click download with professional formatting

### Retry Logic

The system automatically retries incomplete investigations:
- **Up to 3 attempts** with exponential backoff (2s, 4s, 8s)
- **Smart detection** of failures
- **Progress updates** during retries
- **Success rate**: ~99% by attempt 2

### Session Management

- **Persistent sessions** stored in SQLite database
- **Event compaction** for efficiency (interval=3, overlap=1)
- **Session isolation** per investigation

## 📊 Sample Investigation Report

Detective Ed D. generates reports with the following sections:

- **Company Overview** - Basic information and business model
- **CEO Profile** - Leadership background and photo
- **Financial Health** - Revenue, profitability, growth trends
- **🟢 Green Lights** - Positive indicators
- **🔴 Red Flags** - Warning signs
- **Ed's Bottom Line** - Grumpy but honest assessment

## 🔧 Configuration

### Model Settings

The system uses Gemini 2.5-Flash with retry configuration:
```python
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)
```

### A2A Server

- **Port**: 8001 (configurable via environment)
- **Protocol**: A2A (Agent-to-Agent)
- **Endpoint**: `http://localhost:8001/.well_known/agent-card`

### Database

- **Type**: SQLite
- **Location**: `detective_web_sessions.db`
- **Purpose**: Session persistence and event compaction

## 📁 Project Structure

```
Capstone_proyect/
├── remote_agent.py          # A2A server with multi-agent system
├── local_agent.py           # Gradio web interface client
├── environment_minimal.yaml # Conda environment specification
├── .env                     # Environment variables (create this)
├── README.md               # This file
└── detective_sketch.png    # Optional: Detective image for PDFs
```

## 🛠️ Technical Stack

- **Framework**: Google ADK (Agent Development Kit)
- **LLM**: Gemini 2.5-Flash via Google GenAI API
- **Tools**: Google Search, BuiltInCodeExecutor
- **Protocol**: A2A (Agent-to-Agent)
- **UI**: Gradio 6.0.0
- **Database**: SQLite with SQLAlchemy
- **PDF**: ReportLab
- **Language**: Python 3.13

## Pleas check sample screenshots of generated reports as well as screenshots for sample companies also in the gallery of the project

## 👨‍💻 Author Nucino (Felipe Rodriguez)

Built as part of the Google ADK 5-Day Intensive Course (December 2025)

---

*"Listen, kid. Building agents isn't just about the code. It's about persistence, proper error handling, and knowing when to call in backup agents. That's what separates good systems from great ones. Now get to work."* - Detective Ed D. 🕵️
