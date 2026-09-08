# Documenting for AI: The ARCHITECTURE.md Template

To get the most out of AI agents (like GitHub Copilot, Cursor, or Roo Code), they need to understand not just your code, but the *intent* and *structure* behind it. An `ARCHITECTURE.md` file acts as a high-level map that guides the AI to generate code that fits perfectly into your project.

## Why AI Needs an ARCHITECTURE.md
Standard `README.md` files are often too generic or focused on installation. An `ARCHITECTURE.md` provides:
- **Design Patterns:** Tells the AI to use MVI instead of MVVM, or Hexagonal instead of Layered.
- **Dependency Rules:** Prevents the AI from importing UI components into the Domain layer.
- **Naming Conventions:** Ensures new files follow your project's specific suffix patterns.
- **Technology Choices:** Explicitly states preferred libraries (e.g., "Use Ktor for networking, not Retrofit").

---

## The AI-Optimized Template

Copy the content below into a new file named `ARCHITECTURE.md` at the root of your project.

```markdown
# Project Architecture

## High-Level Overview
[Briefly describe the project's purpose and core tech stack.]

## Core Design Principles
- **Pattern:** [e.g., MVI, MVVM, Clean Architecture, Hexagonal]
- **Immutability:** [e.g., Use immutable data classes for all state models.]
- **Concurrency:** [e.g., Use Kotlin Coroutines with structured concurrency.]

## Layered Structure
Describe what code lives where to prevent the AI from putting logic in the wrong place.

1. **App/UI Layer:** Views, Composables, ViewModels. No direct database access.
2. **Domain Layer:** Pure business logic (Use Cases/Interactors). No platform dependencies.
3. **Data Layer:** Repositories, APIs, Databases. Handles data mapping.

## Key Technical Decisions
- **Networking:** [e.g., Ktor / OkHttp]
- **Dependency Injection:** [e.g., Hilt / Koin / Dagger]
- **Database:** [e.g., Room / SQLDelight]

## Naming & Style Conventions
- **ViewModels:** Must end in `ViewModel`.
- **Repositories:** Must be interfaces, with implementations in an `impl` package.
- **Tests:** Use the `[ClassName]Test` format.

## AI Instructions
When generating code for this repository:
- Always check the `Domain` layer first for existing business logic.
- Ensure all new API calls are wrapped in a `Result` or `Either` type.
- Never add logic to a View/Composable; delegate to a ViewModel.
```

---

## How to use this with AI
Once you've created your `ARCHITECTURE.md`, you can point the AI to it in your prompts:

> "I need to add a new user profile feature. Read `ARCHITECTURE.md` to understand our pattern and then generate the Repository and ViewModel for this feature."

If you use tools like **Cursor** or **Cline**, they will often index this file automatically and use it as background context for every suggestion they make.
