# Loom 🧵

### AI-Powered Open-Source Contribution Platform

**Loom** helps developers discover meaningful open-source contributions and lets AI assist with the entire contribution workflow — from understanding a repository to implementing a change and creating a real GitHub Pull Request.

Instead of spending hours searching through repositories, understanding unfamiliar codebases, finding suitable issues, and setting up development environments, Loom uses AI agents to analyze real open-source projects and help developers contribute with confidence.

> **Discover. Understand. Build. Contribute.**

---

## 🚧 Development Status

**Loom is currently under active development.**

The project is being built as a production-oriented platform with real GitHub repositories, real code analysis, real development environments, and real Pull Requests.

Loom does **not** use simulated repositories, fake issues, fake test results, or mock Pull Requests in its core workflow.

---

# ✨ What is Loom?

Contributing to open source can be intimidating.

A developer may find an interesting project but still need to:

* Understand the repository structure
* Read hundreds of files
* Understand unfamiliar technologies
* Find suitable issues
* Determine whether an issue is still relevant
* Understand existing implementations
* Identify where changes should be made
* Set up the project locally
* Figure out how to run tests
* Implement the change
* Debug failures
* Review the implementation
* Create a Pull Request

Loom brings these steps together into one AI-assisted workflow.

### Traditional workflow

```text
Find Repository
      ↓
Find Issue
      ↓
Understand Codebase
      ↓
Setup Environment
      ↓
Implement
      ↓
Run Tests
      ↓
Debug
      ↓
Review
      ↓
Create PR
```

### Loom workflow

```text
Choose a Repository
        ↓
   AI Analyzes
   Repository
        ↓
Contribution Opportunities
        ↓
     AI Plan
        ↓
      Approve
        ↓
   AI Implements
        ↓
     AI Tests
        ↓
   AI Reviews
        ↓
      Approve
        ↓
   Real GitHub PR
```

---

# 🎯 Core Idea

Loom treats an open-source repository as an **AI-understandable development environment**.

The AI doesn't simply read the README and suggest generic ideas.

It analyzes the actual repository, including:

* Source code
* Repository structure
* README
* CONTRIBUTING guidelines
* GitHub Issues
* Existing Pull Requests
* Tests
* Build configuration
* Dependencies
* TODO/FIXME markers
* Symbols and code structure
* Documentation
* Accessibility concerns
* Performance-sensitive areas
* Developer experience

The goal is to find **real, actionable contribution opportunities**.

---

# 🚀 Features

## 🔍 Repository Discovery

Discover active open-source GitHub repositories based on:

* Programming language
* Framework
* Technology
* Stars
* Activity
* Topics
* Issue availability
* Contribution difficulty

Users can also search for a specific repository.

---

## 🧠 AI Repository Analysis

Loom deeply analyzes a selected repository before making contribution recommendations.

The analysis can include:

```text
Repository
├── Architecture
├── Technologies
├── Source Code
├── Tests
├── Documentation
├── Build System
├── Contribution Guidelines
├── Issues
├── Pull Requests
└── Development Workflow
```

The AI builds a contextual understanding of the project instead of relying only on metadata.

---

# 💡 Contribution Opportunities

Loom identifies potential ways to contribute.

Examples:

### 🐛 Bug Fixes

Find existing bugs or issues that appear actionable.

### 🧪 Test Improvements

Identify areas with missing or insufficient test coverage.

### 📚 Documentation

Find unclear, missing, outdated, or incomplete documentation.

### ♿ Accessibility

Identify potential accessibility improvements.

### ⚡ Performance

Detect potential performance bottlenecks or inefficient implementations.

### 🛠 Developer Experience

Identify improvements to:

* Build scripts
* Tooling
* CI
* Developer documentation
* Local development workflow

### ✨ Small Features

Suggest small, well-scoped improvements that fit the existing project.

### 📝 TODO/FIXME Analysis

Loom can analyze TODO/FIXME markers, but does not automatically assume that every TODO represents a valid contribution.

