import { Pressable, PressableProps, ActivityIndicator } from 'react-native';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/utils/cn';
import { Text } from './text';

const buttonVariants = cva(
  'flex-row items-center justify-center rounded-lg active:opacity-80 transition-opacity',
  {
    variants: {
      variant: {
        default: 'bg-primary',
        secondary: 'bg-secondary',
        outline: 'border border-border bg-transparent',
        ghost: 'bg-transparent',
        destructive: 'bg-destructive',
      },
      size: {
        default: 'h-12 px-6',
        sm: 'h-9 px-3',
        lg: 'h-14 px-8',
        icon: 'h-12 w-12',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

const textVariants = cva('font-semibold', {
  variants: {
    variant: {
      default: 'text-primary-foreground',
      secondary: 'text-secondary-foreground',
      outline: 'text-foreground',
      ghost: 'text-foreground',
      destructive: 'text-destructive-foreground',
    },
    size: {
      default: 'text-base',
      sm: 'text-sm',
      lg: 'text-lg',
      icon: 'text-base',
    },
  },
  defaultVariants: {
    variant: 'default',
    size: 'default',
  },
});

export interface ButtonProps
  extends PressableProps,
    VariantProps<typeof buttonVariants> {
  label?: string;
  loading?: boolean;
  className?: string;
  textClassName?: string;
}

export function Button({
  className,
  variant,
  size,
  label,
  loading,
  children,
  textClassName,
  ...props
}: ButtonProps) {
  return (
    <Pressable
      className={cn(buttonVariants({ variant, size }), className)}
      disabled={loading || props.disabled}
      {...props}
    >
      {loading ? (
        <ActivityIndicator color={variant === 'default' ? 'white' : 'gray'} />
      ) : (
        <>
          {label ? (
            <Text className={cn(textVariants({ variant, size }), textClassName)}>
              {label}
            </Text>
          ) : (
            children
          )}
        </>
      )}
    </Pressable>
  );
}
