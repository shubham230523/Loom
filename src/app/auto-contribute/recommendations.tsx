import { useLocalSearchParams, useRouter } from 'expo-router';
import { View, FlatList } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { ScreenContainer } from '@/components/ui/screen-container';
import { Text } from '@/components/ui/text';
import { LoadingState } from '@/components/ui/loading-state';
import { ErrorState } from '@/components/ui/error-state';
import { EmptyState } from '@/components/ui/empty-state';
import { OpportunityCard } from '@/components/opportunity-card';
import apiClient from '@/services/api-client';
import { Opportunity } from '@/types/opportunity';

interface Recommendation {
  opportunity: Opportunity;
  repository: {
    id: string;
    full_name: string;
    language: string;
  };
}

export default function RecommendationsScreen() {
  const { types, difficulties, languages } = useLocalSearchParams<{ types: string, difficulties: string, languages: string }>();
  const router = useRouter();

  const { data, isLoading, error, isError, refetch } = useQuery({
    queryKey: ['recommendations', types, difficulties, languages],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (types) types.split(',').forEach(t => params.append('types', t));
      if (difficulties) difficulties.split(',').forEach(d => params.append('difficulties', d));
      if (languages) languages.split(',').forEach(l => params.append('languages', l));

      const { data } = await apiClient.get<Recommendation[]>('/api/v1/recommendations/', { params });
      return data;
    }
  });

  if (isLoading) {
    return <LoadingState message="Loom is finding the perfect match for you..." />;
  }

  if (isError) {
    return (
      <ErrorState
        title="Matching Failed"
        message={error instanceof Error ? error.message : 'Unknown error'}
        onRetry={() => refetch()}
      />
    );
  }

  return (
    <ScreenContainer className="py-6">
      <View className="mb-6">
        <Text variant="title">Recommended Work</Text>
        <Text variant="muted">Based on your selected preferences and tech stack.</Text>
      </View>

      {!data || data.length === 0 ? (
        <EmptyState
          title="No matches found"
          description="Try broadening your preferences or selecting different languages."
          icon="sparkles"
        />
      ) : (
        <FlatList
          data={data}
          keyExtractor={(item) => item.opportunity.id}
          renderItem={({ item }) => (
            <View className="mb-2">
               <View className="flex-row items-center gap-2 mb-1 px-1">
                 <Text variant="small" weight="bold" className="text-primary">{item.repository.full_name}</Text>
                 <Text variant="small" className="text-muted-foreground">•</Text>
                 <Text variant="small" className="text-muted-foreground">{item.repository.language}</Text>
               </View>
               <OpportunityCard
                 opportunity={item.opportunity}
                 onAnalyze={() => router.push(`/repository/${item.repository.id}`)}
                 onStart={() => console.log('Start contribution', item.opportunity.id)}
               />
            </View>
          )}
          contentContainerStyle={{ paddingBottom: 20 }}
        />
      )}
    </ScreenContainer>
  );
}