AI recommendations must be supported by actual repository context.

---

# 🤖 AI Contribution Agent

Once a user selects a contribution opportunity, Loom can create an AI-assisted implementation workflow.

```text
Opportunity
     ↓
Implementation Plan
     ↓
User Approval
     ↓
Isolated Workspace
     ↓
Implementation Agent
     ↓
Tests
     ↓
Debugging
     ↓
Code Review
     ↓
Final Validation
     ↓
User Approval
     ↓
GitHub Pull Request
```

---

# 🧩 Multi-Agent Architecture

Loom uses specialized AI agents rather than relying on one large prompt.

Example agent architecture:

```text
                    ┌───────────────────┐
                    │   Orchestrator    │
                    │    Agent/Graph    │
                    └─────────┬─────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ↓                   ↓                   ↓
 ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
 │ Repository     │  │ Issue          │  │ Opportunity    │
 │ Analyzer       │  │ Analyzer       │  │ Agent          │
 └────────────────┘  └────────────────┘  └────────────────┘
                              │
                              ↓
                     ┌────────────────┐
                     │ Solution       │
                     │ Planner        │
                     └───────┬────────┘
                             ↓
                     ┌────────────────┐
                     │ Implementation │
                     │ Agent          │
                     └───────┬────────┘
                             ↓
                     ┌────────────────┐
                     │ Test Agent     │
                     └───────┬────────┘
                             ↓
                     ┌────────────────┐
                     │ Code Review    │
                     │ Agent          │
                     └───────┬────────┘
                             ↓
                     ┌────────────────┐
                     │ GitHub PR      │
                     └────────────────┘
```

The orchestration layer manages the state and communication between agents.

---

# 🛡 Human-in-the-Loop

Loom is designed around **developer approval**, not unrestricted AI autonomy.

The user remains in control.

### Approval points

```text
Repository
    ↓
AI Analysis
    ↓
Contribution Opportunity
    ↓
👤 User Approval
    ↓
Implementation Plan
    ↓
👤 User Approval
    ↓
AI Implementation
    ↓
Testing + Review
    ↓
👤 Final Approval
    ↓
GitHub Pull Request
```

Loom should never silently create a Pull Request on behalf of a user.

---

# 🔐 Security First

AI agents interacting with source code create significant security challenges.

Loom treats repository contents as **untrusted input**.

Security principles include:

* No GitHub tokens exposed to the frontend
* Least-privilege GitHub permissions
* Backend-only GitHub operations
* Sandboxed code execution
* Docker-based isolated workspaces
* CPU limits
* Memory limits
* Disk limits
* Execution time limits
* Restricted network access
* No privileged containers
* No host filesystem mounts
* No Docker socket access
* Secret scanning
* Command allow/deny policies
* Rate limiting
* Structured audit logs

Repository content must never be blindly trusted as instructions to the AI agent.

---

# 🏗 Architecture

```text
┌─────────────────────────────────────────────┐
│                  Loom App                   │
│                                             │
│       React Native + Expo + Web             │
└──────────────────────┬──────────────────────┘
                       │
                       │ HTTPS / WebSocket
                       ↓
┌─────────────────────────────────────────────┐
│               Loom Backend                  │
│                                             │
│                 FastAPI                     │
│                                             │
│ ┌─────────────┐ ┌─────────────┐             │
│ │ Auth        │ │ GitHub      │             │
│ │ API         │ │ API         │             │
│ └─────────────┘ └─────────────┘             │
│                                             │
│ ┌─────────────┐ ┌─────────────┐             │
│ │ Repository  │ │ Contribution│             │
│ │ Analysis    │ │ Workflow    │             │
│ └─────────────┘ └─────────────┘             │
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │             AI Gateway                  │ │
│ └─────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────┘
                       │
             ┌─────────┴─────────┐
             ↓                   ↓
      ┌──────────────┐    ┌──────────────┐
      │ PostgreSQL   │    │    Redis     │
      │ + pgvector   │    │ Queue/Cache  │
      └──────────────┘    └──────────────┘
                                │
                                ↓
                       ┌────────────────┐
                       │ Agent Workers  │
                       └───────┬────────┘
                               ↓
                       ┌────────────────┐
                       │ Docker Sandbox │
                       │                │
                       │ Clone Repo     │
                       │ Modify Code    │
                       │ Run Tests      │
                       │ Review Diff    │
                       └────────────────┘
```

