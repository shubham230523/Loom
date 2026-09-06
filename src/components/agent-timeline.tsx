import { View } from 'react-native';
import { SymbolView } from 'expo-symbols';
import { Text } from '@/components/ui/text';
import { useTheme } from '@/hooks/use-theme';
import { AgentEvent } from '@/services/agent-ws.service';

type StepStatus = 'upcoming' | 'active' | 'completed' | 'failed';

interface TimelineStep {
  id: string;
  label: string;
  eventTypes: string[];
}

const STEPS: TimelineStep[] = [
  { id: 'discovery', label: 'Repository discovered', eventTypes: ['agent_started'] },
  { id: 'analysis', label: 'Repository analyzed', eventTypes: ['step_completed'] },
  { id: 'opportunity', label: 'Opportunity found', eventTypes: ['opportunity_found'] },
  { id: 'planning', label: 'Plan created', eventTypes: ['approval_required'] },
  { id: 'implementation', label: 'Implementing', eventTypes: ['file_changed', 'step_started'] },
  { id: 'testing', label: 'Testing', eventTypes: ['test_started', 'test_completed'] },
  { id: 'reviewing', label: 'Reviewing', eventTypes: ['review_started', 'review_completed'] },
  { id: 'pr', label: 'PR creation', eventTypes: ['pr_created'] },
];

interface AgentTimelineProps {
  events: AgentEvent[];
}

export function AgentTimeline({ events }: AgentTimelineProps) {
  const theme = useTheme();

  const getStepStatus = (step: TimelineStep, index: number): StepStatus => {
    const hasEvent = events.some(e => step.eventTypes.includes(e.event_type));
    const isFailed = events.some(e => e.event_type === 'failed');

    if (hasEvent) {
        const nextStepHasStarted = STEPS.slice(index + 1).some(s =>
            events.some(e => s.eventTypes.includes(e.event_type))
        );
        if (nextStepHasStarted) return 'completed';

        const lastEvent = events[events.length - 1];
        if (lastEvent.event_type === 'completed') return 'completed';
        if (isFailed) return 'failed';

        return 'active';
    }

    const laterStepStarted = STEPS.slice(index + 1).some(s =>
        events.some(e => s.eventTypes.includes(e.event_type))
    );
    if (laterStepStarted) return 'completed';

    return 'upcoming';
  };

  return (
    <View className="gap-2">
      {STEPS.map((step, index) => {
        const status = getStepStatus(step, index);

        return (
          <View key={step.id} className="flex-row items-center gap-4 py-2">
            <View className="w-6 items-center">
              {status === 'completed' && (
                <SymbolView name="checkmark.circle.fill" size={20} tintColor="#22C55E" />
              )}
              {status === 'active' && (
                <View className="w-5 h-5 rounded-full bg-primary items-center justify-center">
                    <View className="w-2 h-2 rounded-full bg-white" />
                </View>
              )}
              {status === 'upcoming' && (
                <SymbolView name="circle" size={20} tintColor={theme.textSecondary} />
              )}
              {status === 'failed' && (
                <SymbolView name="xmark.circle.fill" size={20} tintColor="#EF4444" />
              )}
            </View>

            <Text
              className={status === 'upcoming' ? 'text-muted-foreground' : 'text-foreground font-medium'}
              style={{ fontSize: 15 }}
            >
              {step.label}
            </Text>
          </View>
        );
      })}
    </View>
  );
}
