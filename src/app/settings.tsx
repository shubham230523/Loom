import { View, Pressable } from 'react-native';
import { Stack } from 'expo-router';
import { SymbolView, type SFSymbol } from 'expo-symbols';
import { ScreenContainer } from '@/components/ui/screen-container';
import { Text } from '@/components/ui/text';
import { Card } from '@/components/ui/card';
import { useTheme } from '@/hooks/use-theme';
import { cn } from '@/utils/cn';

export default function SettingsScreen() {
  const theme = useTheme();

  return (
    <ScreenContainer scrollable className="py-6">
      <Stack.Screen options={{ title: 'Settings', headerTitleAlign: 'center' }} />

      <View className="gap-6">
        {/* GitHub Section */}
        <SettingsSection title="Connections">
          <SettingsItem
            icon="link"
            label="GitHub"
            value="Not Connected"
            theme={theme}
          />
        </SettingsSection>

        {/* AI Providers Section */}
        <SettingsSection title="Intelligence">
          <SettingsItem
            icon="cpu"
            label="AI Providers"
            value="Default (Loom Cloud)"
            theme={theme}
          />
        </SettingsSection>

        {/* Contribution Preferences Section */}
        <SettingsSection title="Automation">
          <SettingsItem
            icon="wrench.and.screwdriver.fill"
            label="Contribution Preferences"
            theme={theme}
          />
        </SettingsSection>

        {/* Notifications Section */}
        <SettingsSection title="System">
          <SettingsItem
            icon="bell.fill"
            label="Notifications"
            theme={theme}
          />
          <SettingsItem
            icon="lock.fill"
            label="Security"
            theme={theme}
          />
          <SettingsItem
            icon="chart.bar.fill"
            label="Usage"
            theme={theme}
          />
        </SettingsSection>

        <View className="mt-8 mb-12 items-center">
          <Text variant="small" className="text-muted-foreground">Loom Version 1.0.0-alpha</Text>
        </View>
      </View>
    </ScreenContainer>
  );
}

function SettingsSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <View className="gap-2">
      <Text variant="small" className="text-muted-foreground uppercase tracking-widest px-1">
        {title}
      </Text>
      <Card className="p-0 overflow-hidden">
        {children}
      </Card>
    </View>
  );
}

function SettingsItem({
  icon,
  label,
  value,
  theme,
  isLast = false
}: {
  icon: SFSymbol;
  label: string;
  value?: string;
  theme: any;
  isLast?: boolean;
}) {
  return (
    <Pressable
      className={cn(
        "flex-row items-center justify-between p-4 active:bg-muted/50",
        !isLast && "border-b border-border/50"
      )}
      onPress={() => console.log(`${label} pressed`)}
    >
      <View className="flex-row items-center gap-3">
        <SymbolView name={icon} size={20} tintColor={theme.text} />
        <Text className="font-medium">{label}</Text>
      </View>
      <View className="flex-row items-center gap-2">
        {value && <Text variant="muted" className="text-sm">{value}</Text>}
        <SymbolView name="chevron.right" size={14} tintColor={theme.textSecondary} />
      </View>
    </Pressable>
  );
}
