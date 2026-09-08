import { Tabs, useRouter, useSegments } from 'expo-router';
import { SymbolView, type SFSymbol } from 'expo-symbols';
import { Pressable, View, useWindowDimensions } from 'react-native';
import { Text } from '@/components/ui/text';
import { cn } from '@/utils/cn';
import { useTheme } from '@/hooks/use-theme';

export default function TabLayout() {
  const { width } = useWindowDimensions();
  const isDesktop = width >= 768;
  const segments = useSegments();
  const currentTab = segments[segments.length - 1];
  const theme = useTheme();

  return (
    <View className="flex-1 flex-row bg-background">
      {/* Desktop Sidebar */}
      {isDesktop && (
        <View className="w-64 border-r border-border bg-card p-4 flex-col gap-1">
          <View className="px-2 py-4 mb-4">
            <Text variant="title" className="text-2xl font-bold text-primary">Loom</Text>
          </View>

          <SidebarItem name="home" icon="house.fill" label="Home" isFocused={currentTab === 'home'} />
          <SidebarItem name="discover" icon="magnifyingglass" label="Discover" isFocused={currentTab === 'discover'} />
          <SidebarItem name="contributions" icon="plus.square.fill" label="Contributions" isFocused={currentTab === 'contributions'} />
          <SidebarItem name="activity" icon="bell.fill" label="Activity" isFocused={currentTab === 'activity'} />
          <SidebarItem name="profile" icon="person.fill" label="Profile" isFocused={currentTab === 'profile'} />

          <View className="mt-auto pt-4 border-t border-border gap-1">
            <SidebarItem name="settings" icon="gearshape.fill" label="Settings" isFocused={currentTab === 'settings'} />
          </View>
        </View>
      )}

      <View className="flex-1">
        <Tabs
          screenOptions={{
            headerShown: false,
            tabBarActiveTintColor: theme.primary,
            tabBarInactiveTintColor: theme.textSecondary,
            tabBarStyle: isDesktop ? { display: 'none' } : {
              backgroundColor: theme.background,
              borderTopColor: theme.border,
              height: 60,
              paddingBottom: 8,
              paddingTop: 8,
            },
          }}
        >
          <Tabs.Screen
            name="home"
            options={{
              title: 'Home',
              tabBarIcon: ({ color, size }) => (
                <SymbolView name="house.fill" size={size} tintColor={color} />
              ),
            }}
          />
          <Tabs.Screen
            name="discover"
            options={{
              title: 'Discover',
              tabBarIcon: ({ color, size }) => (
                <SymbolView name="magnifyingglass" size={size} tintColor={color} />
              ),
            }}
          />
          <Tabs.Screen
            name="contributions"
            options={{
              title: 'Contribs',
              tabBarIcon: ({ color, size }) => (
                <SymbolView name="plus.square.fill" size={size} tintColor={color} />
              ),
            }}
          />
          <Tabs.Screen
            name="activity"
            options={{
              title: 'Activity',
              tabBarIcon: ({ color, size }) => (
                <SymbolView name="bell.fill" size={size} tintColor={color} />
              ),
            }}
          />
          <Tabs.Screen
            name="profile"
            options={{
              title: 'Profile',
              tabBarIcon: ({ color, size }) => (
                <SymbolView name="person.fill" size={size} tintColor={color} />
              ),
            }}
          />
          <Tabs.Screen
            name="agents"
            options={{
              href: null,
            }}
          />
          <Tabs.Screen
            name="pulls"
            options={{
              href: null,
            }}
          />
        </Tabs>
      </View>
    </View>
  );
}

function SidebarItem({ name, icon, label, isFocused }: { name: string; icon: SFSymbol; label: string; isFocused: boolean }) {
  const router = useRouter();
  const theme = useTheme();

  const handlePress = () => {
    if (name === 'settings') {
      router.push('/settings');
    } else {
      // Cast to any to bypass Expo Router's strict path typing for dynamic routes
      router.push(`/(tabs)/${name}` as any);
    }
  };

  return (
    <Pressable
      onPress={handlePress}
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
