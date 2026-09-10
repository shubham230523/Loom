import { useLocalSearchParams, useRouter, Stack } from 'expo-router';
import { View, Alert, Linking } from 'react-native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { SymbolView } from 'expo-symbols';
import { ScreenContainer } from '@/components/ui/screen-container';
import { Text } from '@/components/ui/text';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Divider } from '@/components/ui/divider';
import { LoadingState } from '@/components/ui/loading-state';
import { ErrorState } from '@/components/ui/error-state';
import { ContributionService } from '@/services/contribution.service';
import { useTheme } from '@/hooks/use-theme';
import { useAgentEvents } from '@/hooks/use-agent-events';
import { useSettingsStore } from '@/store/settings-store';

export default function SolutionPlanScreen() {
  const { id, repositoryId } = useLocalSearchParams<{ id: string, repositoryId: string }>();
  const theme = useTheme();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { isMockMode } = useSettingsStore();

  const { data: planResponse, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['solution-plan', id],
    queryFn: async () => {
      if (isMockMode && id === 'dummy-contrib-123') {
        // Return dummy data immediately for testing
        return {
          agent_run_id: 'dummy-run-456',
          plan: {
            id: 'dummy-plan-789',
            contribution_id: id,
            problem: 'The current user authentication loop fails to handle overlapping token refresh requests, leading to "invalid session" errors when multiple API calls trigger simultaneously.',
            root_cause: 'The `AuthService` lacks a synchronization primitive (lock) to ensure only one refresh operation occurs at a time. Secondary calls proceed with an expired token before the primary refresh completes.',
            relevant_files: [
              'src/services/auth.service.ts',
              'src/services/api-client.ts'
            ],
            relevant_symbols: ['refreshSession', 'apiClient.interceptors'],
            implementation_steps: [
              'Introduce a `isRefreshing` boolean flag in `AuthService`.',
              'Create a `refreshPromise` variable to store the in-flight refresh request.',
              'Update `refreshSession` to return the existing `refreshPromise` if one is active.',
              'Ensure the flag is reset in a `finally` block to prevent deadlocks.',
              'Update the Axios interceptor to queue pending requests while refreshing.'
            ],
            testing_strategy: 'Simulate 5 concurrent API calls with an expired token and verify only 1 refresh network request is sent to the backend.',
            risks: 'Potential memory leaks if queued requests are not properly released on refresh failure.',
            expected_diff_size: 'Small (~50 lines)',
            confidence: 0.98,
            status: 'pending'
          }
        } as any;
      }
      return ContributionService.generatePlan(repositoryId!, id!);
    },
    enabled: !!id && !!repositoryId,
  });

  const plan = planResponse?.plan;
  const { lastEvent } = useAgentEvents(planResponse?.agent_run_id);

  const approveMutation = useMutation({
    mutationFn: async (approved: boolean) => {
      if (id === 'dummy-contrib-123') {
        return {
          id: 'dummy-plan-789',
          status: approved ? 'approved' : 'rejected'
        } as any;
      }
      return ContributionService.approvePlan(repositoryId!, plan!.id, approved);
    },
    onSuccess: async (data) => {
      queryClient.setQueryData(['solution-plan', id], { ...planResponse, plan: data });
      if (data.status === 'approved') {
        if (isMockMode && id === 'dummy-contrib-123') {
          try {
            // Find a real repository ID to use for the mock PR
            // In a real scenario, this would be the ID of shubham230523/AIMastery
            const targetRepoId = 'b8c1121a-2b37-4679-b582-5147f29694e5';
            const targetOppId = '88afde2b-9822-4be3-95cf-a46f581b06b3';

            // Create a REAL contribution record first so we have a valid ID for the mock
            const realContribution = await ContributionService.start(targetRepoId, targetOppId);

            // Trigger the "Real-World Mock" (Clone, Edit, Push, PR)
            const mockResult = await ContributionService.executeMockImplementation(targetRepoId, realContribution.id);

            Alert.alert(
              'Success',
              `Real-world mock completed!\nPR created: ${mockResult.pr_url}`,
              [{ text: 'View PR', onPress: () => Linking.openURL(mockResult.pr_url) }]
            );

            router.replace({
              pathname: '/contribution/[id]/review',
              params: { id: realContribution.id, repositoryId: targetRepoId }
            });
          } catch (err) {
            console.error('Failed to execute real-world mock:', err);
            Alert.alert('Error', 'Real-world mock failed. Check backend logs.');
          }
          return;
        }

        try {
          await ContributionService.setupWorkspace(repositoryId!, id!);
          const implResponse = await ContributionService.executeImplementation(repositoryId!, id!);

          router.replace({
            pathname: '/contribution/[id]/activity',
            params: { id, repositoryId, agentRunId: implResponse.agent_run_id }
          });
        } catch (err) {
          console.error('Failed to trigger implementation:', err);
        }
      } else {
        router.back();
      }
    },
  });

  if (isLoading) {
    return <LoadingState message={lastEvent?.message || "Principal Engineer is designing the solution..."} />;
  }

  if (isError) {
    return (
      <ErrorState
        title="Planning Failed"
        message={error instanceof Error ? error.message : 'Unknown error'}
        onRetry={() => refetch()}
      />
    );
  }

  if (!plan) return null;

  return (
    <ScreenContainer scrollable className="py-6">
      <Stack.Screen options={{ title: 'Implementation Plan', headerTitleAlign: 'center' }} />

      <View className="px-4 gap-6">
        <View className="items-center mb-2">
            <View className="bg-primary/10 p-4 rounded-full mb-4">
                <SymbolView name="lightbulb.fill" size={32} tintColor={theme.primary} />
            </View>
            <Text variant="title" className="text-2xl font-bold text-center">Technical Blueprint</Text>
            <Text variant="muted" className="text-center">Vetted by SolutionPlannerAgent</Text>
        </View>

        <Card>
            <CardHeader>
                <CardTitle><Text variant="subtitle">Problem & Analysis</Text></CardTitle>
            </CardHeader>
            <CardContent className="gap-4">
                <View>
                    <Text weight="bold" variant="small" className="uppercase tracking-wider text-muted-foreground mb-1">Problem</Text>
                    <Text>{plan.problem}</Text>
                </View>
                <Divider />
                <View>
                    <Text weight="bold" variant="small" className="uppercase tracking-wider text-muted-foreground mb-1">Root Cause</Text>
                    <Text>{plan.root_cause}</Text>
                </View>
            </CardContent>
        </Card>

        <View className="gap-3">
            <Text weight="bold" className="text-lg px-1">Implementation Steps</Text>
            {plan.implementation_steps?.map((step: string, i: number) => (
                <Card key={i} className="bg-card">
                    <CardContent className="flex-row gap-3 py-3">
                        <View className="w-6 h-6 rounded-full bg-primary/20 items-center justify-center">
                            <Text variant="small" weight="bold" className="text-primary">{i + 1}</Text>
                        </View>
                        <Text className="flex-1">{step}</Text>
                    </CardContent>
                </Card>
            ))}
            {(!plan.implementation_steps || plan.implementation_steps.length === 0) && (
                <Text variant="small" className="text-muted-foreground italic px-1">No specific steps provided.</Text>
            )}
        </View>

        <Card>
            <CardHeader>
                <CardTitle><Text variant="subtitle">Affected Scope</Text></CardTitle>
            </CardHeader>
            <CardContent className="gap-4">
                <View>
                    <Text weight="bold" variant="small" className="uppercase tracking-wider text-muted-foreground mb-2">Files</Text>
                    <View className="flex-row flex-wrap gap-2">
                        {plan.relevant_files?.map((f: string) => (
                            <Badge key={f} label={f.split('/').pop() || f} variant="secondary" />
                        ))}
                    </View>
                    {(!plan.relevant_files || plan.relevant_files.length === 0) && (
                        <Text variant="small" className="text-muted-foreground italic">No specific files identified.</Text>
                    )}
                </View>
                <Divider />
                <View>
                    <Text weight="bold" variant="small" className="uppercase tracking-wider text-muted-foreground mb-1">Expected Diff</Text>
                    <Text weight="medium">{plan.expected_diff_size}</Text>
                </View>
            </CardContent>
        </Card>

        <Card>
            <CardHeader>
                <CardTitle><Text variant="subtitle">Verification & Risks</Text></CardTitle>
            </CardHeader>
            <CardContent className="gap-4">
                <View>
                    <Text weight="bold" variant="small" className="uppercase tracking-wider text-muted-foreground mb-1">Testing Strategy</Text>
                    <Text>{plan.testing_strategy}</Text>
                </View>
                <Divider />
                <View>
                    <Text weight="bold" variant="small" className="uppercase tracking-wider text-muted-foreground mb-1 text-destructive">Identified Risks</Text>
                    <Text>{plan.risks}</Text>
                </View>
            </CardContent>
        </Card>

        {plan.status === 'pending' ? (
            <View className="flex-row gap-4 mt-4 mb-12">
                <Button
                    variant="outline"
                    className="flex-1"
                    label="Reject"
                    onPress={() => approveMutation.mutate(false)}
                    disabled={approveMutation.isPending}
                />
                <Button
                    className="flex-1"
                    label="Approve & Implement"
                    onPress={() => approveMutation.mutate(true)}
                    disabled={approveMutation.isPending}
                />
            </View>
        ) : (
            <View className="items-center mt-4 mb-12">
                <Badge
                    variant={plan.status === 'approved' ? 'default' : 'destructive'}
                    label={plan.status.toUpperCase()}
                    className="px-8 py-2"
                />
                {plan.status === 'approved' && (
                    <Text variant="small" className="mt-4 text-muted-foreground">
                        Plan approved. Implementation in progress.
                    </Text>
                )}
            </View>
        )}
      </View>
    </ScreenContainer>
  );
}
