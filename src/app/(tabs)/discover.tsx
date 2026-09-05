import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { StyleSheet } from 'react-native';

export default function DiscoverScreen() {
  return (
    <ThemedView style={styles.container}>
      <ThemedText type="subtitle">Discover</ThemedText>
      <ThemedText>Explore new content on Loom.</ThemedText>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
});
