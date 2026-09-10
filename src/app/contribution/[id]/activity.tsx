import { useLocalSearchParams, useRouter, Stack } from 'expo-router';
import { View, ScrollView } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { SymbolView } from 'expo-symbols';
import { ScreenContainer } from '@/components/ui/screen-container';
import { Text } from '@/components/ui/text';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AgentTimeline } from '@/components/agent-timeline';
import { useAgentEvents } from '@/hooks/use-agent-events';
import apiClient from '@/services/api-client';
import { Contribution } from '@/types/contribution';
import { useTheme } from '@/hooks/use-theme';

export default function AgentActivityScreen() {
  const { id, repositoryId, agentRunId } = useLocalSearchParams<{ id: string, repositoryId: string, agentRunId: string }>();
  const theme = useTheme();
  const router = useRouter();

  // 1. WebSocket Hook
  const { events: realEvents, lastEvent: realLastEvent } = useAgentEvents(agentRunId);

  // Dummy events for testing
  const dummyEvents: any[] = [
    { agent_run_id: 'dummy-run-456', event_type: 'agent_started', message: 'Coder agent started execution.', timestamp: new Date(Date.now() - 30000).toISOString() },
    { agent_run_id: 'dummy-run-456', event_type: 'step_started', message: 'Restoring workspace...', timestamp: new Date(Date.now() - 25000).toISOString() },
    { agent_run_id: 'dummy-run-456', event_type: 'step_completed', message: 'Workspace restored.', timestamp: new Date(Date.now() - 20000).toISOString() },
    { agent_run_id: 'dummy-run-456', event_type: 'step_started', message: 'Applying implementation changes (Attempt 1)', timestamp: new Date(Date.now() - 15000).toISOString() },
    { agent_run_id: 'dummy-run-456', event_type: 'file_changed', message: 'Modified src/services/auth.service.ts', timestamp: new Date(Date.now() - 12000).toISOString() },
    { agent_run_id: 'dummy-run-456', event_type: 'file_changed', message: 'Modified src/services/api-client.ts', timestamp: new Date(Date.now() - 10000).toISOString() },
    { agent_run_id: 'dummy-run-456', event_type: 'test_completed', message: 'Implementation tests passed.', timestamp: new Date(Date.now() - 8000).toISOString() },
    { agent_run_id: 'dummy-run-456', event_type: 'review_started', message: 'Triggering autonomous technical audit.', timestamp: new Date(Date.now() - 5000).toISOString() },
    { agent_run_id: 'dummy-run-456', event_type: 'review_completed', message: 'Review finished: APPROVE', timestamp: new Date(Date.now() - 2000).toISOString() },
    { agent_run_id: 'dummy-run-456', event_type: 'completed', message: 'Agent execution completed successfully.', timestamp: new Date(Date.now() - 1000).toISOString() },
  ];

  const events = agentRunId === 'dummy-run-456' ? dummyEvents : realEvents;
  const lastEvent = agentRunId === 'dummy-run-456' ? dummyEvents[dummyEvents.length - 1] : realLastEvent;

  // 2. Poll for contribution status (as fallback/final state)
  const { data: contribution } = useQuery({
    queryKey: ['contribution-activity', id],
    queryFn: async () => {
      if (id === 'dummy-contrib-123') {
        return {
          id,
          status: 'completed' // Force completed for dummy
        } as any;
      }
      const { data } = await apiClient.get<Contribution>(`/api/v1/repositories/${repositoryId}/contributions/${id}`);
      return data;
    },
    enabled: !!id && !!repositoryId,
    refetchInterval: 5000
  });

  const isCompleted = contribution?.status === 'pull_request_created' || lastEvent?.event_type === 'completed';
  const isFailed = contribution?.status === 'failed' || lastEvent?.event_type === 'failed';

  return (
    <ScreenContainer className="py-6">
      <Stack.Screen options={{ title: 'Agent Activity', headerTitleAlign: 'center' }} />

      <View className="px-6 gap-8">
        <View className="items-center mt-4">
            <View className="w-20 h-20 rounded-3xl bg-primary/10 items-center justify-center mb-4">
                <SymbolView
                    name={isFailed ? "exclamationmark.triangle.fill" : "cpu.fill"}
                    size={40}
                    tintColor={isFailed ? "#EF4444" : theme.primary}
                />
            </View>
            <Text variant="title" className="text-2xl font-bold">Loom Coder</Text>
            <Text variant="muted" className="text-center mt-1">
                {lastEvent?.message || "Initializing autonomous execution..."}
            </Text>
        </View>

        <Card>
            <CardHeader>
                <CardTitle><Text variant="subtitle">Live Timeline</Text></CardTitle>
            </CardHeader>
            <CardContent>
                <AgentTimeline events={events} />
            </CardContent>
        </Card>

        {/* Live Logs / Events List */}
        <View className="flex-1">
            <Text weight="bold" className="text-lg mb-3 px-1">Detailed Logs</Text>
            <ScrollView
                className="bg-muted/30 rounded-xl p-4 border border-border/50"
                contentContainerStyle={{ gap: 12 }}
            >
                {events.length === 0 && (
                    <Text variant="small" className="text-muted-foreground italic text-center py-4">
                        Waiting for events...
                    </Text>
                )}
                {[...events].reverse().map((event, i) => (
                    <View key={i} className="gap-1">
                        <View className="flex-row items-center gap-2">
                             <Text variant="small" className="text-[10px] font-mono text-muted-foreground">
                                {new Date(event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                             </Text>
                             <ActivityBadge
                                label={event.event_type.replace('_', ' ').toUpperCase()}
                                variant="secondary"
                             />
                        </View>
                        <Text variant="small" className="leading-5">{event.message}</Text>
                    </View>
                ))}
            </ScrollView>
        </View>

        {/* Action Footer */}
        {(isCompleted || isFailed) && (
            <View className="mt-4 mb-12">
                <Button
                    label={isCompleted ? "Review Changes" : "Return to Backlog"}
                    onPress={() => {
                        if (isCompleted) {
                            router.replace({ pathname: '/contribution/[id]/review', params: { id, repositoryId } });
                        } else {
                            router.back();
                        }
                    }}
                />
            </View>
        )}
      </View>
    </ScreenContainer>
  );
}

function ActivityBadge({ label, variant }: { label: string, variant: 'default' | 'secondary' }) {
    return (
        <View className={`px-2 py-0.5 rounded-md ${variant === 'secondary' ? 'bg-muted' : 'bg-primary'} scale-75 origin-left`}>
            <Text className={`text-[10px] font-bold ${variant === 'secondary' ? 'text-muted-foreground' : 'text-primary-foreground'}`}>
                {label}
            </Text>
        </View>
    );
}
