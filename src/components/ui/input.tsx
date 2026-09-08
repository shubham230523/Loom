import React, { useState } from 'react';
import { TextInput, TextInputProps, View, Platform } from 'react-native';
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
  onFocus,
  onBlur,
  ...props
}: InputProps) {
  const theme = useTheme();
  const [isFocused, setIsFocused] = useState(false);

  return (
    <View
      className={cn(
        'flex-row items-center rounded-lg border bg-background px-3 h-12 transition-colors',
        isFocused ? 'border-primary ring-1 ring-primary/20' : 'border-border',
        containerClassName
      )}
    >
      {leftIcon && <View className="mr-2">{leftIcon}</View>}
      <TextInput
        className={cn(
          'flex-1 h-full text-foreground font-sans text-base',
          Platform.OS === 'web' && 'outline-none',
          className
        )}
        onFocus={(e) => {
          setIsFocused(true);
          onFocus?.(e);
        }}
        onBlur={(e) => {
          setIsFocused(false);
          onBlur?.(e);
        }}
        placeholderTextColor={theme.textSecondary}
        {...props}
      />
      {rightIcon && <View className="ml-2">{rightIcon}</View>}
    </View>
  );
}
