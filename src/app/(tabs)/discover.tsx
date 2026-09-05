import { useState } from 'react';
import { View, Pressable } from 'react-native';
import { SymbolView } from 'expo-symbols';
import { ScreenContainer } from '@/components/ui/screen-container';
import { Text } from '@/components/ui/text';
import { Input } from '@/components/ui/input';
import { EmptyState } from '@/components/ui/empty-state';
import { useTheme } from '@/hooks/use-theme';

export default function DiscoverScreen() {
  const theme = useTheme();
  const [searchQuery, setSearchQuery] = useState('');

  // Data state (empty by default)
  const data: any[] = [];

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
            onChangeText={setSearchQuery}
            leftIcon={
              <SymbolView
                name="magnifyingglass"
                size={18}
                tintColor={theme.textSecondary}
              />
            }
          />
        </View>
        <Pressable
          className="h-12 w-12 items-center justify-center rounded-lg border border-border bg-card active:opacity-70"
          onPress={() => console.log('Filter pressed')}
        >
          <SymbolView
            name="line.3.horizontal.decrease.circle"
            size={22}
            tintColor={theme.text}
          />
        </Pressable>
      </View>

      <View className="flex-1">
        {data.length === 0 ? (
          <EmptyState
            title={searchQuery ? `No results for "${searchQuery}"` : "Discover Projects"}
            description="Search for high-impact repositories to start contributing."
            icon="magnifyingglass"
          />
        ) : (
          <View>
            {/* Repository list items would go here */}
            <Text>Results found</Text>
          </View>
        )}
      </View>
    </ScreenContainer>
  );
}
