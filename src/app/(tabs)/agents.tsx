import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { StyleSheet } from 'react-native';

export default function AgentsScreen() {
  return (
    <ThemedView style={styles.container}>
      <ThemedText type="subtitle">Running Agents</ThemedText>
      <ThemedText>Monitor your active autonomous agents.</ThemedText>
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
