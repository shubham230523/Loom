# IDE Context and Rules

One of the biggest frustrations with AI coding assistants is their tendency to suggest outdated APIs, ignore project-specific standards, or hallucinate library versions.

## Why Context Rules Matter

AI models are trained on snapshots of the internet. They don't inherently know that your project uses a specific version of Kotlin, a strict TypeScript configuration, or a custom Rust error-handling pattern.

By providing "Rules" or "Instructions" files at the root of your project, you:
1. **Enforce Consistency:** Ensure all AI-generated code follows your team's style guide.
2. **Prevent Hallucinations:** Direct the AI to use specific libraries or internal patterns.
3. **Reduce Rework:** Get better first-draft code, reducing the time spent on manual corrections.
4. **Project Awareness:** Help the AI understand the architecture (e.g., MVI in Android, Hexagonal in Rust).

## How to Use These Templates

Copy the content of the relevant template to the root of your project:

- **Cursor:** Use `.cursorrules`.
- **GitHub Copilot:** Use `.github/copilot-instructions.md`.
- **Cline / Roo Code:** Use `.clinerules`.

*Note: Some extensions require these files to be in the root directory to be automatically picked up.*
