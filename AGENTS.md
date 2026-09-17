# Loom Agents 🤖

Loom uses a multi-agent architecture to orchestrate repository analysis and code contributions.

## Current Limitations & Mock-First Approach

While the architecture is designed for production-level autonomy, the current version is optimized as a **functional prototype**.

1. **Structured Output Resilience:** Small/Free AI models frequently hallucinate schema keys. The backend uses aggressive mapping and fallback safe-defaults to prevent crashes.
2. **Environment Determinism:** Real-world build systems (Android/Gradle/Node) often fail in sandboxes due to network or dependency constraints.
3. **Task Specificity:** Agents perform best when tasks are deterministic. Ambiguous tasks (e.g., "Fix TODO on line 25") are prone to reasoning loops.

**Recommendation:** For the best experience, use the "Real-World Mock" feature to demonstrate the end-to-end GitHub PR workflow.

---

# Expo Development Note
Read the exact versioned docs at https://docs.expo.dev/versions/v57.0.0/ before writing any code.
