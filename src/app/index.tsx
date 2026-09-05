import { useEffect } from 'react';
import { useRouter } from 'expo-router';
import { ThemedView } from '@/components/themed-view';
import { ThemedText } from '@/components/themed-text';
import { StyleSheet } from 'react-native';

export default function Splash() {
  const router = useRouter();

  useEffect(() => {
    async function prepare() {
      // Simulate some loading or check auth
      await new Promise(resolve => setTimeout(resolve, 2000));
      router.replace('/welcome');
    }
    prepare();
  }, [router]);

  return (
    <ThemedView style={styles.container}>
      <ThemedText type="title">LOOM</ThemedText>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#208AEF', // Match splash color from app.json
  },
});
