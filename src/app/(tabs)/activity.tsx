import { View } from 'react-native';
import { ScreenContainer } from '@/components/ui/screen-container';
import { Text } from '@/components/ui/text';
import { EmptyState } from '@/components/ui/empty-state';

export default function ActivityScreen() {
  return (
    <ScreenContainer scrollable className="pt-16 pb-6">
      <View className="mb-8">
        <Text variant="title">Activity</Text>
        <Text variant="muted">Stay updated with agent actions and repository events.</Text>
      </View>

      <View className="flex-1">
        <EmptyState
          title="No recent activity"
          description="Notifications from your active agents and watched repositories will appear here."
          icon="bell.fill"
          className="min-h-[400px]"
        />
      </View>
    </ScreenContainer>
  );
}
