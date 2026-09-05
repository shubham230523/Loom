import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { StyleSheet } from 'react-native';
import { Link } from 'expo-router';

export default function ProfileScreen() {
  return (
    <ThemedView style={styles.container}>
      <ThemedText type="subtitle">Profile</ThemedText>
      <ThemedText>Manage your Loom profile.</ThemedText>

      <Link href="/settings" style={styles.link}>
        <ThemedText type="link">Go to Settings</ThemedText>
      </Link>
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
  link: {
    marginTop: 20,
  },
});