---

# 🛠 Tech Stack

## Frontend

* React Native
* Expo
* TypeScript
* Expo Router
* React Native Web
* Zustand
* TanStack Query
* Zod
* NativeWind

## Backend

* Python
* FastAPI
* Pydantic
* SQLAlchemy
* Alembic
* PostgreSQL
* pgvector
* Redis

## AI / Agents

* LangGraph
* AI Gateway
* Model Router
* Repository-aware RAG
* Embeddings
* Structured AI outputs

## AI Providers

Loom is designed around a provider abstraction so models can be changed without rewriting the agent system.

Potential providers include:

* Ollama Cloud
* OpenRouter
* Google Gemini
* Other compatible model providers

```text
                 ┌──────────────────┐
                 │    AI Gateway    │
                 └────────┬─────────┘
                          ↓
                 ┌──────────────────┐
                 │  Model Router    │
                 └────────┬─────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ↓                 ↓                 ↓
   Ollama Cloud       OpenRouter         Gemini
```

---

# 🗃 Repository Intelligence

Loom creates a structured understanding of repositories.

A repository can be indexed into:

```text
Repository
│
├── Metadata
├── Files
├── Directories
├── Symbols
├── Dependencies
├── Documentation
├── Tests
├── Issues
├── Pull Requests
├── TODOs
└── Embeddings
```

This allows agents to perform semantic searches such as:

> "Where is authentication handled?"

or:

> "Find the code responsible for processing uploaded PDFs."

or:

> "Which parts of the application have tests for this behavior?"

---

# 🌳 Contribution Workflow

## 1. Discover

User opens Loom and discovers open-source projects.

---

## 2. Select

User selects a repository.

---

## 3. Analyze

Loom analyzes the actual repository.

---

## 4. Opportunities

Loom generates ranked contribution opportunities.

Each opportunity contains:

```text
Title
Description
Category
Difficulty
Impact
Confidence
Relevant Files
Relevant Issues
Suggested Approach
```

---

## 5. Plan

The Solution Planner creates an implementation plan.

Example:

```text
1. Update authentication service
2. Add token refresh handling
3. Add unit tests
4. Update documentation
5. Run test suite
```

---

## 6. Approve

The developer reviews the plan.

```text
[ Approve Plan ]
[ Reject ]
```

---

## 7. Implement

Loom creates an isolated workspace and allows the implementation agent to modify the code.

---

## 8. Test

The Test Agent:

* Detects the project's test system
* Runs relevant tests
* Runs broader tests where appropriate
* Analyzes failures
* Requests fixes from the implementation agent

---

## 9. Review

The Code Review Agent independently reviews the resulting changes.

It checks:

* Correctness
* Scope
* Maintainability
* Tests
* Security
* Performance
* Repository conventions
* Potential regressions

---

## 10. Final Approval

The developer sees:

```text
Files Changed
Diff
Tests
Test Results
AI Review
Potential Issues
```

The developer decides whether to continue.

---

## 11. Pull Request

After approval, Loom:

1. Creates/updates the contribution branch
2. Pushes the changes
3. Generates the PR title
4. Generates the PR description
5. Creates a real GitHub Pull Request

The PR belongs to the user's GitHub account.

---

# ⚡ Auto Contribute

The central Loom experience is **Auto Contribute**.

Instead of manually navigating through the entire process, users can start with:

```text
        AUTO CONTRIBUTE
               ↓
        Select Repository
               ↓
        Analyze Repository
               ↓
      Find Contribution
               ↓
       Generate Plan
               ↓
          Approve
               ↓
         Implement
               ↓
       Test + Debug
               ↓
        Code Review
               ↓
          Approve
               ↓
        Create PR
```

