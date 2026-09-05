import { View, ViewProps } from 'react-native';
import { cn } from '@/utils/cn';

export interface CardProps extends ViewProps {
  className?: string;
}

export function Card({ className, ...props }: CardProps) {
  return (
    <View
      className={cn(
        'rounded-xl border border-border bg-card p-4 shadow-sm',
        className
      )}
      {...props}
    />
  );
}

export function CardHeader({ className, ...props }: CardProps) {
  return <View className={cn('flex-col space-y-1.5 p-0 mb-4', className)} {...props} />;
}

export function CardTitle({ className, ...props }: CardProps) {
  return <View className={cn('font-semibold leading-none tracking-tight', className)} {...props} />;
}

export function CardContent({ className, ...props }: CardProps) {
  return <View className={cn('p-0', className)} {...props} />;
}

export function CardFooter({ className, ...props }: CardProps) {
  return <View className={cn('flex items-center pt-4', className)} {...props} />;
}
