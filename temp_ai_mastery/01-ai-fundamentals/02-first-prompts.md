# First Prompts: Beginner AI Workflows

The best way to learn AI-assisted development is by doing. Here are 5 core workflows with copy-pasteable prompt templates to get you started.

---

## 1. Explaining Legacy/Unfamiliar Code
Use this when you encounter a "wall of code" that you don't understand.

**Prompt Template:**
> "Act as a Senior Developer. Explain what this code does in simple terms. Break it down section by section and highlight any potential side effects or dependencies.
>
> [PASTE CODE HERE]"

---

## 2. Converting Code Between Languages/Frameworks
Perfect for migrating logic or translating a solution you found online.

**Prompt Template:**
> "I have this [SOURCE LANGUAGE/FRAMEWORK] code that I need to convert to [TARGET LANGUAGE/FRAMEWORK]. Ensure you follow the idiomatic patterns and best practices of the target language.
>
> Source Code:
> [PASTE CODE HERE]"

---

## 3. Generating Boilerplate and Data Models
Skip the repetitive typing of POJOs, DTOs, or standard layouts.

**Prompt Template:**
> "Generate a [LANGUAGE] data model based on the following JSON schema. Include standard methods like getters/setters (if applicable), a constructor, and a method to convert it to a string.
>
> JSON Schema:
> [PASTE JSON HERE]"

---

## 4. Finding and Fixing Bug Stack Traces
AI is exceptionally good at parsing cryptic error messages and suggesting fixes.

**Prompt Template:**
> "I'm getting the following error in my [LANGUAGE/ENVIRONMENT] project. Analyze the stack trace and the provided code snippet to identify the root cause and suggest a fix.
>
> Error:
> [PASTE ERROR HERE]
>
> Relevant Code:
> [PASTE CODE HERE]"

---

## 5. Writing Unit Tests for Existing Code
Automate the creation of test suites to ensure your logic is robust.

**Prompt Template:**
> "Act as a Quality Engineer. Write comprehensive unit tests for the following function using [TESTING FRAMEWORK, e.g., JUnit/Mockito]. Include tests for the happy path, edge cases, and potential error conditions.
>
> Function:
> [PASTE CODE HERE]"

---

## Best Practices for Prompting
- **Provide Context:** Always mention the language, framework, and version you are using.
- **Use Markdown:** Use triple backticks (\`\`\`) to wrap your code snippets so the AI can distinguish between your instructions and the code.
- **Iterate:** If the first result isn't perfect, say: "That's close, but can you change [X] to [Y]?"
