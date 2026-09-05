import { View, ViewProps } from 'react-native';
import { SymbolView } from 'expo-symbols';
import { Text } from './text';
import { RetryButton } from './retry-button';
import { cn } from '@/utils/cn';

export interface ErrorStateProps extends ViewProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({
  title = 'Something went wrong',
  message = 'An unexpected error occurred. Please try again.',
  onRetry,
  className,
  ...props
}: ErrorStateProps) {
  return (
    <View className={cn('flex-1 items-center justify-center p-8 gap-4', className)} {...props}>
      <View className="bg-destructive/10 w-16 h-16 rounded-full items-center justify-center mb-2">
        <SymbolView
          name={{ ios: 'exclamationmark.triangle', android: 'warning', web: 'warning' }}
          size={32}
          tintColor="#EF4444" // Using a standard error red (Red-500)
        />
      </View>
      <View className="items-center gap-1">
        <Text variant="subtitle">{title}</Text>
        <Text variant="muted" align="center">
          {message}
        </Text>
      </View>
      {onRetry && <RetryButton onPress={onRetry} className="mt-2" />}
    </View>
  );
}
