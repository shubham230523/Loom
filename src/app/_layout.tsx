import { DarkTheme, DefaultTheme, ThemeProvider, Stack, useRouter, useSegments } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { useEffect } from 'react';
import { useColorScheme } from 'react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { AnimatedSplashOverlay } from '@/components/animated-icon';
import { useAuthStore } from '@/store/auth-store';
import { AuthService } from '@/services/auth.service';

// Import global CSS for NativeWind
import '../global.css';

SplashScreen.preventAutoHideAsync();

const queryClient = new QueryClient();

export default function RootLayout() {
  const colorScheme = useColorScheme();
  const { isAuthenticated, isLoading } = useAuthStore();
  const segments = useSegments();
  const router = useRouter();

  // 1. Initial Session Check
  useEffect(() => {
    AuthService.fetchCurrentUser();
  }, []);

  // 2. Auth-based Navigation Guard
  useEffect(() => {
    if (isLoading) return;

    // Type casting to avoid TS error on '(index)' if needed,
    // but better to just check segments[0] as string | undefined
    const seg0 = segments[0] as string | undefined;
    const isPublicScreen = seg0 === 'welcome' || seg0 === undefined || seg0 === 'index';

    if (isAuthenticated && isPublicScreen) {
      // Redirect to home if logged in and trying to access landing/auth screens
      router.replace('/(tabs)/home');
    } else if (!isAuthenticated && !isPublicScreen) {
      // Redirect to welcome if not logged in and trying to access protected screens
      router.replace('/welcome');
    }
  }, [isAuthenticated, segments, isLoading, router]);

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider value={colorScheme === 'dark' ? DarkTheme : DefaultTheme}>
        <AnimatedSplashOverlay />
        <Stack screenOptions={{ headerShown: false }}>
          <Stack.Screen name="index" />
          <Stack.Screen name="welcome" />
          <Stack.Screen name="(tabs)" />
          <Stack.Screen name="settings" options={{ presentation: 'modal', headerShown: true }} />
        </Stack>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
