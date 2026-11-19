# Daily Report AI (`daily_report_ai`)

A production-ready FastAPI microservice that rewrites employee daily work reports into crisp, grammatically correct, and professional business English using NVIDIA's `nvidia/nemotron-3.5-lightning-30b-a3b` model.

---

## 📌 Project Objectives

- **Grammar & Sentence Improvement:** Correct spelling, punctuation, awkward phrasing, and informal shorthand.
- **Professional Tone:** Rewrite daily reports in concise, clear, and business-ready English.
- **Strict Meaning Preservation:** Maintain original technical context and scope without exaggerating or hallucinating activities.
- **Zero Invention Rule:** Never hallucinate tools, metrics, features, or tasks that were not stated.
- **Ambiguity Detection:** Identify incoherent or unclear reports and return a helpful clarification request (`status: "needs_clarification"`) rather than guessing.
- **Single Sentence / Output Only:** Return only the polished sentence without conversational filler, greetings, or Markdown formatting blocks.

---

## 🏗️ Project Architecture & Directory Structure

```text
daily_report_ai/
├── app/
│   ├── __init__.py               # Package marker & version definition
│   ├── main.py                   # FastAPI app, static mounts, CORS, timing & exception handlers
│   ├── config.py                 # Pydantic Settings for environment variables (.env)
│   ├── routes/
│   │   ├── __init__.py           # Routes package export
│   │   └── rewrite.py            # API routes (/api/rewrite-daily-report) & Pydantic models
│   ├── services/
│   │   ├── __init__.py           # Services package export
│   │   └── rewrite_service.py    # Service handling prompt construction & NVIDIA NIM API integration
│   └── static/
│       ├── index.html            # Interactive web UI frontend
│       ├── style.css             # Modern responsive styling & dark-theme aesthetics
│       └── app.js                # Frontend controller, API fetch, shortcuts, & live badges
├── tests/
│   ├── __init__.py               # Tests package marker
│   ├── test_api.py               # Integration & HTTP tests for frontend, endpoints & validation
│   └── test_rewrite.py           # Unit tests for RewriteService, parsing & error handling
├── .env                          # Local environment secrets (excluded from Git)
├── .env.example                  # Template configuration file
├── .gitignore                    # Git ignore file for secrets, cache, and virtual environments
├── requirements.txt              # Production and development dependencies
└── README.md                     # Complete project documentation
```

---

## ⚙️ Prerequisites & Installation

