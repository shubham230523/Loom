import { View, Pressable } from 'react-native';
import { Stack, useRouter } from 'expo-router';
import { SymbolView, type SFSymbol } from 'expo-symbols';
import { ScreenContainer } from '@/components/ui/screen-container';
import { Text } from '@/components/ui/text';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useTheme } from '@/hooks/use-theme';
import { cn } from '@/utils/cn';
import { AuthService } from '@/services/auth.service';
import { useAuthStore } from '@/store/auth-store';

export default function SettingsScreen() {
  const theme = useTheme();
  const { user } = useAuthStore();

  const router = useRouter();

  const handleLogout = async () => {
    await AuthService.logout();
    router.replace('/welcome');
  };

  return (
    <ScreenContainer scrollable className="py-6">
      <Stack.Screen options={{ title: 'Settings', headerTitleAlign: 'center' }} />

      <View className="gap-6">
        {/* Account Section */}
        <SettingsSection title="Account">
          <SettingsItem
            icon="person.fill"
            label="Profile"
            value={user?.username}
            theme={theme}
          />
          <SettingsItem
            icon="link"
            label="GitHub"
            value={user?.github_user_id ? "Connected" : "Not Connected"}
            theme={theme}
            isLast
          />
        </SettingsSection>

        {/* AI Providers Section */}
        <SettingsSection title="Intelligence">
          <SettingsItem
            icon="cpu"
            label="AI Providers"
            value="Default (OpenRouter)"
            theme={theme}
            isLast
          />
        </SettingsSection>

        {/* Contribution Preferences Section */}
        <SettingsSection title="Automation">
          <SettingsItem
            icon="wrench.and.screwdriver.fill"
            label="Contribution Preferences"
            theme={theme}
            isLast
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
            isLast
          />
        </SettingsSection>

        <View className="mt-4">
          <Button
            variant="destructive"
            label="Log Out"
            onPress={handleLogout}
          />
        </View>

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
