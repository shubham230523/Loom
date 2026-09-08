# Multi-File Refactoring with AI Prompt Chains

Large-scale refactors—like migrating from one library to another or restructuring a core architecture—are high-risk and time-consuming. AI can dramatically accelerate this, but only if you use an **iterative prompt chain** to maintain consistency across dozens of files.

## The Multi-File Refactoring Strategy

Do not try to refactor the entire codebase in one prompt. Use this three-step cycle:

### Phase 1: The "Single Source of Truth" (SSOT)
Before touching any files, define the new pattern clearly.
- **Goal:** Create a reference implementation.
- **Prompt:** *"I am migrating from REST to GraphQL. Here is one existing REST-based repository and the new GraphQL schema. Generate the new GraphQL-based repository for this specific file as a reference."*

### Phase 2: The Migration Chain
Once the reference is perfect, use a prompt chain to replicate it.
- **Goal:** Apply the pattern to batches of related files.
- **Prompt Template:**
  > "Using the pattern established in `[REFERENCE_FILE]`, migrate the following files from [OLD PATTERN] to [NEW PATTERN].
  >
  > **Constraints:**
  > - Keep the business logic identical.
  > - Only change the [specific layer, e.g., Data Layer/Networking].
  > - Ensure all imports are updated to the new libraries.
  >
  > Files to migrate:
  > - `[FILE_PATH_1]`
  > - `[FILE_PATH_2]`
  > - ..."

### Phase 3: The Verification & Cleanup
Use the AI to audit its own work and identify missing pieces.
- **Goal:** Ensure no broken references or deprecated code remains.
- **Prompt:** *"I have just finished migrating 20 files to [NEW PATTERN]. Scan the attached list of files and identify any remaining instances of [OLD PATTERN] or broken imports that I might have missed."*

---

## Common Advanced Workflows

### 1. Migrating REST to GraphQL
- **Focus:** Data models and networking clients.
- **Tip:** Feed the AI your `.graphql` schema and ask it to generate the corresponding DTOs first.

### 2. Updating Deprecated Libraries
- **Focus:** API signatures and dependency injection.
- **Tip:** Provide the migration guide for the new library version as context.

### 3. Enforcing Dependency Injection (DI)
- **Focus:** Constructor injection and module configuration.
- **Tip:** Provide your DI framework's "Root Module" or "Component" file so the AI knows how to register new dependencies.

---

## Best Practices
- **Small Batches:** Refactor 3-5 files at a time. This prevents the AI from losing track of the context window.
- **Commit Frequently:** Make a Git commit after each successful batch refactor.
- **Audit Imports:** AI often forgets to remove unused imports. Always run your IDE's "Optimize Imports" after a large refactor.
- **Use `grep` or `find_usages`:** Use your IDE tools to find every instance of the old pattern before you start the migration chain.
