import { useLocalSearchParams, Stack } from 'expo-router';
import { View, Image, Linking } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { SymbolView } from 'expo-symbols';
import { ScreenContainer } from '@/components/ui/screen-container';
import { Text } from '@/components/ui/text';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Divider } from '@/components/ui/divider';
import { LoadingState } from '@/components/ui/loading-state';
import { ErrorState } from '@/components/ui/error-state';
import { RepositoryService } from '@/services/repository.service';
import { useTheme } from '@/hooks/use-theme';

export default function RepositoryDetailsScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const theme = useTheme();

  const { data: repo, isLoading, error, isError, refetch } = useQuery({
    queryKey: ['repository', id],
    queryFn: () => RepositoryService.getById(Number(id)),
    enabled: !!id,
  });

  const handleOpenGitHub = () => {
    if (repo?.html_url) {
      Linking.openURL(repo.html_url);
    }
  };

  const handleAnalyze = () => {
    console.log('Analyze Repository requested for:', id);
    // AI analysis integration will go here
  };

  if (isLoading) {
    return <LoadingState message="Fetching repository details..." />;
  }

  if (isError) {
    return (
      <ErrorState
        title="Failed to load repository"
        message={error instanceof Error ? error.message : 'Unknown error'}
        onRetry={() => refetch()}
      />
    );
  }

  if (!repo) return null;

  return (
    <ScreenContainer scrollable className="py-6">
      <Stack.Screen options={{ title: repo.name, headerTitleAlign: 'center' }} />

      {/* Header Section */}
      <View className="items-center mb-8">
        <View className="w-20 h-20 rounded-2xl bg-muted items-center justify-center mb-4 border border-border overflow-hidden">
          <Image
            source={{ uri: repo.owner.avatar_url }}
            className="w-full h-full"
            resizeMode="cover"
          />
        </View>
        <Text variant="title" className="text-3xl font-bold mb-1 text-center">{repo.name}</Text>
        <Text variant="muted" className="text-lg">by {repo.owner.login}</Text>
      </View>

      <View className="gap-6">
        {/* Actions */}
        <View className="flex-row gap-4">
          <Button
            className="flex-1"
            label="Analyze Repository"
            onPress={handleAnalyze}
          />
          <Button
            variant="outline"
            className="px-4"
            onPress={handleOpenGitHub}
          >
            <SymbolView name="link" size={20} tintColor={theme.text} />
          </Button>
        </View>

        {/* About */}
        <Card>
          <CardHeader>
            <CardTitle><Text variant="subtitle">About</Text></CardTitle>
          </CardHeader>
          <CardContent>
            <Text className="text-muted-foreground leading-6">
              {repo.description || 'No description provided.'}
            </Text>
          </CardContent>
        </Card>

        {/* Info Grid */}
        <View className="flex-row gap-4 flex-wrap">
          <InfoCard
            label="Language"
            value={repo.language || 'Unknown'}
            icon="curlybraces"
          />
          <InfoCard
            label="Stars"
            value={repo.stargazers_count.toLocaleString()}
            icon="star.fill"
            iconColor="#EAB308"
          />
          <InfoCard
            label="Forks"
            value={repo.forks_count.toLocaleString()}
            icon="arrow.branch"
          />
          <InfoCard
            label="Branch"
            value={repo.default_branch}
            icon="checklist"
          />
        </View>

        {/* Activity Section Placeholder */}
        <Card>
          <CardHeader>
            <CardTitle><Text variant="subtitle">Activity</Text></CardTitle>
          </CardHeader>
          <CardContent>
            <View className="flex-row items-center justify-between py-2">
              <Text variant="small" className="text-muted-foreground">Last updated</Text>
              <Text variant="small" weight="medium">
                {new Date(repo.updated_at).toLocaleDateString()}
              </Text>
            </View>
            <Divider className="my-2" />
            <Text variant="small" className="text-muted-foreground italic">
              Detailed contribution and agent activity metrics will appear here after analysis.
            </Text>
          </CardContent>
        </Card>
      </View>
    </ScreenContainer>
  );
}

function InfoCard({ label, value, icon, iconColor }: { label: string; value: string; icon: any; iconColor?: string }) {
  const theme = useTheme();
  return (
    <Card className="flex-1 min-w-[140px] items-center py-4">
      <SymbolView name={icon} size={20} tintColor={iconColor || theme.textSecondary} className="mb-2" />
      <Text variant="small" className="text-muted-foreground mb-1">{label}</Text>
      <Text weight="bold" className="text-center">{value}</Text>
    </Card>
  );
}
