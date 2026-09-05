import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { StyleSheet, Pressable } from 'react-native';
import { router } from 'expo-router';
import { Spacing } from '@/constants/theme';

export default function WelcomeScreen() {
  return (
    <ThemedView style={styles.container}>
      <ThemedText type="title">Welcome to Loom</ThemedText>
      <ThemedText style={styles.subtitle}>Your collaborative space.</ThemedText>

      <Pressable
        onPress={() => router.replace('/(tabs)/home')}
        style={styles.button}
      >
        <ThemedText type="linkPrimary">Get Started</ThemedText>
      </Pressable>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: Spacing.six,
  },
  subtitle: {
    marginTop: Spacing.two,
    marginBottom: Spacing.six,
    textAlign: 'center',
  },
  button: {
    padding: Spacing.four,
    borderRadius: Spacing.three,
    backgroundColor: 'rgba(0,0,0,0.05)',
  },
});
