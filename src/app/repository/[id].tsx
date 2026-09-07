import { useLocalSearchParams, Stack, useRouter } from 'expo-router';
import { View, Image, Linking } from 'react-native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { SymbolView } from 'expo-symbols';
import { ScreenContainer } from '@/components/ui/screen-container';
import { Text } from '@/components/ui/text';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { LoadingState } from '@/components/ui/loading-state';
import { ErrorState } from '@/components/ui/error-state';
import { RepositoryService } from '@/services/repository.service';
import { OpportunityService } from '@/services/opportunity.service';
import { ContributionService } from '@/services/contribution.service';
import { useTheme } from '@/hooks/use-theme';
import { OpportunityCard } from '@/components/opportunity-card';
import { LoadingIndicator } from '@/components/ui/loading-indicator';

export default function RepositoryDetailsScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const theme = useTheme();
  const router = useRouter();
  const queryClient = useQueryClient();

  // 1. Fetch Repository Metadata
  const { data: repo, isLoading: isRepoLoading, isError: isRepoError, error: repoError, refetch: refetchRepo } = useQuery({
    queryKey: ['repository', id],
    queryFn: () => RepositoryService.getById(id!),
    enabled: !!id,
  });

  const loomId = repo?.loom_id; // This will be the UUID if imported

  // 2. Fetch Opportunities (only if imported)
  const { data: opportunities, isLoading: isOppsLoading } = useQuery({
    queryKey: ['opportunities', loomId],
    queryFn: () => OpportunityService.list(loomId!),
    enabled: !!loomId,
  });

  // 3. Discovery Mutation
  const discoverMutation = useMutation({
    mutationFn: () => OpportunityService.discover(loomId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['opportunities', loomId] });
    },
  });

  // 4. Scoring Mutation
  const scoreMutation = useMutation({
    mutationFn: (oppId: string) => OpportunityService.score(loomId!, oppId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['opportunities', loomId] });
    },
  });

  // 5. Initialize Mutation
  const initializeMutation = useMutation({
    mutationFn: () => RepositoryService.initialize(repo!.id),
    onSuccess: (data) => {
      queryClient.setQueryData(['repository', id], { ...repo, ...data, is_imported: true });
      queryClient.invalidateQueries({ queryKey: ['repository', id] });
    },
  });

  const handleOpenGitHub = () => {
    if (repo?.html_url) {
      Linking.openURL(repo.html_url);
    }
  };

  const handleDiscover = () => {
    if (!repo?.is_imported) {
      initializeMutation.mutate();
    } else {
      discoverMutation.mutate();
    }
  };

  const handleAnalyzeOpportunity = (oppId: string) => {
    scoreMutation.mutate(oppId);
  };

  const handleStartContribution = async (oppId: string) => {
    try {
      const contribution = await ContributionService.start(loomId!, oppId);
      router.push({
        pathname: '/contribution/[id]/plan',
        params: { id: contribution.id, repositoryId: loomId! }
      });
    } catch (error) {
      console.error('Failed to start contribution:', error);
    }
  };

  if (isRepoLoading) {
    return <LoadingState message="Fetching repository details..." />;
  }

  if (isRepoError) {
    return (
      <ErrorState
        title="Failed to load repository"
        message={repoError instanceof Error ? repoError.message : 'Unknown error'}
        onRetry={() => refetchRepo()}
      />
    );
  }

  if (!repo) return null;

  return (
    <ScreenContainer scrollable className="py-6">
      <Stack.Screen options={{ title: repo.name, headerTitleAlign: 'center' }} />

      {/* Header Section */}
      <View className="items-center mb-8 px-4">
        <View className="w-20 h-20 rounded-2xl bg-muted items-center justify-center mb-4 border border-border overflow-hidden">
          {repo?.owner?.avatar_url ? (
            <Image
              source={{ uri: repo.owner.avatar_url }}
              className="w-full h-full"
              resizeMode="cover"
            />
          ) : (
            <SymbolView name="person.circle.fill" size={40} tintColor={theme.textSecondary} />
          )}
        </View>
        <Text variant="title" className="text-3xl font-bold mb-1 text-center">{repo?.name || 'Loading...'}</Text>
        <Text variant="muted" className="text-lg">by {repo?.owner?.login || '...'}</Text>
      </View>

      <View className="gap-6 px-4">
        {/* Main Actions */}
        <View className="flex-row gap-4">
          <Button
            className="flex-1"
            variant={repo.is_imported ? "default" : "secondary"}
            label={
              initializeMutation.isPending
                ? "Adding to Loom..."
                : discoverMutation.isPending
                  ? "Discovering..."
                  : repo.is_imported
                    ? "Discover Opportunities"
                    : "Add to Loom"
            }
            onPress={handleDiscover}
            disabled={discoverMutation.isPending || initializeMutation.isPending}
          />
          <Button
            variant="outline"
            className="px-4"
            onPress={handleOpenGitHub}
          >
            <SymbolView name="link" size={20} tintColor={theme.text} />
          </Button>
        </View>

        {/* Technical Summary */}
        <Card>
          <CardHeader>
            <CardTitle><Text variant="subtitle">Technical Context</Text></CardTitle>
          </CardHeader>
          <CardContent>
            <Text className="text-muted-foreground leading-6 mb-4">
              {repo?.description || 'No description provided.'}
            </Text>
            <View className="flex-row gap-4 flex-wrap">
              <Badge label={repo?.language || 'Unknown'} variant="secondary" />
              <View className="flex-row items-center gap-1">
                <SymbolView name="star.fill" size={12} tintColor="#EAB308" />
                <Text variant="small" className="text-muted-foreground">{(repo?.stargazers_count || 0).toLocaleString()}</Text>
              </View>
              <View className="flex-row items-center gap-1">
                <SymbolView name="arrow.branch" size={12} tintColor={theme.textSecondary} />
                <Text variant="small" className="text-muted-foreground">{(repo?.forks_count || 0).toLocaleString()}</Text>
              </View>
            </View>
          </CardContent>
        </Card>

        {/* Opportunities List */}
        <View>
          <View className="flex-row items-center justify-between mb-4">
            <Text variant="subtitle" className="text-xl font-bold">Contribution Backlog</Text>
            {isOppsLoading && <LoadingIndicator size="small" />}
          </View>

          {!opportunities || opportunities.length === 0 ? (
            <Card className="items-center py-12 px-6">
              <SymbolView name="sparkles" size={32} tintColor={theme.textSecondary} className="mb-4" />
              <Text weight="medium" className="mb-2">No opportunities yet</Text>
              <Text variant="small" className="text-muted-foreground text-center">
                Tap 'Discover Opportunities' to let Loom analyze this project and find tasks.
              </Text>
            </Card>
          ) : (
            opportunities.map((opp) => (
              <OpportunityCard
                key={opp.id}
                opportunity={opp}
                onAnalyze={handleAnalyzeOpportunity}
                onStart={handleStartContribution}
              />
            ))
          )}
        </View>
      </View>
    </ScreenContainer>
  );
}
