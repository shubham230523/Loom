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

export default function PullRequestReviewScreen() {
  const { id, repositoryId } = useLocalSearchParams<{ id: string, repositoryId: string }>();

  // 1. Fetch contribution details
  const { data: contribution, isLoading: isContrLoading, isError: isContrError, error: contrError, refetch: refetchContr } = useQuery({
    queryKey: ['contribution-review', id],
    queryFn: () => ContributionService.getDetails(repositoryId!, id!),
    enabled: !!id && !!repositoryId,
  });

  // 2. Fetch final validation result
  const { data: validation, isLoading: isValLoading } = useQuery({
    queryKey: ['contribution-validation', id],
    queryFn: () => ContributionService.validate(repositoryId!, id!),
    enabled: !!id && !!repositoryId,
  });

  // 3. Push & PR Mutation
  const prMutation = useMutation({
    mutationFn: async () => {
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
        <Card className={validation?.is_valid ? "bg-green-500/5 border-green-500/20" : "bg-yellow-500/5 border-yellow-500/20"}>
            <CardContent className="flex-row items-center gap-6 py-6">
                <View className="w-16 h-16 rounded-full bg-background border-4 border-primary items-center justify-center">
                    <Text weight="bold" className="text-xl">{validation?.score || 0}</Text>
                </View>
                <View className="flex-1">
                    <Text weight="bold" className="text-lg">Readiness Score</Text>
                    <Text variant="small" className="text-muted-foreground">{validation?.summary}</Text>
                </View>
                {validation?.is_valid && (
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
                    value={latestTest?.status?.toUpperCase() || 'NONE'}
                    icon={latestTest?.status === 'success' ? "checkmark.circle.fill" : "xmark.circle.fill"}
                    color={latestTest?.status === 'success' ? "#22C55E" : "#EF4444"}
                />
                <EvidenceCard
                    label="Code Review"
                    value={latestReview?.decision || 'NONE'}
                    icon={latestReview?.decision === 'APPROVE' ? "shield.fill" : "shield.slash.fill"}
                    color={latestReview?.decision === 'APPROVE' ? "#22C55E" : "#EAB308"}
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
        {validation?.issues && validation.issues.length > 0 && (
            <View className="gap-2">
                <Text weight="bold" className="text-lg px-1 text-destructive">Remaining Concerns</Text>
                {validation.issues.map((issue: any, i: number) => (
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
                disabled={!validation?.is_valid}
                className={!validation?.is_valid ? "opacity-50" : ""}
            />
            {prMutation.isError && (
                <Text variant="small" className="text-destructive text-center mt-3">
                   Sync Failed: {(prMutation.error as any)?.message || 'Check your connection.'}
                </Text>
            )}
            {!validation?.is_valid && (
                <Text variant="small" className="text-destructive text-center mt-3 font-medium">
                    Please resolve critical validation issues before submitting.
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
