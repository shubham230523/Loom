# System Stability and Frontend Cleanup

This plan addresses the backend connectivity issues reported in the logs and the numerous TypeScript errors in the frontend.

## User Review Required

> [!IMPORTANT]
> The backend issues (PostgreSQL, Redis, Docker) are environment-related. You MUST have the Docker daemon running and start the required containers for the backend to function correctly.

> [!NOTE]
> The frontend TypeScript errors are primarily caused by missing Jest type definitions in the TypeScript configuration and mismatched data models between the frontend and backend.

## Proposed Changes

### Infrastructure

#### [ACTION] Start Docker Services
I recommend running the following command in your root directory to start the database and redis:
```bash
docker-compose up -d
```
*Note: Ensure Docker Desktop is running first.*

---

### Backend [MODIFY]

#### [repository.py](file:///C:/Users/shubham/Documents/ReactNative/Loom/backend/app/api/v1/repositories/repository.py) (Hypothetical path)
I will verify the backend schema to ensure `discovery_status` and `discovery_error` are actually returned by the API.

---

### Frontend [MODIFY]

#### [tsconfig.json](file:///C:/Users/shubham/Documents/ReactNative/Loom/tsconfig.json)
Update `compilerOptions` to include `jest` types and improve module resolution for tests.

#### [repository.ts](file:///C:/Users/shubham/Documents/ReactNative/Loom/src/types/repository.ts)
Update `GitHubRepository` interface to include `discovery_status`, `discovery_error`, and add `'not_started'` to `indexing_status`.

#### [discover.tsx](file:///C:/Users/shubham/Documents/ReactNative/Loom/src/app/(tabs)/discover.tsx)
Remove unused imports and variables to resolve linting/TSC errors.

#### [[id].tsx](file:///C:/Users/shubham/Documents/ReactNative/Loom/src/app/repository/[id].tsx)
Fix logic relying on missing or mismatched status fields.

---

## Verification Plan

### Automated Tests
- Run `npx tsc --noEmit` to verify all 69 TypeScript errors are resolved.
- Run `npm test` to ensure Jest tests now correctly recognize the environment.

### Manual Verification
- Once Docker services are up, verify `GET /api/v1/auth/me` and `GET /api/v1/auth/github/callback` no longer return 500 errors.
