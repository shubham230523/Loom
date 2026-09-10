import { useState, useEffect, useCallback } from 'react';
import { agentWsService, AgentEvent } from '@/services/agent-ws.service';

export function useAgentEvents(agentRunId?: string) {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [lastEvent, setLatestEvent] = useState<AgentEvent | null>(null);

  const handleEvent = useCallback((event: AgentEvent) => {
    setEvents(prev => [...prev, event]);
    setLatestEvent(event);
  }, []);

  useEffect(() => {
    if (!agentRunId || agentRunId.startsWith('dummy-')) return;

    agentWsService.connect(agentRunId, handleEvent);

    return () => {
      agentWsService.disconnect();
    };
  }, [agentRunId, handleEvent]);

  return {
    events,
    lastEvent,
    clearEvents: () => setEvents([])
  };
}
