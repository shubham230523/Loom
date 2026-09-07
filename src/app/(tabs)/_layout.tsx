import { Tabs } from 'expo-router';
import { SymbolView } from 'expo-symbols';
import { useColorScheme } from 'react-native';

import { Colors } from '@/constants/theme';

export default function TabLayout() {
  const scheme = useColorScheme();
  const theme = Colors[scheme === 'dark' ? 'dark' : 'light'];

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: theme.primary,
        tabBarInactiveTintColor: theme.textSecondary,
        tabBarStyle: {
          backgroundColor: theme.background,
          borderTopColor: theme.border,
          height: 60,
          paddingBottom: 8,
          paddingTop: 8,
        },
        tabBarLabelStyle: {
          fontFamily: 'system-ui',
          fontSize: 12,
          fontWeight: '500',
        },
      }}>
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
  );
}
