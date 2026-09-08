# Agentic Terminal Tools: A Developer's Guide

Terminal-based AI agents represent the "next level" of AI-assisted development. Unlike chat-based assistants, these tools have the ability to run terminal commands, read/write files autonomously, and execute entire workflows (like debugging a failing test suite) with minimal human intervention.

## Top Terminal AI Agents

### 1. Aider
Aider is a command-line chat tool that allows you to edit code in your local git repo. It is exceptionally good at "pair programming" directly in the terminal.
- **Key Strength:** Seamless Git integration and surgical code edits.
- **Best Use Case:** Feature implementation and refactoring.

### 2. Claude Code (Beta)
Anthropic's official CLI tool for interacting with Claude 3.5 Sonnet directly from your terminal.
- **Key Strength:** Deep understanding of complex reasoning and high-quality code output.
- **Best Use Case:** Explaining complex architectures and generating high-level plans.

### 3. OpenHands (formerly OpenDevin)
An open-source agentic platform that can use a variety of LLMs to perform complex engineering tasks.
- **Key Strength:** Can use a browser and terminal autonomously to solve issues.
- **Best Use Case:** Solving GitHub issues and autonomous debugging.

---

## Setup & Configuration

### General Requirements
- **API Keys:** You'll need API keys for Anthropic (Claude) or OpenAI (GPT).
- **Environment:** Ensure you have `Node.js` or `Python` installed, depending on the tool.

### Aider Setup
```bash
python -m pip install aider-chat
export ANTHROPIC_API_KEY=your-key
aider
```

### Claude Code Setup
```bash
npm install -g @anthropic-ai/claude-code
claude
```

---

## Autonomous Workflow: Fixing a Failing Test Suite

One of the most powerful uses of a terminal agent is letting it fix a broken build.

### The Workflow:
1. **Identify the Failure:** Run your tests (`npm test`, `pytest`, etc.).
2. **Invoke the Agent:** Start your agent (e.g., `aider`).
3. **The "Fix It" Command:**
   > "Run the test suite. If any tests fail, analyze the error, read the relevant source code, and fix the implementation until all tests pass. Do not stop until the build is green."
4. **Agent Action:**
   - The agent runs the test command.
   - It parses the stack trace.
   - It opens the failing file and identifies the bug.
   - It writes the fix and **re-runs the tests** to verify.

---

## Terminal Agent Cheat Sheet

| Task | Aider Command | Claude Code / General Agent |
| :--- | :--- | :--- |
| **Add Files** | `/add path/to/file` | Just mention the file path in your prompt. |
| **Run Tests** | `/run npm test` | "Run npm test and show me the output." |
| **Undo Last** | `/undo` | "Revert the last change you made." |
| **Commit** | (Automated by Aider) | "Commit these changes with a descriptive message." |

## Safety & Best Practices
- **Use Git Branches:** Always run agents on a new feature branch.
- **Review Every Diff:** Even though they are "autonomous," you should review the diff before merging.
- **Limit Scope:** Give agents specific tasks rather than "fix the whole repo."
