import { useLocalSearchParams, useRouter, Stack } from 'expo-router';
import { View } from 'react-native';
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

export default function SolutionPlanScreen() {
  const { id, repositoryId } = useLocalSearchParams<{ id: string, repositoryId: string }>();
  const theme = useTheme();
  const router = useRouter();
  const queryClient = useQueryClient();

  const { data: plan, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['solution-plan', id],
    queryFn: () => ContributionService.generatePlan(repositoryId!, id!),
    enabled: !!id && !!repositoryId,
  });

  const approveMutation = useMutation({
    mutationFn: (approved: boolean) => ContributionService.approvePlan(repositoryId!, plan!.id, approved),
    onSuccess: (data) => {
      queryClient.setQueryData(['solution-plan', id], data);
      if (data.status === 'approved') {
        console.log('Plan approved, starting implementation...');
      } else {
        router.back();
      }
    },
  });

  if (isLoading) {
    return <LoadingState message="Principal Engineer is designing the solution..." />;
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
            {plan.implementation_steps.map((step, i) => (
                <Card key={i} className="bg-card">
                    <CardContent className="flex-row gap-3 py-3">
                        <View className="w-6 h-6 rounded-full bg-primary/20 items-center justify-center">
                            <Text variant="small" weight="bold" className="text-primary">{i + 1}</Text>
                        </View>
                        <Text className="flex-1">{step}</Text>
                    </CardContent>
                </Card>
            ))}
        </View>

        <Card>
            <CardHeader>
                <CardTitle><Text variant="subtitle">Affected Scope</Text></CardTitle>
            </CardHeader>
            <CardContent className="gap-4">
                <View>
                    <Text weight="bold" variant="small" className="uppercase tracking-wider text-muted-foreground mb-2">Files</Text>
                    <View className="flex-row flex-wrap gap-2">
                        {plan.relevant_files.map(f => (
                            <Badge key={f} label={f.split('/').pop() || f} variant="secondary" />
                        ))}
                    </View>
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
