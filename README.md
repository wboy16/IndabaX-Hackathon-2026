# 🌿 Omiti Advisory - AI Agent Backend for Namibian Rangeland & Livestock
**Deep Learning IndabaX Namibia 2026 Hackathon**

Omiti Advisory is a robust, modular Django RESTful API backend serving as the bridge between interactive user interfaces (web/mobile frontend) and a dataset/LLM pipeline. The backend turns complex rangeland, satellite, and weather data into practical, transparent grazing and livestock management guidance for Namibian farmers.

---

## 📌 IMPORTANT CONTRIBUTION REMINDER
> [!IMPORTANT]
> **GitHub Contributor Addition Required:**
> Please ensure you add **`naftalindeapo`** as a collaborator/contributor to your team's GitHub repository before submission!

---

## 📁 Project Architecture & File Hierarchy

The codebase adopts Django's official project layout while strictly isolating business services, AI agent tool calling, and API routing so ML teammates can refine prompts/models without breaking backend API contracts.

```
c:\Users\Mr. KMWB\Documents\IndabaX Hackathon 2026\
├── manage.py                     # Django CLI runner
├── rangeland_backend/            # Core Django Settings & Configuration
│   ├── settings.py               # Django app settings, CORS, DRF config
│   ├── urls.py                   # Root URL routing
│   ├── wsgi.py                   # WSGI application entry
│   └── asgi.py                   # ASGI application entry
│
├── advisory/                     # REST API App
│   ├── urls.py                   # API routes (/api/chat, /api/weather, /api/data, etc.)
│   ├── views.py                  # API ViewSets & endpoints
│   ├── serializers.py            # Input validation & schema definitions
│   └── tests.py                  # Django test suite
│
├── services/                     # Business Logic & External Data Integration
│   ├── weather.py                # Live Open-Meteo & NASA POWER API integration
│   └── dataset.py                # Rangeland CSV dataset loader & query engine
│
├── ai/                           # AI & LLM Agent Module (Shared with ML Teammate)
│   ├── agent.py                  # LLM Tool-calling runner (OpenAI / Fallback engine)
│   └── prompts.py                # Namibian agricultural system prompts & reasoning constraints
│
├── data/                         # Data Assets
│   └── namibia_rangeland_synthetic.csv  # 1,200 site records across all 14 Namibian regions
│
├── requirements.txt              # Dependency management
├── .env.example                  # Environment variables template
└── README.md                     # Technical guide for Frontend & ML engineers
```

---

## 🚀 Quick Start Guide (Local Setup)

### 1. Anaconda Environment Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd "IndabaX Hackathon 2026"

# Create and activate the conda environment
conda create -n rangeland_env python=3.12 -y
conda activate rangeland_env
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env .env
```
*(Optional: Add your `OPENAI_API_KEY` in `.env` for live OpenAI GPT tool-calling. If omitted, the backend automatically uses its built-in rule-based reasoning engine so all endpoints remain 100% functional).*

### 4. Run Database Migrations & Start Server
```bash
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

The API will be available locally at `http://127.0.0.1:8000/`.

---

## 🔌 API Endpoints Reference

### 1. Health Check
- **Endpoint:** `GET /api/health/`
- **Description:** Verifies API health and active components.

### 2. Conversational Advisor Agent (Main Endpoint)
- **Endpoint:** `POST /api/chat/`
- **Request Body:**
```json
{
  "query": "Is my camp in Omaheke overgrazed right now?",
  "region": "Omaheke",
  "land_tenure": "Commercial",
  "herd_size": 120,
  "farm_size_ha": 1000.0
}
```
- **Response Features:**
  - Invokes `query_rangeland_data` and `get_recent_weather` tools.
  - Explains all evidence (NDVI, biomass, recent 14-day rainfall) rather than returning an unexplained verdict.
  - Explicitly lists data limitations.

### 3. Live Weather Query
- **Endpoint:** `GET /api/weather/?region=Khomas` or `POST /api/weather/`
- **Description:** Fetches live 14-day rainfall, daily precipitation history, and current weather from Open-Meteo & NASA POWER.

### 4. Rangeland Dataset Query
- **Endpoint:** `GET /api/data/?region=Omaheke&land_tenure=Communal` or `POST /api/data/`
- **Description:** Queries vegetation cover, carrying capacity (ha/LSU), grass vs. bush biomass, and bush encroachment levels across 14 Namibian regions.

### 5. Speech-to-Text (STT Webhook / Endpoint)
- **Endpoint:** `POST /api/stt/`
- **Description:** Accepts audio files for English voice prompt transcription (OpenAI Whisper integration with mock fallback).

### 6. Text-to-Speech (TTS Webhook / Endpoint)
- **Endpoint:** `POST /api/tts/`
- **Description:** Synthesizes written advisory responses into spoken English audio.

---

## 🧪 Verification & Testing

Run the Django unit test suite:
```bash
python manage.py test
```

---

## 🤝 Team Workflow Instructions

### For Frontend Developers:
- Use `/api/chat/` for the main chat interface. Pass `query`, `region`, `herd_size`, and `farm_size_ha`.
- CORS is enabled by default (`CORS_ALLOW_ALL_ORIGINS = True`), so you can connect your React / Next.js / Vue / HTML frontend directly.

### For ML Engineers:
- Work directly in the `ai/` folder.
- Custom system prompts and reasoning rules live in `ai/prompts.py`.
- Custom tool definitions, LangChain setups, or local model endpoints live in `ai/agent.py`.
- To swap synthetic CSV data for the full Kaggle Namibian Rangeland dataset, update `DATASET_PATH` or modify `services/dataset.py`.