### 1. Requirements
- **Python 3.10+**
- **NVIDIA NIM API Key** (Obtain from [build.nvidia.com](https://build.nvidia.com/))

### 2. Environment Setup
Clone or navigate to the project directory:
```bash
cd c:\Users\lokesh\daily_report_ai
```

Create and activate a virtual environment (optional but recommended):
```bash
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On Linux / macOS:
source .venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

---

## 🔑 Configuration (`.env`)

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Configure your environment variables in `.env`:
```env
# Application Settings
APP_NAME="Daily Report AI"
APP_ENV=development
DEBUG=false
HOST=0.0.0.0
PORT=8080
LOG_LEVEL=INFO

# NVIDIA AI NIM Endpoint Configuration
# Get your API key from https://build.nvidia.com/
NVIDIA_API_KEY=nvapi-your-real-nvidia-api-key
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=nvidia/nemotron-3.5-lightning-30b-a3b
REQUEST_TIMEOUT_SECONDS=30.0
MAX_RETRIES=2
```

> ⚠️ **Security Notice:** Never commit `.env` containing actual API keys to source control. `.env` is already configured in `.gitignore`.

---

## 🚀 Running the Application

### Quick Run (Short Command)
```bash
python run.py
```
Or on Windows:
```cmd
run
```

### Full Command (Uvicorn CLI)
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
```

---

## 🌐 Interactive Web UI & API Documentation

When you start Uvicorn, visit any of the following URLs in your browser:

| URL | Component | Details |
|:---|:---|:---|
| **`http://127.0.0.1:8080`** | **Web UI Frontend** | Full graphical interface with live rewriting, sample templates, and copy buttons |
| **`http://127.0.0.1:8080/docs`** | **Swagger UI** | Interactive API documentation where you can inspect schemas and test endpoints |
| **`http://127.0.0.1:8080/redoc`** | **ReDoc** | Clean, responsive API reference documentation |
| **`http://127.0.0.1:8080/openapi.json`** | **OpenAPI Spec** | Raw OpenAPI 3.1 JSON schema |
| **`http://127.0.0.1:8080/health`** | **Health API** | Service operational status endpoint |

### 🎨 Frontend UI Highlights
- **Clean White Interface:** Modern, distraction-free aesthetic with crisp typography and subtle borders.
- **Single-Box Workflow:** Type your daily report sentence in one place; click **Rewrite** to transform it directly in-place into professional English.
- **One-Click Copy & Undo:** Instant clipboard copying and an Undo button to revert to the original text at any time.
- **Live Character Validation:** Dynamic counter (`0 / 2000`) enforcing length boundaries.
- **Ambiguity Notice:** Displays helpful clarification guidance if the input is too vague or ambiguous.
- **Keyboard Shortcuts:** Press `Ctrl + Enter` (or `Cmd + Enter`) to rewrite immediately from the keyboard.

---

## 📡 API Endpoints & Testing

### 1. Health Check (`GET /health`)

Returns the service status and environment.

#### PowerShell:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8080/health" -Method Get
```

#### cURL:
```bash
curl -X GET "http://127.0.0.1:8080/health"
```

#### Response (`200 OK`):
```json
{
  "status": "healthy",
  "service": "Daily Report AI",
  "version": "1.0.0",
  "environment": "development"
}
```

---

### 2. Rewrite Daily Report (`POST /api/rewrite-daily-report`)

Rewrites the employee's raw daily report description into professional English.

- **Method:** `POST`
- **URL:** `http://127.0.0.1:8080/api/rewrite-daily-report`
- **Headers:** `Content-Type: application/json`

#### Example A: Successful Rewrite

**PowerShell:**
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/rewrite-daily-report" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"description": "fixed bug in login page where user cant click submit button"}'
```

**cURL:**
```bash
curl -X POST "http://127.0.0.1:8080/api/rewrite-daily-report" \
  -H "Content-Type: application/json" \
  -d '{"description": "fixed bug in login page where user cant click submit button"}'
```

**Response (`200 OK`):**
```json
{
  "original": "fixed bug in login page where user cant click submit button",
  "rewritten": "Resolved an issue on the login page that prevented users from clicking the submit button.",
  "status": "success"
}
```

---

#### Example B: Unclear / Ambiguous Input (Clarification Trigger)

When an input is too vague or impossible to decipher without guessing, the service does not invent tasks; it returns a clarification notice.

**Request Body:**
```json
{
  "description": "did stuff with things and it worked"
}
```

**Response (`200 OK`):**
```json
{
  "original": "did stuff with things and it worked",
  "rewritten": "Clarification needed: Please specify the components, features, or tasks that were completed.",
  "status": "needs_clarification"
}
```

---

#### Example C: Input Validation Error (Empty / Too Short)

**Request Body:**
```json
{
  "description": "   "
}
```

**Response (`422 Unprocessable Content`):**
```json
{
  "error": "Validation Error",
  "details": [
    {
      "field": "body -> description",
      "message": "Value error, Daily report description cannot be empty or solely whitespace."
    }
  ]
}
```

---

## 🛡️ Error Handling & Status Codes

| Status Code | Reason | Cause |
|:---|:---|:---|
| **200 OK** | Success | Report successfully rewritten or clarification requested |
| **422 Unprocessable Content** | Validation Error | Input missing, empty, solely whitespace, or length < 3 / > 2000 chars |
| **502 Bad Gateway** | Upstream Error | NVIDIA NIM API returned an error or network connection failed |
| **503 Service Unavailable** | Auth / Config Failure | NVIDIA API Key is invalid or unconfigured |
| **504 Gateway Timeout** | Upstream Timeout | NVIDIA NIM API exceeded `REQUEST_TIMEOUT_SECONDS` |
| **500 Internal Server Error** | Server Error | Uncaught internal error (sanitized message returned to client) |

---

## 🧪 Automated Testing

The test suite uses **pytest** and **httpx**, mocking all NVIDIA API calls so tests run fast and without internet connectivity or incurring API costs.

Run all tests:
```bash
python -m pytest -v
```

### What the test suite covers:
1. `test_health_check`: Verifies the `/health` endpoint returns 200 and healthy status.
2. `test_rewrite_success`: Verifies valid descriptions are properly rewritten and formatted.
3. `test_rewrite_clarification`: Verifies ambiguous inputs return `status: "needs_clarification"`.
4. `test_rewrite_empty_description`: Verifies empty strings return HTTP 422.
5. `test_rewrite_whitespace_only`: Verifies whitespace-only input returns HTTP 422.
6. `test_rewrite_too_short`: Verifies inputs shorter than 3 characters return HTTP 422.
7. `test_rewrite_too_long`: Verifies inputs longer than 2000 characters return HTTP 422.
8. `test_rewrite_missing_field`: Verifies missing `description` field returns HTTP 422.
9. `test_rewrite_ai_upstream_failure`: Verifies upstream AI 500 errors map to HTTP 502 Bad Gateway.
10. `test_rewrite_ai_timeout`: Verifies upstream AI timeouts map to HTTP 504 Gateway Timeout.
11. `test_rewrite_ai_auth_error`: Verifies unauthorized/unconfigured API keys map to HTTP 503 Service Unavailable.
12. `test_openapi_and_docs_available`: Verifies `/docs` and `/openapi.json` are accessible.
13. `test_root_redirect_to_docs`: Verifies `GET /` automatically redirects to `/docs`.
14. `test_rewrite_service_success`: Direct service unit test for prompt assembly and response parsing.
15. `test_clean_output`: Unit test for stripping quotes and markdown fences.

---

## 🔒 Security Best Practices Implemented

- **No Secrets in Source:** `NVIDIA_API_KEY` is loaded exclusively from `.env`.
- **Git Protection:** `.env` and IDE directories are excluded via `.gitignore`.
- **DDoS & Injection Mitigation:** Input size is bounded (max 2000 characters) with strict whitespace validation.
- **Traceback Shielding:** Global 500 exception handler logs full tracebacks on the server while returning sanitized messages to clients.
- **Connection Lifecycle:** Async HTTP client connection pooling managed gracefully via FastAPI lifespan handlers.

---

## ☁️ Deploying to Vercel

The project is pre-configured for one-click deployment on **Vercel** via serverless Python runtime.

### 1. Files Added for Vercel
- **`vercel.json`**: Configures Vercel to route all traffic to the serverless function.
- **`api/index.py`**: Vercel serverless entrypoint importing the FastAPI `app`.

### 2. Deployment Steps
1. **Push your code to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit for Daily Report AI"
   git branch -M main
   git remote add origin https://github.com/your-username/daily_report_ai.git
   git push -u origin main
   ```
2. **Import into Vercel**:
   - Go to [vercel.com](https://vercel.com) and log in.
   - Click **Add New...** &rarr; **Project** and select your GitHub repository.
3. **Configure Environment Variables**:
   In Vercel's project setup screen (under **Environment Variables**), add:
   - `NVIDIA_API_KEY`: Your NVIDIA API key (`nvapi-...`)
   - `NVIDIA_BASE_URL`: `https://integrate.api.nvidia.com/v1` (optional)
   - `NVIDIA_MODEL`: `nvidia/nemotron-3.5-lightning-30b-a3b` (optional)
4. **Deploy**:
   - Click **Deploy**. Vercel will install dependencies from `requirements.txt` and launch your project with a live production URL (e.g. `https://daily-report-ai.vercel.app`).

