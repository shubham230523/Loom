import { View, Platform } from 'react-native';
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
  { id: 'analysis', label: 'Repository analyzed', eventTypes: ['step_completed', 'index_completed'] },
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

const isApple = Platform.OS === 'ios' || Platform.OS === 'macos';

export function AgentTimeline({ events }: AgentTimelineProps) {
  const theme = useTheme();

  const getStepStatus = (step: TimelineStep, index: number): StepStatus => {
    const isFailed = events.some(e => e.event_type === 'failed' || e.event_type === 'step_failed');
    const isCompleted = events.some(e => e.event_type === 'completed');

    // Find index of last step with events
    let lastStepWithEventsIndex = -1;
    for (let i = STEPS.length - 1; i >= 0; i--) {
        if (events.some(e => STEPS[i].eventTypes.includes(e.event_type))) {
            lastStepWithEventsIndex = i;
            break;
        }
    }

    const hasEvent = events.some(e => step.eventTypes.includes(e.event_type));

    if (hasEvent) {
        // If any step AFTER this one has events, then this one is definitely completed
        const laterStepHasStarted = STEPS.slice(index + 1).some(s =>
            events.some(e => s.eventTypes.includes(e.event_type))
        );
        if (laterStepHasStarted) return 'completed';

        // If overall failed and this is the last step we were on
        if (isFailed && index === lastStepWithEventsIndex) return 'failed';

        // If overall completed and this is the last step we were on
        if (isCompleted && index === lastStepWithEventsIndex) return 'completed';

        return 'active';
    }

    // If we haven't reached this step yet, but we've passed it (skipped/implied)
    if (lastStepWithEventsIndex > index) return 'completed';

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
                isApple ? (
                    <SymbolView name="checkmark.circle.fill" size={20} tintColor="#22C55E" />
                ) : (
                    <Text className="text-green-500 text-lg">✅</Text>
                )
              )}
              {status === 'active' && (
                <View className="w-5 h-5 rounded-full bg-primary items-center justify-center">
                    <View className="w-2 h-2 rounded-full bg-white" />
                </View>
              )}
              {status === 'upcoming' && (
                isApple ? (
                    <SymbolView name="circle" size={20} tintColor={theme.textSecondary} />
                ) : (
                    <View className="w-4 h-4 rounded-full border border-muted-foreground/30" />
                )
              )}
              {status === 'failed' && (
                isApple ? (
                    <SymbolView name="xmark.circle.fill" size={20} tintColor="#EF4444" />
                ) : (
                    <Text className="text-red-500 text-lg">❌</Text>
                )
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
