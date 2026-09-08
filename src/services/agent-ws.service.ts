import { useAuthStore } from '@/store/auth-store';

export type AgentEventType =
  | 'agent_started'
  | 'step_started'
  | 'step_completed'
  | 'file_changed'
  | 'test_started'
  | 'test_completed'
  | 'review_started'
  | 'review_completed'
  | 'approval_required'
  | 'pr_created'
  | 'completed'
  | 'failed';

export interface AgentEvent {
  agent_run_id: string;
  event_type: AgentEventType;
  message: string;
  metadata?: any;
  timestamp: string;
}

class AgentWebSocketService {
  private ws: WebSocket | null = null;
  private baseUrl: string;

  constructor() {
    // Standardize WS URL based on API URL
    const apiUrl = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';
    this.baseUrl = apiUrl.replace('http', 'ws');
  }

  connect(agentRunId: string, onEvent: (event: AgentEvent) => void) {
    if (this.ws) {
      this.ws.close();
    }

    const token = useAuthStore.getState().token;
    if (!token) {
      console.error('No auth token available for WebSocket connection');
      return;
    }

    const url = `${this.baseUrl}/ws/agents/${agentRunId}?token=${token}`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log(`WebSocket connected for agent run: ${agentRunId}`);
    };

    this.ws.onmessage = (e) => {
      try {
        const event: AgentEvent = JSON.parse(e.data);
        onEvent(event);
      } catch (err) {
        console.error('Failed to parse agent event:', err);
      }
    };

    this.ws.onerror = (e) => {
      console.error('WebSocket error:', e);
    };

    this.ws.onclose = () => {
      console.log('WebSocket closed');
      this.ws = null;
    };
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export const agentWsService = new AgentWebSocketService();
