# AI Glossary and Mindset

Transitioning to AI-assisted development requires a shift in how you think about "computing." This guide explains the core concepts you'll encounter every day.

## Core Concepts

### 1. LLMs (Large Language Models)
An LLM is a type of AI trained on massive amounts of text data. For developers, think of it not as a database, but as a **highly sophisticated pattern-matcher and reasoning engine**. It predicts the next most likely "chunk" of data based on the input it receives.

### 2. Tokens
Tokens are the basic units of text that an LLM processes. They aren't exactly words; they can be parts of words, whitespace, or punctuation.
- **Why it matters:** Most AI models have limits on how many tokens they can process at once, and costs are often calculated per token.

### 3. Context Window
The context window is the "short-term memory" of the AI. It represents the maximum number of tokens the model can "see" and consider at one time (including your prompt and the conversation history).
- **Developer Tip:** If your codebase is too large for the context window, the AI will "forget" the earlier parts of the file or conversation.

### 4. Hallucinations
A hallucination occurs when an LLM generates information that is factually incorrect but sounds highly confident and plausible.
- **Critical Mindset:** Never trust AI-generated code blindly. **Always verify and test.** AI is a co-pilot, not the captain.

### 5. System Prompts
A system prompt (or system instruction) is a high-level directive given to the AI to define its persona, constraints, and behavior. It sets the "rules of engagement" before the user even types a message.
- **Example:** "You are an expert Android developer who prioritizes Kotlin and Material 3 design."

## The AI Mindset Shift

- **Be Specific:** The more context you provide (the "Context Window"), the better the output.
- **Iterative Refinement:** Don't expect perfection on the first try. Use the AI's output as a draft and refine it through follow-up prompts.
- **Focus on Reasoning:** Use AI to explain *why* something is happening, not just to give you the `copy-paste` fix.
