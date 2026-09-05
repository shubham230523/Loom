import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { StyleSheet } from 'react-native';

export default function PullsScreen() {
  return (
    <ThemedView style={styles.container}>
      <ThemedText type="subtitle">Pull Requests</ThemedText>
      <ThemedText>Manage code reviews and contributions.</ThemedText>
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
