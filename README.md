# Loom 🧵

**AI-Powered Open-Source Contribution Platform**

[![Live Web Demo](https://img.shields.io/badge/Live_Demo-GitHub_Pages-208AEF?style=for-the-badge&logo=github)](https://shubham230523.github.io/Loom/)
👉 **Live Web Demo**: [https://shubham230523.github.io/Loom/](https://shubham230523.github.io/Loom/)

Loom is a full-stack platform designed to simplify open-source contributions. It combines a **React Native / Expo** cross-platform frontend with a **FastAPI multi-agent Python backend** to discover GitHub repositories, analyze codebases using vector search (`pgvector`), generate technical implementation plans, modify code in sandboxed environments, run tests, conduct autonomous code reviews, and create real GitHub Pull Requests.

---

## 📸 What is Loom?

Contributing to open source often requires searching for actionable issues, navigating large and unfamiliar codebases, configuring local environments, writing code, running tests, and creating Pull Requests.

Loom streamlines this process into a **human-in-the-loop AI contribution workflow**:

```text
Browse/Search Repository
           ↓
Discover Contribution Opportunities (Bugs, Features, Tests)
           ↓
AI Generates Technical Solution Plan
           ↓
👤 Developer Approves Plan
           ↓
AI Modifies Code in Workspace & Runs Verification Tests in Sandbox
           ↓
Autonomous Code Review & Diff Audit
           ↓
👤 Developer Approves Final Changes
           ↓
Real GitHub Branch Pushed & Pull Request Created
```

---

## 🛠 Tech Stack & Architecture

Loom consists of a mobile/web client, a FastAPI API server, background agents, vector database indexing, and Docker container sandboxing.

### 📱 Frontend (Client)
* **Framework**: React Native 0.86 + Expo 57 (Expo Router for file-based routing)
* **Web Support**: React Native Web (Static HTML/JS export deployed via GitHub Pages or Vercel)
* **Styling**: NativeWind v4 (Tailwind CSS)
* **State Management & Data Fetching**: Zustand + TanStack React Query v5
* **Networking**: Axios with automatic fallback mock adapter for static/offline web demos

### 🐍 Backend (API & Agent System)
* **Framework**: FastAPI (Python 3.10+) + Uvicorn
* **Database**: PostgreSQL 16 with `pgvector` extension (Vector search over codebase symbols & files)
* **ORM & Migrations**: Async SQLAlchemy 2.0 + Alembic
* **Cache & Messaging**: Redis (rate limiting, state management, WebSocket broadcasting)
* **Code Parsing & AST**: `tree-sitter` for multi-language symbol extraction
* **Sandboxing**: Docker Engine SDK (spawns isolated containers to compile code and run test suites)

### 🧠 Multi-Agent Architecture
Loom uses specialized AI agents coordinated through an AI Gateway layer:

* **Opportunity Agent (`opportunity_generator.py` / `issue_analyzer.py`)**: Scans GitHub issues, repository structure, and TODOs to identify actionable, well-scoped opportunities.
* **Solution Planner (`solution_planner.py`)**: Uses `pgvector` semantic search over repository symbols and files to generate a structured implementation blueprint (root cause, affected files, step-by-step plan, testing strategy).
* **Implementation Agent (`implementation.py`)**: Applies changes to files in isolated workspace directories based on the approved solution plan.
* **Test Agent (`test_agent.py`)**: Executes build and test commands inside Docker sandbox containers and captures stdout/stderr.
* **Debugger Agent (`debugger.py`)**: Analyzes test failures and feeds debugging context back into the implementation retry loop.
* **Code Reviewer Agent (`code_reviewer.py`)**: Conducts an independent code review, checks for security regressions, and assigns a readiness score (0–100).

### 🤖 Supported AI Providers
The AI Gateway layer routes prompts based on task type to providers including:
* **OpenRouter** (Cohere, Gemma, Nemotron, Claude, GPT-4o-mini)
* **Google Gemini**
* **Ollama** (Local models)
* **OpenAI** / **Anthropic**

---

## ⚙️ Configuration Options (Models, Testing, & Review)

Loom is highly configurable via environment variables in `backend/.env`.

### 🤖 AI Provider & Model Configuration

| Variable | Description | Default Value | Recommended Options / Alternatives |
| :--- | :--- | :--- | :--- |
| `AI_PROVIDER` | AI Provider used by the Gateway | `"openrouter"` | `gemini`, `openai`, `anthropic`, `ollama-cloud` |
| `DEFAULT_MODEL` | General fallback LLM model slug | `"gpt-4o"` | `"cohere/north-mini-code:free"` (Free on OpenRouter) |
| `AGENT_MODEL` | Default model for autonomous agent tasks | `"gpt-4o-mini"` | `"google/gemma-2-9b-it:free"` (Free on OpenRouter) |
| `ENABLE_AI_CACHE` | Cache AI response outputs | `True` | `False` |
| `AI_CACHE_TTL` | AI cache time to live in seconds | `86400` *(24 hours)* | Any integer |
| `MAX_DEBUG_RETRIES` | Max retries for implementation fix loops | `3` | Integer (e.g., `5`) |
| `MAX_REVIEW_CYCLES` | Max code review feedback iterations | `3` | Integer |

#### 🎯 Task-Specific Model Overrides (Optional)
Override models for specific agent tasks to optimize cost, speed, and reasoning:

| Task Override Variable | Task Description | Default Value | Recommended Free Override |
| :--- | :--- | :--- | :--- |
| `MODEL_REPO_ANALYSIS` | Repository structure & architecture summary | `None` *(falls back to DEFAULT_MODEL)* | `"nvidia/nemotron-3-ultra:free"` |
| `MODEL_ISSUE_ANALYSIS` | Issue parsing & opportunity generation | `None` | `"google/gemma-2-9b-it:free"` |
| `MODEL_PLANNING` | Solution Planner blueprint generation | `None` | `"cohere/north-mini-code:free"` |
| `MODEL_IMPLEMENTATION` | Code modification agent | `None` | `"cohere/north-mini-code:free"` |
| `MODEL_DEBUGGING` | Analyzing test output & generating fixes | `None` | `"cohere/north-mini-code:free"` |
| `MODEL_TESTING` | Test detection & test suite execution | `None` | `"google/gemma-2-9b-it:free"` |
| `MODEL_CODE_REVIEW` | Independent code audit & scoring | `None` | `"google/gemma-2-9b-it:free"` |
| `MODEL_PR_GENERATION` | Pull Request title & description generation | `None` | `"google/gemma-2-9b-it:free"` |

---

### 🧪 Sandbox & Testing Configuration

| Variable | Description | Default Value | Options / Details |
| :--- | :--- | :--- | :--- |
| `SANDBOX_IMAGE` | Docker container image for code execution | `"thyrlian/android-sdk:latest"` | Any valid Docker image (e.g., `python:3.11`, `node:20`) |
| `SANDBOX_TEST_LEVEL` | Test execution mode in workspace | `"none"` | `'full'` (runs tests), `'compilation_only'` (checks build), `'none'` (skip) |
| `SANDBOX_CPU_LIMIT` | Max CPU cores per sandbox container | `2.0` | Float (e.g., `1.0`, `4.0`) |
| `SANDBOX_MEMORY_LIMIT` | RAM allocation per sandbox container | `"2g"` | String (e.g., `"1g"`, `"4g"`) |
| `SANDBOX_DISK_LIMIT` | Disk space limit per sandbox container | `"2g"` | String |
| `SANDBOX_TIMEOUT` | Sandbox execution timeout in seconds | `1200` *(20 mins)* | Integer seconds |
| `SANDBOX_PIDS_LIMIT` | Process limit per sandbox container | `500` | Integer |
| `SANDBOX_NETWORK_MODE` | Sandbox container network isolation | `"none"` | `"none"` (disabled network), `"bridge"` |
| `LOCAL_GRADLE_CACHE_DIR`| Host directory mounted for Gradle cache | `~/.gradle` | File path |

---

### 🔍 Code Review & Automation Configuration

| Variable | Description | Default Value | Options |
| :--- | :--- | :--- | :--- |
| `ENABLE_CODE_REVIEW` | Enable autonomous Code Review Agent audit | `False` | `True` / `False` |
| `AUTO_PUSH_AND_PR` | Auto push branch & create PR upon success | `False` | `True` / `False` |
| `SECRET_DETECTION_PATTERNS` | Regex patterns to scan for leaked secrets | Default API key & private key patterns | List of regex strings |

---

## 🚀 Running Loom Locally (Full Stack)

To run the complete platform with live AI agents, local repository cloning, Docker sandboxing, and real GitHub PR creation:

### Prerequisites
* **Node.js**: v20+
* **Python**: 3.10+
* **Docker & Docker Desktop / Engine**: Active and running

---

### Step 1: Start PostgreSQL (`pgvector`) & Redis
In the root folder, run Docker Compose to start the database and cache:

```bash
docker compose up -d
```
* PostgreSQL running on `localhost:5432` (`loom` / `loom`)
* Redis running on `localhost:6379`

---

### Step 2: Configure & Start Backend (FastAPI)

1. Navigate to `backend/` and set up Python virtual environment:
   ```bash
   cd backend
   python -m venv venv

   # On Linux/macOS:
   source venv/bin/activate

   # On Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create `.env` file inside `backend/`:
   ```env
   APP_NAME="Loom API"
   ENVIRONMENT="development"
   DEBUG=true
   SECRET_KEY="dev-secret-key"
   ALLOWED_HOSTS=["*"]

   DATABASE_URL="postgresql+asyncpg://loom:loom@localhost:5432/loom"
   REDIS_URL="redis://localhost:6379/0"

   # GitHub OAuth Credentials (from GitHub Developer Settings)
   GITHUB_CLIENT_ID="your_github_client_id"
   GITHUB_CLIENT_SECRET="your_github_client_secret"
   GITHUB_REDIRECT_URI="http://localhost:8000/api/v1/auth/github/callback"

   # AI Provider Keys
   AI_PROVIDER="openrouter"
   OPENROUTER_API_KEY="sk-or-v1-..."
   # or GEMINI_API_KEY="..."

   DEFAULT_MODEL="cohere/north-mini-code:free"
   AGENT_MODEL="google/gemma-2-9b-it:free"
   ```

4. Run database migrations:
   ```bash
   alembic upgrade head
   ```

5. Start the API server:
   ```bash
   python ../run_server.py
   ```
   * FastAPI interactive documentation available at: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Step 3: Start Frontend (React Native / Expo Web)

In a new terminal window:

1. Install frontend dependencies:
   ```bash
   npm install
   ```

2. Start the Expo development server:
   ```bash
   # Run in Web Browser
   npm run web

   # Or run with Expo Go / Android Emulator
   npm run android
   ```
   * Access web client at: [http://localhost:8081](http://localhost:8081)

---

## 🌐 Live Web Demo (GitHub Pages)

Check out the live interactive web demo hosted directly on GitHub Pages:
🔗 **[https://shubham230523.github.io/Loom/](https://shubham230523.github.io/Loom/)**

* **Standalone Demo Mode**: When `apiClient` cannot reach a running backend server, it catches network errors and returns realistic mock data for auth, repo search, opportunity discovery, solution planning, activity streaming, and review diffs.
* **Automated CI/CD**: Pushing to `master` or `main` automatically builds and deploys the static web build to GitHub Pages via `.github/workflows/deploy-github-pages.yml`.

---

## 📁 Repository Structure

```text
Loom/
├── apps/               # React Native / Expo Mobile & Web App
│   └── src/
│       ├── app/        # Expo Router screens (Home, Discover, Repository, Plan, Activity, Review)
│       ├── components/ # Reusable UI components (Cards, Screens, Buttons, Inputs)
│       ├── services/   # API client, WebSocket listener, Auth & Repository services
│       ├── store/      # Zustand state stores (Auth, Settings)
│       └── types/      # TypeScript type definitions
│
├── backend/            # FastAPI Server & AI Agent System
│   ├── app/
│   │   ├── agents/     # Multi-Agent logic (Planner, Implementation, Test, Debugger, Reviewer)
│   │   ├── ai/         # AI Gateway, Providers (OpenRouter, Gemini, Ollama), Semantic Search
│   │   ├── api/        # REST endpoints (/v1/repositories, /v1/auth) & WebSockets (/ws)
│   │   ├── database/   # SQLAlchemy Models (User, Repository, Opportunity, Contribution, etc.)
│   │   ├── github/     # GitHub API service (OAuth, Clones, Branching, Pull Requests)
│   │   └── sandbox/    # Docker container runner & command execution policies
│   ├── migrations/     # Alembic database migrations
│   └── requirements.txt
│
├── docker-compose.yml  # PostgreSQL (pgvector) + Redis services
├── run_server.py       # FastAPI launcher script
└── README.md
```

---

## 🛡 Security & Design Principles

* **Human-in-the-Loop Control**: AI agents generate plans and code modifications, but developer approval is required before executing or creating GitHub Pull Requests.
* **Sandboxed Execution**: Code execution and test verification run inside isolated Docker containers without host network mounts.
* **Prompt Injection Defense**: Repository source code and issue descriptions are treated as untrusted input and wrapped in explicit system prompt delimiters.

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
