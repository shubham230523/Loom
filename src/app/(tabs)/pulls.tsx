import { View } from 'react-native';
import { ScreenContainer } from '@/components/ui/screen-container';
import { Text } from '@/components/ui/text';
import { EmptyState } from '@/components/ui/empty-state';

export default function PullsScreen() {
  return (
    <ScreenContainer scrollable className="py-6">
      <View className="mb-8">
        <Text variant="title">Pull Requests</Text>
        <Text variant="muted">Collaborate on code reviews and track proposed changes.</Text>
      </View>

      <View className="flex-1">
        <EmptyState
          title="No open pull requests"
          description="Pull requests from your connected repositories will appear here for review."
          icon="arrow.triangle.pull"
          className="min-h-[400px]"
        />
      </View>
    </ScreenContainer>
  );
}
