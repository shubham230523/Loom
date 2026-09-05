import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { StyleSheet } from 'react-native';

export default function ContributionsScreen() {
  return (
    <ThemedView style={styles.container}>
      <ThemedText type="subtitle">Contributions</ThemedText>
      <ThemedText>Your contributions to the community.</ThemedText>
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
