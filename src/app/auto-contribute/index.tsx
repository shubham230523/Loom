import { useState } from 'react';
import { View, Pressable } from 'react-native';
import { useRouter, Stack } from 'expo-router';
import { ScreenContainer } from '@/components/ui/screen-container';
import { Text } from '@/components/ui/text';
import { Button } from '@/components/ui/button';

const CONTRIBUTION_TYPES = ['bug', 'feature', 'refactor', 'documentation', 'testing'];
const DIFFICULTIES = ['Easy', 'Intermediate', 'Hard'];
const LANGUAGES = ['TypeScript', 'Python', 'Go', 'Rust', 'Java'];

export default function AutoContributeConfigScreen() {
  const router = useRouter();

  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [selectedDifficulties, setSelectedDifficulties] = useState<string[]>([]);
  const [selectedLanguages, setSelectedLanguages] = useState<string[]>([]);

  const toggle = (list: string[], setList: (l: string[]) => void, item: string) => {
    if (list.includes(item)) {
      setList(list.filter(i => i !== item));
    } else {
      setList([...list, item]);
    }
  };

  const handleFindWork = () => {
    router.push({
      pathname: '/auto-contribute/recommendations',
      params: {
        types: selectedTypes.join(','),
        difficulties: selectedDifficulties.join(','),
        languages: selectedLanguages.join(',')
      }
    });
  };

  return (
    <ScreenContainer scrollable className="py-6">
      <Stack.Screen options={{ title: 'Auto Contribute', headerTitleAlign: 'center' }} />

      <View className="mb-8 px-4">
        <Text variant="title">Configure Workflow</Text>
        <Text variant="muted">Let Loom find the best matching tasks for your profile.</Text>
      </View>

      <View className="gap-8 px-4">
        <SelectionSection
          title="What do you want to work on?"
          items={CONTRIBUTION_TYPES}
          selected={selectedTypes}
          onToggle={(item) => toggle(selectedTypes, setSelectedTypes, item)}
        />

        <SelectionSection
          title="Challenge Level"
          items={DIFFICULTIES}
          selected={selectedDifficulties}
          onToggle={(item) => toggle(selectedDifficulties, setSelectedDifficulties, item)}
        />

        <SelectionSection
          title="Preferred Tech"
          items={LANGUAGES}
          selected={selectedLanguages}
          onToggle={(item) => toggle(selectedLanguages, setSelectedLanguages, item)}
        />

        <View className="mt-4 mb-12">
          <Button
            label="Find Suitable Work"
            size="lg"
            onPress={handleFindWork}
          />
        </View>
      </View>
    </ScreenContainer>
  );
}

function SelectionSection({ title, items, selected, onToggle }: { title: string, items: string[], selected: string[], onToggle: (i: string) => void }) {
  return (
    <View className="gap-3">
      <Text weight="bold" className="text-lg px-1">{title}</Text>
      <View className="flex-row flex-wrap gap-2">
        {items.map(item => {
          const isSelected = selected.includes(item);
          return (
            <Pressable
              key={item}
              onPress={() => onToggle(item)}
              className={`px-4 py-2 rounded-full border ${isSelected ? 'bg-primary border-primary' : 'bg-card border-border'} active:opacity-70`}
            >
              <Text className={isSelected ? 'text-primary-foreground font-bold' : 'text-foreground'}>
                {item.charAt(0).toUpperCase() + item.slice(1)}
              </Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}
