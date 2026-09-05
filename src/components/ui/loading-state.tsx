import { View, ViewProps } from 'react-native';
import { LoadingIndicator } from './loading-indicator';
import { Text } from './text';
import { cn } from '@/utils/cn';

export interface LoadingStateProps extends ViewProps {
  message?: string;
  className?: string;
}

export function LoadingState({ message = 'Loading...', className, ...props }: LoadingStateProps) {
  return (
    <View className={cn('flex-1 items-center justify-center p-6 gap-4', className)} {...props}>
      <LoadingIndicator />
      {message && <Text variant="muted">{message}</Text>}
    </View>
  );
}
