import { useLocalSearchParams, Stack, useRouter } from 'expo-router';
import { View } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { ScreenContainer } from '@/components/ui/screen-container';
import { Text } from '@/components/ui/text';
import { LoadingState } from '@/components/ui/loading-state';
import { ErrorState } from '@/components/ui/error-state';
import { DiffViewer } from '@/components/diff-viewer';
import { Button } from '@/components/ui/button';
import apiClient from '@/services/api-client';
import { Contribution } from '@/types/contribution';

export default function ImplementationScreen() {
  const { id, repositoryId } = useLocalSearchParams<{ id: string, repositoryId: string }>();
  const router = useRouter();

  const { data: contribution, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['contribution', id],
    queryFn: async () => {
      const { data } = await apiClient.get<Contribution>(`/api/v1/repositories/${repositoryId}/contributions/${id}`);
      return data;
    },
    enabled: !!id && !!repositoryId,
    refetchInterval: (query) => {
        const data = query.state.data as Contribution | undefined;
        // Keep polling until we have a diff or it fails
        return (data && !data.diff_summary && data.status !== 'failed') ? 3000 : false;
    }
  });

  if (isLoading) {
    return <LoadingState message="Retrieving implementation status..." />;
  }

  if (isError) {
    return (
      <ErrorState
        title="Status Check Failed"
        message={error instanceof Error ? error.message : 'Unknown error'}
        onRetry={() => refetch()}
      />
    );
  }

  if (!contribution) return null;

  return (
    <ScreenContainer scrollable className="py-6">
      <Stack.Screen options={{ title: 'Implementation Result', headerTitleAlign: 'center' }} />

      <View className="px-4 gap-6">
        <View className="items-center mb-2">
            <Text variant="title" className="text-2xl font-bold">Execution Review</Text>
            <Text variant="muted" className="text-center">Review the changes made by the autonomous agent.</Text>
        </View>

        {!contribution.diff_summary ? (
            <View className="py-12 items-center">
                {contribution.status === 'failed' ? (
                    <ErrorState
                        title="Autonomous Implementation Failed"
                        message="Loom was unable to make the tests pass after multiple attempts."
                        onRetry={() => router.back()}
                    />
                ) : (
                    <LoadingState message="Agent is currently applying changes and running tests..." />
                )}
            </View>
        ) : (
            <>
                <DiffViewer
                    diff={contribution.diff_summary.diff}
                    additions={contribution.diff_summary.additions}
                    deletions={contribution.diff_summary.deletions}
                    files={contribution.diff_summary.files}
                />

                <View className="mt-4 mb-12">
                    <Button
                        label="Prepare Pull Request"
                        size="lg"
                        onPress={() => console.log('Prepare PR')}
                    />
                </View>
            </>
        )}
      </View>
    </ScreenContainer>
  );
}
