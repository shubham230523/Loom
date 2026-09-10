import { useLocalSearchParams, Stack, useRouter } from 'expo-router';
import { View, Image, Linking, Pressable, Alert } from 'react-native';
import { useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
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
import { OpportunityCard } from '@/components/opportunity-card';
import { LoadingIndicator } from '@/components/ui/loading-indicator';
import { useSettingsStore } from '@/store/settings-store';

const DUMMY_OPPORTUNITY_ID = 'dummy-opp-123';

export default function RepositoryDetailsScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { isMockMode } = useSettingsStore();

  // 1. Fetch Repository Metadata
  const { data: repo, isLoading: isRepoLoading, isError: isRepoError, error: repoError, refetch: refetchRepo } = useQuery({
    queryKey: ['repository', id],
    queryFn: () => RepositoryService.getById(id!),
    enabled: !!id,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data?.is_imported) return false;

      const isIndexing = data.indexing_status === 'in_progress' || data.indexing_status === 'not_started';
      const isDiscovering = data.discovery_status === 'discovering';

      // Poll if indexing or discovery is in progress
      return isIndexing || isDiscovering ? 3000 : false;
    }
  });

  const loomId = repo?.loom_id; // This will be the UUID if imported

  // 2. Fetch Opportunities (only if imported)
  const { data: opportunitiesResponse, isLoading: isOppsLoading, refetch: refetchOpps } = useQuery({
    queryKey: ['opportunities', loomId],
    queryFn: () => OpportunityService.list(loomId!),
    enabled: !!loomId,
  });

  // Inject dummy opportunity for testing ONLY if in mock mode
  const opportunities = opportunitiesResponse ? [
    ...opportunitiesResponse,
    ...(isMockMode ? [{
      id: DUMMY_OPPORTUNITY_ID,
      repository_id: loomId || '',
      title: '[TEST] Refactor User Authentication Loop',
      description: 'The current auth loop has a race condition during token refresh. This task implements a lock mechanism to prevent multiple simultaneous refreshes.',
      type: 'refactor',
      impact: 'High',
      difficulty: 'Intermediate',
      confidence: 0.95,
      score: 85,
      status: 'pending',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    } as any] : [])
  ] : (isMockMode && loomId ? [{
    id: DUMMY_OPPORTUNITY_ID,
    repository_id: loomId,
    title: '[TEST] Refactor User Authentication Loop',
    description: 'The current auth loop has a race condition during token refresh. This task implements a lock mechanism to prevent multiple simultaneous refreshes.',
    type: 'refactor',
    impact: 'High',
    difficulty: 'Intermediate',
    confidence: 0.95,
    score: 85,
    status: 'pending',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  } as any] : null);

  // Watch for discovery completion to refetch opportunities
  useEffect(() => {
    if (repo?.discovery_status === 'completed') {
      refetchOpps();
    }
  }, [repo?.discovery_status]);

  // 3. Discovery Mutation
  const discoverMutation = useMutation({
    mutationFn: () => OpportunityService.discover(loomId!),
    onSuccess: (data) => {
      if (data.status === 'indexing' || data.status === 'discovering') {
        // Trigger a refetch to start polling for status
        refetchRepo();
      } else {
        queryClient.invalidateQueries({ queryKey: ['opportunities', loomId] });
      }
    },
    onError: (error: any) => {
      console.error('Discovery failed:', error);
      Alert.alert('Discovery Failed', error.message || 'An unexpected error occurred during opportunity discovery.');
    }
  });

  // 4. Scoring Mutation
  const scoreMutation = useMutation({
    mutationFn: (oppId: string) => OpportunityService.score(loomId!, oppId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['opportunities', loomId] });
    },
    onError: (error: any) => {
      console.error('Scoring failed:', error);
      Alert.alert('Analysis Failed', error.message || 'An unexpected error occurred during opportunity analysis.');
    }
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
      if (!loomId) {
        return;
      }
      discoverMutation.mutate();
    }
  };

  const handleAnalyzeOpportunity = (oppId: string) => {
    scoreMutation.mutate(oppId);
  };

  const handleStartContribution = async (oppId: string) => {
    if (isMockMode && oppId === DUMMY_OPPORTUNITY_ID) {
      router.push({
        pathname: '/contribution/[id]/plan',
        params: { id: 'dummy-contrib-123', repositoryId: loomId! }
      });
      return;
    }

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
      <Stack.Screen options={{ title: repo?.name || 'Repository', headerShown: false }} />

      {/* Custom Header with Back Button */}
      <View className="flex-row items-center px-4 mb-6">
        <Pressable
          onPress={() => {
            router.back();
          }}
          className="w-10 h-10 items-center justify-center rounded-full bg-slate-200 active:bg-slate-300"
        >
          <Text className="text-slate-900 text-2xl font-bold leading-none">←</Text>
        </Pressable>
        <View className="flex-1 items-center mr-10">
          <Text weight="bold" className="text-lg">{repo?.name}</Text>
        </View>
      </View>

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
            <View className="items-center justify-center">
              <Text className="text-4xl">👤</Text>
            </View>
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
            loading={
              initializeMutation.isPending ||
              discoverMutation.isPending ||
              repo.indexing_status === 'in_progress' ||
              repo.discovery_status === 'discovering'
            }
            label={
              repo.indexing_status === 'failed'
                ? "Analysis Failed - Retry"
                : repo.discovery_status === 'failed'
                  ? "Discovery Failed - Retry"
                  : repo.indexing_status === 'in_progress'
                    ? "Analyzing Codebase..."
                    : repo.discovery_status === 'discovering'
                      ? "Discovering..."
                      : initializeMutation.isPending
                        ? "Adding to Loom..."
                        : discoverMutation.isPending
                          ? "Starting Discovery..."
                          : repo.is_imported
                            ? "Discover Opportunities"
                            : "Add to Loom"
            }
            onPress={handleDiscover}
            disabled={
              discoverMutation.isPending ||
              initializeMutation.isPending ||
              repo.indexing_status === 'in_progress' ||
              repo.discovery_status === 'discovering'
            }
          />
          <Button
            variant="outline"
            className="px-4"
            onPress={handleOpenGitHub}
          >
            <Text className="text-xl">🔗</Text>
          </Button>
        </View>

        {repo.discovery_error && (
          <View className="bg-destructive/10 p-4 rounded-xl border border-destructive/20">
            <Text className="text-destructive text-sm font-medium mb-1">Discovery Error</Text>
            <Text variant="small" className="text-destructive/80">{repo.discovery_error}</Text>
          </View>
        )}

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
                <Text>⭐</Text>
                <Text variant="small" className="text-muted-foreground">{(repo?.stargazers_count || 0).toLocaleString()}</Text>
              </View>
              <View className="flex-row items-center gap-1">
                <Text>🍴</Text>
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
              <Text className="text-3xl mb-4">✨</Text>
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
                isAnalyzing={scoreMutation.isPending && scoreMutation.variables === opp.id}
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
