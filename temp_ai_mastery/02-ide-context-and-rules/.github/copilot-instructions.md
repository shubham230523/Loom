# GitHub Copilot Custom Instructions

## Context Awareness
You are working on a high-performance, modern software project. Your suggestions should prioritize:
1. **Type Safety:** Always provide type-safe implementations.
2. **Modern Standards:** Use Kotlin 2.x+, TypeScript 5.x+, and the latest stable Rust.
3. **Security:** Avoid patterns that introduce SQL injection, XSS, or memory leaks.

## Project Standards
- **Kotlin:** Use Compose Material 3 and Hilt for DI.
- **TypeScript:** Use Zod for schema validation and Tailwind CSS for styling.
- **Rust:** Use `tokio` for async and `anyhow` for simple error handling in binaries.

## Interaction Style
- Keep explanations brief.
- If the requested task is complex, provide a high-level plan before implementation.
- If you see an opportunity for optimization, suggest it with a comment.
