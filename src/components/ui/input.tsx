import { TextInput, TextInputProps, View } from 'react-native';
import { cn } from '@/utils/cn';
import { useTheme } from '@/hooks/use-theme';

export interface InputProps extends TextInputProps {
  className?: string;
  containerClassName?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export function Input({
  className,
  containerClassName,
  leftIcon,
  rightIcon,
  ...props
}: InputProps) {
  const theme = useTheme();

  return (
    <View
      className={cn(
        'flex-row items-center rounded-lg border border-border bg-background px-3 h-12',
        containerClassName
      )}
    >
      {leftIcon && <View className="mr-2">{leftIcon}</View>}
      <TextInput
        className={cn(
          'flex-1 h-full text-foreground font-sans text-base',
          className
        )}
        placeholderTextColor={theme.textSecondary}
        {...props}
      />
      {rightIcon && <View className="ml-2">{rightIcon}</View>}
    </View>
  );
}
