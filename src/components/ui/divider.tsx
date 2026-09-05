import { View, ViewProps } from 'react-native';
import { cn } from '@/utils/cn';

export interface DividerProps extends ViewProps {
  orientation?: 'horizontal' | 'vertical';
  className?: string;
}

export function Divider({
  className,
  orientation = 'horizontal',
  ...props
}: DividerProps) {
  return (
    <View
      className={cn(
        'bg-border',
        orientation === 'horizontal' ? 'h-[1px] w-full' : 'h-full w-[1px]',
        className
      )}
      {...props}
    />
  );
}
