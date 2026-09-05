import { useEffect } from 'react';
import { useRouter } from 'expo-router';
import { View } from 'react-native';

/**
 * SplashRedirect handles the initial application entry.
 * The visual splash experience is managed by AnimatedSplashOverlay in the root _layout.tsx.
 */
export default function SplashRedirect() {
  const router = useRouter();

  useEffect(() => {
    // Immediate redirect to the welcome screen.
    // The overlay will be on top during this transition.
    router.replace('/welcome');
  }, [router]);

  return <View style={{ flex: 1, backgroundColor: '#208AEF' }} />;
}
