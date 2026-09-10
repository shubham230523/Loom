import { useLocalSearchParams, Stack } from 'expo-router';
import { View, Linking } from 'react-native';
import { useQuery, useMutation } from '@tanstack/react-query';
import { SymbolView } from 'expo-symbols';
import { ScreenContainer } from '@/components/ui/screen-container';
import { Text } from '@/components/ui/text';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Divider } from '@/components/ui/divider';
import { LoadingState } from '@/components/ui/loading-state';
import { ErrorState } from '@/components/ui/error-state';
import { DiffViewer } from '@/components/diff-viewer';
import { ContributionService } from '@/services/contribution.service';

import { useSettingsStore } from '@/store/settings-store';

export default function PullRequestReviewScreen() {
  const { id, repositoryId } = useLocalSearchParams<{ id: string, repositoryId: string }>();
  const { isMockMode } = useSettingsStore();

  // 1. Fetch contribution details
  const { data: contribution, isLoading: isContrLoading, isError: isContrError, error: contrError, refetch: refetchContr } = useQuery({
    queryKey: ['contribution-review', id],
    queryFn: async () => {
      if (id === 'dummy-contrib-123') {
        return {
          id,
          repository_id: repositoryId,
          branch_name: 'ai/dummy-refactor-auth-loop',
          repository: {
            full_name: 'shubham230523/Loom',
            default_branch: 'master'
          },
          status: 'completed',
          code_reviews: [{
            decision: 'APPROVE',
            summary: 'The implementation correctly introduces a mutex lock around the token refresh logic. Axios interceptors now properly queue outgoing requests during an active refresh cycle.',
            confidence: 0.96
          }],
          test_runs: [{
            status: 'success',
            command: 'npm test src/services/auth.service.test.ts',
            duration: 12.4
          }],
          diff_summary: {
            additions: 42,
            deletions: 12,
            files: 2,
            diff: `--- a/src/services/auth.service.ts
+++ b/src/services/auth.service.ts
@@ -10,6 +10,8 @@
+  private isRefreshing = false;
+  private refreshPromise: Promise<string> | null = null;
+
   async refreshSession(): Promise<string> {
-    return await this.api.post('/auth/refresh');
+    if (this.isRefreshing) return this.refreshPromise!;
+    this.isRefreshing = true;
+    this.refreshPromise = this.api.post('/auth/refresh').finally(() => {
+      this.isRefreshing = false;
+    });
+    return this.refreshPromise;
   }`
          }
        } as any;
      }
      return ContributionService.getDetails(repositoryId!, id!);
    },
    enabled: !!id && !!repositoryId,
  });

  // 2. Fetch final validation result
  const { data: validation, isLoading: isValLoading } = useQuery({
    queryKey: ['contribution-validation', id],
    queryFn: async () => {
      if (id === 'dummy-contrib-123') {
        return {
          is_valid: true,
          score: 98,
          summary: 'Contribution adheres to project standards and passes all sanity checks.',
          issues: []
        } as any;
      }
      return ContributionService.validate(repositoryId!, id!);
    },
    enabled: !!id && !!repositoryId,
  });

  // 3. Push & PR Mutation
  const prMutation = useMutation({
    mutationFn: async () => {
        if (id === 'dummy-contrib-123') {
          // Simulate network delay
          await new Promise(resolve => setTimeout(resolve, 2000));
          return {
            url: 'https://github.com/shubham230523/Loom/pull/42'
          } as any;
        }
        await ContributionService.push(repositoryId!, id!);
        return await ContributionService.createPullRequest(repositoryId!, id!);
    },
    onSuccess: (data) => {
      console.log('Successfully created PR:', data.url);
      Linking.openURL(data.url);
    }
  });

  const handleCreatePR = () => {
    prMutation.mutate();
  };

  if (isContrLoading || isValLoading) {
    return <LoadingState message="Aggregating contribution evidence..." />;
  }

  if (prMutation.isPending) {
    return <LoadingState message="Synchronizing with GitHub..." />;
  }

  if (isContrError) {
    return (
      <ErrorState
        title="Load Failed"
        message={contrError instanceof Error ? contrError.message : 'Unknown error'}
        onRetry={() => refetchContr()}
      />
    );
  }

  if (!contribution) return null;

  const latestReview = contribution.code_reviews?.[contribution.code_reviews.length - 1];
  const latestTest = contribution.test_runs?.[contribution.test_runs.length - 1];

  return (
    <ScreenContainer scrollable className="py-6">
      <Stack.Screen options={{ title: 'Final Approval', headerTitleAlign: 'center' }} />

      <View className="px-4 gap-6">
        <View className="items-center">
            <Text variant="title" className="text-2xl font-bold">Contribution Ready</Text>
            <Text variant="muted" className="text-center">Final review before remote synchronization.</Text>
        </View>

        {/* Validation Score Header */}
        <Card className={(validation?.is_valid || isMockMode) ? "bg-green-500/5 border-green-500/20" : "bg-yellow-500/5 border-yellow-500/20"}>
            <CardContent className="flex-row items-center gap-6 py-6">
                <View className="w-16 h-16 rounded-full bg-background border-4 border-primary items-center justify-center">
                    <Text weight="bold" className="text-xl">{isMockMode ? 100 : (validation?.score || 0)}</Text>
                </View>
                <View className="flex-1">
                    <Text weight="bold" className="text-lg">Readiness Score</Text>
                    <Text variant="small" className="text-muted-foreground">
                        {isMockMode ? "Mock Mode: Automatic 100% readiness for demonstration." : validation?.summary}
                    </Text>
                </View>
                {(validation?.is_valid || isMockMode) && (
                    <SymbolView name="checkmark.seal.fill" size={32} tintColor="#22C55E" />
                )}
            </CardContent>
        </Card>

        {/* Repository Context */}
        <View className="gap-2">
            <Text weight="bold" className="text-lg px-1">Context</Text>
            <Card>
                <CardContent className="gap-3 py-4">
                    <View className="flex-row items-center justify-between">
                        <Text variant="small" className="text-muted-foreground">Repository</Text>
                        <Text weight="bold">{(contribution as any).repository?.full_name}</Text>
                    </View>
                    <Divider />
                    <View className="flex-row items-center justify-between">
                        <Text variant="small" className="text-muted-foreground">Target Branch</Text>
                        <Badge label={(contribution as any).repository?.default_branch || 'main'} variant="secondary" />
                    </View>
                    <Divider />
                    <View className="flex-row items-center justify-between">
                        <Text variant="small" className="text-muted-foreground">Contribution Branch</Text>
                        <Text className="font-mono text-xs">{contribution.branch_name}</Text>
                    </View>
                </CardContent>
            </Card>
        </View>

        {/* Verification Evidence */}
        <View className="gap-2">
            <Text weight="bold" className="text-lg px-1">Verification Evidence</Text>
            <View className="flex-row gap-4">
                <EvidenceCard
                    label="Test Status"
                    value={isMockMode ? "SUCCESS" : (latestTest?.status?.toUpperCase() || 'NONE')}
                    icon={(isMockMode || latestTest?.status === 'success') ? "checkmark.circle.fill" : "xmark.circle.fill"}
                    color={(isMockMode || latestTest?.status === 'success') ? "#22C55E" : "#EF4444"}
                />
                <EvidenceCard
                    label="Code Review"
                    value={isMockMode ? "APPROVE" : (latestReview?.decision || 'NONE')}
                    icon={(isMockMode || latestReview?.decision === 'APPROVE') ? "shield.fill" : "shield.slash.fill"}
                    color={(isMockMode || latestReview?.decision === 'APPROVE') ? "#22C55E" : "#EAB308"}
                />
            </View>
        </View>

        {/* Code Review Summary */}
        {latestReview && (
            <Card>
                <CardHeader>
                    <CardTitle><Text variant="subtitle">Agent Audit Findings</Text></CardTitle>
                </CardHeader>
                <CardContent>
                    <Text className="text-muted-foreground italic mb-2">"{latestReview.summary}"</Text>
                    <Text variant="small" weight="medium">Confidence: {Math.round(latestReview.confidence * 100)}%</Text>
                </CardContent>
            </Card>
        )}

        {/* Changes Summary */}
        {contribution.diff_summary && (
            <DiffViewer
                diff={contribution.diff_summary.diff}
                additions={contribution.diff_summary.additions}
                deletions={contribution.diff_summary.deletions}
                files={contribution.diff_summary.files}
            />
        )}

        {/* Validation Issues List */}
        {validation?.issues && validation.issues.length > 0 && !isMockMode && (
            <View className="gap-2">
                <Text weight="bold" className="text-lg px-1 text-destructive">Remaining Concerns</Text>
                {validation.issues?.map((issue: any, i: number) => (
                    <Card key={i} className="bg-destructive/5 border-destructive/10">
                        <CardContent className="flex-row gap-3 py-3">
                            <SymbolView
                                name={issue.severity === 'critical' ? "exclamationmark.octagon.fill" : "exclamationmark.triangle.fill"}
                                size={18}
                                tintColor="#EF4444"
                            />
                            <View className="flex-1">
                                <Text weight="bold" variant="small" className="text-destructive uppercase">{issue.category}</Text>
                                <Text variant="small">{issue.message}</Text>
                            </View>
                        </CardContent>
                    </Card>
                ))}
            </View>
        )}

        {/* Final Submission */}
        <View className="mt-4 mb-12">
            <Button
                label="Create Pull Request"
                size="lg"
                onPress={handleCreatePR}
                disabled={!isMockMode && !validation?.is_valid}
                className={(!isMockMode && !validation?.is_valid) ? "opacity-50" : ""}
            />
            {prMutation.isError && (
                <Text variant="small" className="text-destructive text-center mt-3">
                   Sync Failed: {(prMutation.error as any)?.message || 'Check your connection.'}
                </Text>
            )}
            {!isMockMode && !validation?.is_valid && (
                <Text variant="small" className="text-destructive text-center mt-3 font-medium">
                    Please resolve critical validation issues before submitting.
                </Text>
            )}
            {isMockMode && (
                <Text variant="small" className="text-primary text-center mt-3 font-medium">
                    Mock Mode active: Validation constraints bypassed for demonstration.
                </Text>
            )}
        </View>
      </View>
    </ScreenContainer>
  );
}

function EvidenceCard({ label, value, icon, color }: { label: string, value: string, icon: any, color: string }) {
    return (
        <Card className="flex-1 items-center py-4">
            <SymbolView name={icon} size={24} tintColor={color} className="mb-2" />
            <Text variant="small" className="text-muted-foreground mb-1">{label}</Text>
            <Text weight="bold" style={{ color }}>{value}</Text>
        </Card>
    );
}
