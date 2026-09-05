import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { StyleSheet } from 'react-native';

export default function ActivityScreen() {
  return (
    <ThemedView style={styles.container}>
      <ThemedText type="subtitle">Activity</ThemedText>
      <ThemedText>Recent notifications and activity.</ThemedText>
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
