import { View, ViewProps, ScrollView, ScrollViewProps } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { cn } from '@/utils/cn';

export interface ScreenContainerProps extends ViewProps {
  scrollable?: boolean;
  scrollViewProps?: ScrollViewProps;
  className?: string;
  withPadding?: boolean;
}

export function ScreenContainer({
  children,
  scrollable = false,
  scrollViewProps,
  className,
  withPadding = true,
  ...props
}: ScreenContainerProps) {
  const insets = useSafeAreaInsets();

  const content = (
    <View
      className={cn(
        'flex-1 bg-background',
        withPadding && 'px-4',
        className
      )}
      style={{
        paddingTop: insets.top,
        paddingBottom: insets.bottom,
      }}
      {...props}
    >
      {children}
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
