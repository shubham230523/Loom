import { ActivityIndicator, View, ViewProps } from 'react-native';
import { cn } from '@/utils/cn';

export interface LoadingIndicatorProps extends ViewProps {
  size?: 'small' | 'large';
  color?: string;
  className?: string;
  fullScreen?: boolean;
}

export function LoadingIndicator({
  className,
  size = 'large',
  color,
  fullScreen = false,
  ...props
}: LoadingIndicatorProps) {
  const containerClasses = cn(
    'items-center justify-center',
    fullScreen ? 'flex-1 bg-background' : 'p-4',
    className
  );

  return (
    <View className={containerClasses} {...props}>
      <ActivityIndicator size={size} color={color || '#208AEF'} />
    </View>
  );
}
