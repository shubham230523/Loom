import { useState, useCallback } from 'react';
import { View, Pressable, FlatList, Image } from 'react-native';
import { SymbolView } from 'expo-symbols';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'expo-router';
import { ScreenContainer } from '@/components/ui/screen-container';
import { Text } from '@/components/ui/text';
import { Input } from '@/components/ui/input';
import { EmptyState } from '@/components/ui/empty-state';
import { LoadingState } from '@/components/ui/loading-state';
import { ErrorState } from '@/components/ui/error-state';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useTheme } from '@/hooks/use-theme';
import { RepositoryService } from '@/services/repository.service';
import { GitHubRepository } from '@/types/repository';

export default function DiscoverScreen() {
  const theme = useTheme();
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);

  const { data, isLoading, error, isError, refetch, isFetching } = useQuery({
    queryKey: ['repositories', searchQuery, page],
    queryFn: () => RepositoryService.search({ q: searchQuery || 'stars:>1000', page }),
    enabled: true, // Always show some repos if empty query
  });

  const handleSearch = useCallback((text: string) => {
    setSearchQuery(text);
    setPage(1);
  }, []);

  const renderRepository = ({ item }: { item: GitHubRepository }) => (
    <Pressable
      onPress={() => router.push(`/repository/${item.id}`)}
      style={({ pressed }) => [{ opacity: pressed ? 0.7 : 1 }]}
    >
      <Card className="mb-4">
        <View className="flex-row gap-3 items-center mb-2">
          <Image
            source={{ uri: item.owner.avatar_url }}
            className="w-6 h-6 rounded-full"
          />
          <Text variant="small" weight="medium" className="text-muted-foreground">
            {item.owner.login}
          </Text>
        </View>
        <Text variant="subtitle" className="mb-1">{item.name}</Text>
        {item.description && (
          <Text variant="small" className="text-muted-foreground mb-3" numberOfLines={2}>
            {item.description}
          </Text>
        )}
        <View className="flex-row flex-wrap gap-2">
          {item.language && (
            <Badge variant="outline" label={item.language} />
          )}
          <View className="flex-row items-center gap-1">
            <Text style={{ fontSize: 12 }}>⭐</Text>
            <Text variant="small" className="text-muted-foreground">
              {(item.stargazers_count / 1000).toFixed(1)}k
            </Text>
          </View>
          <View className="flex-row items-center gap-1">
            <Text style={{ fontSize: 12 }}>🍴</Text>
            <Text variant="small" className="text-muted-foreground">
              {item.forks_count}
            </Text>
          </View>
        </View>
      </Card>
    </Pressable>
  );

  const renderContent = () => {
    if (isLoading && !isFetching) {
      return <LoadingState message="Discovering high-impact repositories..." />;
    }

    if (isError) {
      return (
        <ErrorState
          title="Search Failed"
          message={error instanceof Error ? error.message : 'Failed to fetch repositories'}
          onRetry={() => refetch()}
        />
      );
    }

    if (data?.items.length === 0) {
      return (
        <EmptyState
          title={searchQuery ? `No results for "${searchQuery}"` : "No repositories found"}
          description="Try a different search term or check your connection."
          icon="magnifyingglass"
        />
      );
    }

    return (
      <FlatList
        data={data?.items}
        renderItem={renderRepository}
        keyExtractor={(item) => item.id.toString()}
        onEndReached={() => {
          if (!isFetching && (data?.items.length || 0) < (data?.total_count || 0)) {
            setPage(prev => prev + 1);
          }
        }}
        onEndReachedThreshold={0.5}
        ListFooterComponent={isFetching && page > 1 ? <LoadingState className="h-20" /> : null}
        contentContainerStyle={{ paddingBottom: 20 }}
      />
    );
  };

  return (
    <ScreenContainer className="py-6">
      <View className="mb-6">
        <Text variant="title">Discover</Text>
        <Text variant="muted">Find and collaborate on open source projects.</Text>
      </View>

      <View className="flex-row gap-2 mb-6">
        <View className="flex-1">
          <Input
            placeholder="Search repositories..."
            value={searchQuery}
            onChangeText={handleSearch}
            leftIcon={
              <Text style={{ fontSize: 18, marginLeft: 8 }}>🔍</Text>
            }
          />
        </View>
        <Pressable
          className="h-12 w-12 items-center justify-center rounded-lg border border-border bg-card active:opacity-70"
          onPress={() => console.log('Filter pressed')}
        >
          <Text style={{ fontSize: 22 }}>⚙️</Text>
        </Pressable>
      </View>

      <View className="flex-1">
        {renderContent()}
      </View>
    </ScreenContainer>
  );
}
