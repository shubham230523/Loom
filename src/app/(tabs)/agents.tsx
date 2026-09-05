import { View } from 'react-native';
import { ScreenContainer } from '@/components/ui/screen-container';
import { Text } from '@/components/ui/text';
import { EmptyState } from '@/components/ui/empty-state';

export default function AgentsScreen() {
  return (
    <ScreenContainer scrollable className="py-6">
      <View className="mb-8">
        <Text variant="title">Running Agents</Text>
        <Text variant="muted">Monitor and manage your active autonomous agents.</Text>
      </View>

      <View className="flex-1">
        <EmptyState
          title="No agents running"
          description="Your autonomous agents will appear here when they are active on tasks."
          icon="cpu"
          className="min-h-[400px]"
        />
      </View>
    </ScreenContainer>
  );
}