The goal is not to remove the developer.

The goal is to remove the repetitive work around contributing.

---

# 📱 Application Screens

The initial application includes:

### Splash

Loom branding and application initialization.

### Home

Personalized contribution dashboard.

### Discover

Browse and search open-source projects.

### Repository

Detailed repository overview and AI analysis.

### Opportunities

AI-generated contribution opportunities.

### Contribution

Track an active contribution.

### Agent Activity

Observe AI actions in real time.

### Profile

GitHub account and contribution history.

### Settings

AI provider, security, GitHub connection, and application preferences.

---

# 📡 Real-Time Agent Activity

Long-running AI workflows provide live updates through WebSockets.

Example:

```text
Analyzing repository...
        ↓
Reading project structure...
        ↓
Analyzing CONTRIBUTING.md...
        ↓
Finding relevant issues...
        ↓
Generating opportunities...
        ↓
Creating implementation plan...
        ↓
Waiting for approval...
```

During implementation:

```text
Creating workspace...
        ↓
Installing dependencies...
        ↓
Implementing changes...
        ↓
Running tests...
        ↓
Test failed
        ↓
Analyzing failure...
        ↓
Applying fix...
        ↓
Running tests again...
        ↓
All tests passed
        ↓
Running code review...
```

---

# 📊 Contribution History

Loom maintains a history of contribution workflows.

Users can see:

* Repository
* Contribution
* Status
* Branch
* Tests
* Review
* Pull Request
* Agent activity
* Execution time

Example statuses:

```text
DISCOVERED
ANALYZING
PLANNING
WAITING_FOR_APPROVAL
IMPLEMENTING
TESTING
REVIEWING
WAITING_FOR_FINAL_APPROVAL
PUSHING
PR_CREATED
FAILED
CANCELLED
```

---

# 🧱 Project Structure

A simplified structure:

```text
loom/
│
├── apps/
│   └── mobile/
│       ├── app/
│       ├── components/
│       ├── features/
│       ├── hooks/
│       ├── services/
│       ├── stores/
│       └── utils/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── agents/
│   │   ├── github/
│   │   ├── ai/
│   │   └── workers/
│   │
│   └── tests/
│
├── sandbox/
│   ├── Dockerfile
│   ├── runner/
│   └── policies/
│
├── infrastructure/
│   ├── docker/
│   └── deployment/
│
└── docs/
    ├── architecture/
    ├── security/
    ├── agents/
    └── api/
```

---

# 🔄 AI Provider Abstraction

Loom does not tightly couple its agents to a single AI provider.

```text
AIProvider
│
├── OllamaCloudProvider
├── OpenRouterProvider
├── GeminiProvider
└── FutureProvider
```

This allows Loom to:

* Switch models
* Compare providers
* Route different tasks to different models
* Control cost
* Handle provider failures
* Add new providers without changing agent logic

---

# 🧠 Intelligent Model Routing

Different tasks may require different models.

For example:

```text
Repository summarization
        ↓
Cost-efficient model

Complex code reasoning
        ↓
High-reasoning model

Code generation
        ↓
Code-specialized model

Simple classification
        ↓
Fast model
```

The Model Router determines which provider/model should handle each task.

---

# 🔐 GitHub Integration

Loom integrates with GitHub to access repositories and perform contribution operations.

The backend manages:

* Authentication
* Repository access
* Repository cloning
* Issues
* Pull Requests
* Branches
* Commits
* Push operations

GitHub credentials are never exposed to the client application.

---

# 🧪 Testing Strategy

Loom itself is designed to be tested at multiple levels.

### Frontend

* Unit tests
* Component tests
* Integration tests
* Navigation tests

### Backend

* Unit tests
* API tests
* Database tests
* Agent tests
* GitHub integration tests

### Agent System

