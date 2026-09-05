import { View, ViewProps, ScrollView, ScrollViewProps } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { cn } from '@/utils/cn';
import { MaxContentWidth } from '@/constants/theme';

export interface ScreenContainerProps extends ViewProps {
  scrollable?: boolean;
  scrollViewProps?: ScrollViewProps;
  className?: string;
  withPadding?: boolean;
  maxWidth?: number;
}

export function ScreenContainer({
  children,
  scrollable = false,
  scrollViewProps,
  className,
  withPadding = true,
  maxWidth = MaxContentWidth,
  ...props
}: ScreenContainerProps) {
  const insets = useSafeAreaInsets();

  const content = (
    <View
      className={cn(
        'flex-1 bg-background items-center',
        className
      )}
      style={{
        paddingTop: insets.top,
        paddingBottom: insets.bottom,
      }}
      {...props}
    >
      <View
        className={cn(
          'w-full flex-1',
          withPadding && 'px-4'
        )}
        style={{ maxWidth }}
      >
        {children}
      </View>
    </View>
  );

  if (scrollable) {
    return (
      <ScrollView
        className="flex-1 bg-background"
        contentContainerStyle={{ flexGrow: 1 }}
        {...scrollViewProps}
      >
        {content}
      </ScrollView>
    );
  }

  return content;
}
