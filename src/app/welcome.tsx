import { View } from 'react-native';
import { useRouter } from 'expo-router';
import { SymbolView } from 'expo-symbols';
import { ScreenContainer } from '@/components/ui/screen-container';
import { Text } from '@/components/ui/text';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AuthService } from '@/services/auth.service';
import { useAuthStore } from '@/store/auth-store';
import { LoadingState } from '@/components/ui/loading-state';

export default function WelcomeScreen() {
  const router = useRouter();
  const { isLoading, error } = useAuthStore();

  const handleGitHubSignIn = async () => {
    await AuthService.startGitHubLogin();
  };

  const handleSkip = () => {
    router.replace('/(tabs)/home');
  };

  if (isLoading) {
    return <LoadingState message="Connecting to Loom..." />;
  }

  return (
    <ScreenContainer scrollable className="pt-16 pb-12">
      <View className="items-center mb-12">
        <Badge variant="outline" label="v1.0.0-alpha" className="mb-4" />
        <Text variant="title" className="text-5xl tracking-[10px] text-primary font-black mb-2">
          LOOM
        </Text>
        <Text variant="muted" align="center" className="max-w-[280px]">
          Autonomous collaboration for modern development teams.
        </Text>
      </View>

      <View className="gap-6 mb-12">
        <Card>
          <CardHeader className="flex-row items-center gap-3">
            <View className="bg-primary/10 p-2 rounded-lg">
              <SymbolView name="cpu" size={24} tintColor="#208AEF" />
            </View>
            <CardTitle>
              <Text variant="subtitle">Auto Contribute</Text>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Text variant="small" className="text-muted-foreground">
              Let autonomous agents handle documentation, refactoring, and boilerplate while you stay in the flow.
            </Text>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex-row items-center gap-3">
            <View className="bg-primary/10 p-2 rounded-lg">
              <SymbolView name="magnifyingglass" size={24} tintColor="#208AEF" />
            </View>
            <CardTitle>
              <Text variant="subtitle">Discover Projects</Text>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Text variant="small" className="text-muted-foreground">
              Find high-impact repositories where your skills are most needed. Smart matching for contributors.
            </Text>
          </CardContent>
        </Card>
      </View>

      <View className="gap-4">
        {error && (
          <Text className="text-destructive text-center mb-2 font-medium">
            {error}
          </Text>
        )}

        <Button
          variant="default"
          onPress={handleGitHubSignIn}
          className="bg-[#24292e]" // GitHub brand color
        >
          <View className="flex-row items-center gap-2">
            <SymbolView name="person.fill.badge.plus" size={20} tintColor="white" />
            <Text className="text-white font-bold">Sign in with GitHub</Text>
          </View>
        </Button>

        <Button variant="ghost" onPress={handleSkip}>
          <Text variant="muted">Skip for now</Text>
        </Button>
      </View>

      <View className="mt-12 items-center">
        <Text variant="small" className="text-muted-foreground text-[10px] uppercase tracking-widest">
          Powered by Loom Intelligence
        </Text>
      </View>
    </ScreenContainer>
  );
}
