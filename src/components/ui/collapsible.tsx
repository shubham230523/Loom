import { SymbolView } from 'expo-symbols';
import { PropsWithChildren, useState } from 'react';
import { Pressable, View } from 'react-native';
import Animated, { FadeIn } from 'react-native-reanimated';

import { Text } from './text';
import { useTheme } from '@/hooks/use-theme';

export function Collapsible({ children, title }: PropsWithChildren & { title: string }) {
  const [isOpen, setIsOpen] = useState(false);
  const theme = useTheme();

  return (
    <View>
      <Pressable
        className="flex-row items-center gap-2"
        style={({ pressed }) => [pressed && { opacity: 0.7 }]}
        onPress={() => setIsOpen((value) => !value)}>
        <View className="w-8 h-8 rounded-full bg-muted items-center justify-center">
          <SymbolView
            name={{ ios: 'chevron.right', android: 'chevron_right', web: 'chevron_right' }}
            size={14}
            weight="bold"
            tintColor={theme.text}
            style={{ transform: [{ rotate: isOpen ? '90deg' : '0deg' }] }}
          />
        </View>

        <Text variant="small" weight="medium">{title}</Text>
      </Pressable>
      {isOpen && (
        <Animated.View entering={FadeIn.duration(200)}>
          <View className="mt-3 ml-8 p-4 bg-muted/50 rounded-lg">
            {children}
          </View>
        </Animated.View>
      )}
    </View>
  );
}
