# Loom Automated Testing Strategy

This document outlines the testing architecture and strategy for the Loom application, following the testing pyramid.

## Testing Pyramid

1. **Unit Tests**: Focus on isolated logic, utility functions, and individual services/stores.
2. **Integration Tests**: Focus on the interaction between multiple components, such as API endpoints with the database or frontend components with hooks.
3. **End-to-End (E2E) Tests**: Focus on critical user journeys across the full stack.

## Backend Testing (Python/FastAPI)

- **Framework**: `pytest`
- **Database**: PostgreSQL (using an isolated test database)
- **Tooling**: `pytest-asyncio`, `httpx` (TestClient), `pytest-env`

### Categories
- **Unit Tests**: Found in `backend/tests/unit`. Covers services, AI parsing, and utils.
- **Integration Tests**: Found in `backend/tests/integration`. Covers FastAPI endpoints and database interactions.
- **Security Tests**: Found in `backend/tests/security`. Covers authentication, authorization, and prompt injection.

### Commands
- `npm run test:backend`: Runs all backend tests.
- `npm run test:backend:unit`: Runs only backend unit tests.

## Frontend Testing (React Native/Expo)

- **Framework**: `jest`
- **Utilities**: `jest-expo`, `@testing-library/react-native`

### Categories
- **Unit Tests**: Covers Zustand stores, hooks, and utility functions.
- **Component Tests**: Covers UI components in isolation (loading, error, interactions).
- **Navigation Tests**: Covers auth guards and routing logic.

### Commands
- `npm run test:frontend`: Runs all frontend tests.
- `npm run test:frontend:watch`: Runs frontend tests in watch mode.

## External Dependency Strategy

### GitHub API
- Most tests use mocked responses to avoid rate limits and dependency on network.
- A separate `integration/github` suite can be run with real credentials if provided.

### AI Providers
- Real AI calls are mocked using contract tests.
- We test that Loom sends the correct prompts and handles various response formats (JSON, markdown, malformed).

### Docker Sandbox
- Tests use a mock command runner for unit/integration tests.
- Sandbox-specific integration tests verify actual container execution.

## Critical User Journeys (E2E)

1. **Auth Flow**: Launch -> GitHub Redirect -> Callback -> Dashboard.
2. **Discovery**: Discover -> Search -> Repo Details.
3. **Workflow**: Repository -> Analysis -> Opportunity -> Plan -> Approval -> Implementation.
