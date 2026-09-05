import {
  Tabs,
  TabList,
  TabTrigger,
  TabSlot,
  TabTriggerSlotProps,
} from 'expo-router/ui';
import { SymbolView, type SFSymbol } from 'expo-symbols';
import { Pressable, View } from 'react-native';
import { Text } from './ui/text';
import { cn } from '@/utils/cn';
import { useTheme } from '@/hooks/use-theme';

export default function AppTabs() {
  return (
    <Tabs className="flex-col md:flex-row h-screen bg-background">
      {/* Mobile Header (Hidden on Desktop) */}
      <View className="md:hidden p-4 border-b border-border flex-row items-center justify-between">
        <Text variant="subtitle" className="font-bold">Loom</Text>
      </View>

      {/* Desktop Sidebar */}
      <TabList className="hidden md:flex w-64 border-r border-border bg-card p-4 flex-col gap-1">
        <View className="px-2 py-4 mb-4">
          <Text variant="title" className="text-2xl font-bold text-primary">Loom</Text>
        </View>

        <SidebarItem name="home" href="/home" icon="house.fill" label="Home" />
        <SidebarItem name="discover" href="/discover" icon="magnifyingglass" label="Discover" />
        <SidebarItem name="contributions" href="/contributions" icon="plus.square.fill" label="Contributions" />
        <SidebarItem name="agents" href="/agents" icon="cpu" label="Running Agents" />
        <SidebarItem name="pulls" href="/pulls" icon="arrow.triangle.pull" label="Pull Requests" />
        <SidebarItem name="activity" href="/activity" icon="bell.fill" label="Activity" />

        <View className="mt-auto pt-4 border-t border-border gap-1">
          <SidebarItem name="profile" href="/profile" icon="person.fill" label="Profile" />
          <SidebarItem name="settings" href="/settings" icon="gearshape.fill" label="Settings" />
        </View>
      </TabList>

      {/* Main Content Area */}
      <View className="flex-1">
        <TabSlot />
      </View>

      {/* Mobile Bottom Bar (Hidden on Desktop) */}
      <TabList className="md:hidden flex-row border-t border-border bg-card pb-safe">
        <MobileTabTrigger name="home" href="/home" icon="house.fill" />
        <MobileTabTrigger name="discover" href="/discover" icon="magnifyingglass" />
        <MobileTabTrigger name="contributions" href="/contributions" icon="plus.square.fill" />
        <MobileTabTrigger name="activity" href="/activity" icon="bell.fill" />
        <MobileTabTrigger name="profile" href="/profile" icon="person.fill" />
      </TabList>
    </Tabs>
  );
}

function SidebarItem({ name, href, icon, label }: { name: string; href: string; icon: SFSymbol; label: string }) {
  const theme = useTheme();

  return (
    <TabTrigger name={name} href={href} asChild>
      <SidebarButton icon={icon} label={label} theme={theme} />
    </TabTrigger>
  );
}

function SidebarButton({ icon, label, isFocused, theme, ...props }: TabTriggerSlotProps & { icon: SFSymbol; label: string; theme: any }) {
  return (
    <Pressable
      {...props}
      className={cn(
        "flex-row items-center gap-3 px-3 py-2.5 rounded-lg transition-colors",
        isFocused ? "bg-primary/10" : "hover:bg-muted active:bg-muted"
      )}
    >
      <SymbolView
        name={icon}
        size={20}
        tintColor={isFocused ? theme.primary : theme.textSecondary}
      />
      <Text
        className={cn(
          "font-medium",
          isFocused ? "text-primary" : "text-muted-foreground"
        )}
      >
        {label}
      </Text>
    </Pressable>
  );
}

function MobileTabTrigger({ name, href, icon }: { name: string; href: string; icon: SFSymbol }) {
  const theme = useTheme();
  return (
    <TabTrigger name={name} href={href} asChild className="flex-1">
      <TabTriggerButton icon={icon} theme={theme} />
    </TabTrigger>
  );
}

function TabTriggerButton({ icon, isFocused, theme, ...props }: TabTriggerSlotProps & { icon: SFSymbol; theme: any }) {
  return (
    <Pressable
      {...props}
      className="items-center justify-center py-3"
    >
      <SymbolView
        name={icon}
        size={24}
        tintColor={isFocused ? theme.primary : theme.textSecondary}
      />
    </Pressable>
  );
}