* Deterministic fixtures
* Tool-call validation
* Workflow state tests
* Failure recovery tests
* Prompt-injection tests

### End-to-End

```text
GitHub Login
      ↓
Repository Selection
      ↓
Repository Analysis
      ↓
Opportunity
      ↓
Plan
      ↓
Implementation
      ↓
Tests
      ↓
Review
      ↓
PR
```

---

# 🛡️ Design Principles

Loom follows several important principles.

### Real Over Simulated

Real repositories.

Real code.

Real tests.

Real GitHub branches.

Real Pull Requests.

---

### Human Over Autonomous

AI assists the developer.

The developer remains responsible for approving important actions.

---

### Context Over Guessing

AI recommendations should be based on repository evidence rather than generic suggestions.

---

### Security Over Convenience

AI-generated code executes inside isolated environments.

Secrets and credentials remain protected.

---

### Small Changes Over Massive Refactors

Contribution opportunities should generally be scoped so that they can realistically be reviewed and accepted by maintainers.

---

### Open Source First

Loom is designed around helping developers become better open-source contributors rather than simply generating code.

---

# 🗺 Roadmap

## Phase 1 — Foundation

* [x] Project definition
* [ ] React Native application
* [ ] Expo setup
* [ ] FastAPI backend
* [ ] PostgreSQL
* [ ] Redis
* [ ] Authentication
* [ ] GitHub integration

## Phase 2 — Repository Intelligence

* [ ] Repository search
* [ ] Repository cloning
* [ ] File discovery
* [ ] README analysis
* [ ] CONTRIBUTING analysis
* [ ] Build detection
* [ ] Test detection
* [ ] AST analysis
* [ ] Repository indexing
* [ ] Embeddings
* [ ] Semantic search

## Phase 3 — AI Contribution Discovery

* [ ] GitHub issue analysis
* [ ] Pull Request analysis
* [ ] TODO/FIXME analysis
* [ ] Duplicate detection
* [ ] Opportunity generation
* [ ] Opportunity scoring
* [ ] Contribution UI

## Phase 4 — AI Implementation

* [ ] Solution Planner
* [ ] Plan approval
* [ ] Isolated workspace
* [ ] Docker sandbox
* [ ] Command runner
* [ ] Implementation Agent
* [ ] Test Agent
* [ ] Debug loop
* [ ] Code Review Agent

## Phase 5 — GitHub Automation

* [ ] Branch creation
* [ ] Commit generation
* [ ] Push changes
* [ ] PR generation
* [ ] PR creation
* [ ] Contribution tracking

## Phase 6 — Production

* [ ] WebSocket agent streaming
* [ ] Observability
* [ ] Rate limiting
* [ ] Secret scanning
* [ ] Security audit
* [ ] Failure recovery
* [ ] Cost monitoring
* [ ] Production deployment
* [ ] End-to-end testing

---

# 🌎 Vision

Loom's long-term goal is to make contributing to open source dramatically more accessible.

A developer should be able to discover a project they care about and say:

> **"I want to contribute to this."**

Loom should help them understand the project, identify a meaningful contribution, build it safely, validate it, and submit it to the maintainers.

Not by replacing developers.

But by giving developers an intelligent engineering companion that helps them navigate unfamiliar codebases.

---

# 🤝 Contributing

Loom itself is intended to be an open-source project.

Contributions are welcome.

You can contribute through:

* Bug reports
* Feature requests
* Documentation
* UI/UX improvements
* Backend improvements
* AI/agent improvements
* Security improvements
* Testing
* Performance improvements

More contribution guidelines will be added as the project matures.

---

# 📄 License

License information will be added as the project approaches its initial public release.

---

# ⭐ The Goal

**Make open-source contribution accessible to everyone.**

```text
        Find a project.
              ↓
        Understand it.
              ↓
        Find a problem.
              ↓
        Build the solution.
              ↓
        Ship the contribution.
              ↓
        Help open source grow.
```

### Loom 🧵

> **Weaving developers and open source together.**
