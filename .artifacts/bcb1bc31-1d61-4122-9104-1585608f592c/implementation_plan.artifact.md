# Implement AI Streaming across the Stack

Provide real-time feedback for long-running AI operations by streaming "thinking" tokens and intermediate progress via WebSockets to the frontend.

## User Review Required

> [!IMPORTANT]
> This change introduces a "Thinking" state in the UI activity timeline. The backend will now emit many more WebSocket events during AI generation.

## Proposed Changes

### Backend - AI Gateway & Providers

#### [MODIFY] [backend/app/ai/gateway.py](file:///C:/Users/shubham/Documents/ReactNative/Loom/backend/app/ai/gateway.py)
- Update `chat_structured` to accept an optional `on_token` async callback.
- If `on_token` is provided, the gateway will use the provider's streaming capability to fetch tokens, call the callback, and then reassemble the full response for Pydantic validation.

#### [MODIFY] [backend/app/ai/providers/openrouter.py](file:///C:/Users/shubham/Documents/ReactNative/Loom/backend/app/ai/providers/openrouter.py)
- Refactor `chat_structured` to use `chat_stream` internally when a callback is requested.

---

### Backend - Agents & Services

#### [MODIFY] [backend/app/agents/solution_planner.py](file:///C:/Users/shubham/Documents/ReactNative/Loom/backend/app/agents/solution_planner.py)
- Update `create_plan` to accept `agent_run_id` and `db`.
- Pass a callback to `ai_gateway.chat_structured` that emits `thinking_chunk` events.

#### [MODIFY] [backend/app/agents/implementation.py](file:///C:/Users/shubham/Documents/ReactNative/Loom/backend/app/agents/implementation.py)
- Update `implement_solution` to accept `agent_run_id` and `db`.
- Pass a callback to emit thinking events while generating file changes.

#### [MODIFY] [backend/app/services/agent_run_service.py](file:///C:/Users/shubham/Documents/ReactNative/Loom/backend/app/services/agent_run_service.py)
- Ensure `emit_event` handles `thinking_chunk` events efficiently (possibly skipping DB persistence for very high-frequency tokens to avoid bloat).

---

### Frontend - UI & Hooks

#### [MODIFY] [src/hooks/use-agent-events.ts](file:///C:/Users/shubham/Documents/ReactNative/Loom/src/hooks/use-agent-events.ts)
- Add a `thinkingText` state that accumulates `thinking_chunk` messages.
- Reset `thinkingText` when a new non-thinking event arrives or when the agent switches files.

#### [MODIFY] [src/app/contribution/[id]/activity.tsx](file:///C:/Users/shubham/Documents/ReactNative/Loom/src/app/contribution/[id]/activity.tsx)
- Display the `thinkingText` in the Live Timeline or as a special "Active Reasoning" card.

## Verification Plan

### Automated Tests
- Run backend unit tests for agents to ensure Pydantic validation still passes after reassembling streams.

### Manual Verification
- Trigger a "Generate Plan" operation and verify tokens appear in the terminal and then in the UI.
- Trigger an "Implement" operation and verify file generation "thinking" is visible.
