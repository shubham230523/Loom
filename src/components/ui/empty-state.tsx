import { View, ViewProps } from 'react-native';
import { SymbolView, type SFSymbol } from 'expo-symbols';
import { Text } from './text';
import { cn } from '@/utils/cn';
import { useTheme } from '@/hooks/use-theme';

export interface EmptyStateProps extends ViewProps {
  title?: string;
  description?: string;
  icon?: SFSymbol;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({
  title = 'No data found',
  description = 'There is nothing to display right now.',
  icon = 'tray',
  action,
  className,
  ...props
}: EmptyStateProps) {
  const theme = useTheme();

  return (
    <View className={cn('flex-1 items-center justify-center p-8 gap-4', className)} {...props}>
      <View className="bg-muted w-16 h-16 rounded-full items-center justify-center mb-2">
        <SymbolView
          name={{ ios: icon, android: 'info', web: 'info' }}
          size={32}
          tintColor={theme.textSecondary}
        />
      </View>
      <View className="items-center gap-1">
        <Text variant="subtitle">{title}</Text>
        <Text variant="muted" align="center">
          {description}
        </Text>
      </View>
      {action && <View className="mt-2">{action}</View>}
    </View>
  );
}
