import { Button, ButtonProps } from './button';
import { SymbolView } from 'expo-symbols';
import { useTheme } from '@/hooks/use-theme';

export interface RetryButtonProps extends Omit<ButtonProps, 'label'> {
  label?: string;
}

export function RetryButton({ label = 'Retry', ...props }: RetryButtonProps) {
  const theme = useTheme();

  return (
    <Button variant="outline" label={label} {...props} className="flex-row gap-2">
      <SymbolView
        name={{ ios: 'arrow.clockwise', android: 'refresh', web: 'refresh' }}
        size={16}
        tintColor={theme.text}
      />
    </Button>
  );
}
