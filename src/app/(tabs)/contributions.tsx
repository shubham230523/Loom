import { View } from 'react-native';
import { ScreenContainer } from '@/components/ui/screen-container';
import { Text } from '@/components/ui/text';
import { EmptyState } from '@/components/ui/empty-state';
import { Button } from '@/components/ui/button';
import { useRouter } from 'expo-router';

export default function ContributionsScreen() {
  const router = useRouter();

  return (
    <ScreenContainer scrollable className="py-6">
      <View className="mb-8">
        <Text variant="title">Contributions</Text>
        <Text variant="muted">Track and manage your impact on the community.</Text>
      </View>

      <View className="flex-1">
        <EmptyState
          title="No contributions yet"
          description="Your code contributions, documentation updates, and agent-led improvements will appear here."
          icon="plus.square.fill"
          action={
            <Button
              label="Explore Projects"
              onPress={() => router.push('/(tabs)/discover')}
            />
          }
          className="min-h-[400px]"
        />
      </View>
    </ScreenContainer>
  );
}
