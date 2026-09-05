import { Text as RNText, TextProps } from 'react-native';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/utils/cn';

const textVariants = cva('text-foreground', {
  variants: {
    variant: {
      default: 'text-base font-sans',
      title: 'text-3xl font-sans font-bold tracking-tight',
      subtitle: 'text-xl font-sans font-semibold',
      small: 'text-sm font-sans',
      code: 'text-sm font-mono bg-muted px-1.5 py-0.5 rounded-sm',
      link: 'text-primary underline',
      muted: 'text-muted-foreground',
    },
    weight: {
      light: 'font-light',
      normal: 'font-normal',
      medium: 'font-medium',
      semibold: 'font-semibold',
      bold: 'font-bold',
    },
    align: {
      left: 'text-left',
      center: 'text-center',
      right: 'text-right',
    },
  },
  defaultVariants: {
    variant: 'default',
    weight: 'normal',
    align: 'left',
  },
});

export interface TypographyProps
  extends TextProps,
    VariantProps<typeof textVariants> {
  className?: string;
}

export function Text({ className, variant, weight, align, ...props }: TypographyProps) {
  return (
    <RNText
      className={cn(textVariants({ variant, weight, align }), className)}
      {...props}
    />
  );
}
