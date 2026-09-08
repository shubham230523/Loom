import { View, Pressable, Image } from 'react-native';
import { Link } from 'expo-router';
import { SymbolView } from 'expo-symbols';
import { ScreenContainer } from '@/components/ui/screen-container';
import { Text } from '@/components/ui/text';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Divider } from '@/components/ui/divider';
import { useTheme } from '@/hooks/use-theme';
import { useAuthStore } from '@/store/auth-store';
import { AuthService } from '@/services/auth.service';

export default function ProfileScreen() {
  const theme = useTheme();
  const { user } = useAuthStore();

  const handleGitHubConnect = () => {
    AuthService.startGitHubLogin();
  };

  return (
    <ScreenContainer scrollable className="pt-16 pb-6">
      {/* Profile Header */}
      <View className="items-center mb-8">
        <View className="w-24 h-24 rounded-full bg-muted items-center justify-center mb-4 border border-border overflow-hidden">
          {user?.avatar_url ? (
            <Image
              source={{ uri: user.avatar_url }}
              className="w-full h-full"
              resizeMode="cover"
            />
          ) : (
            <SymbolView name="person.fill" size={48} tintColor={theme.textSecondary} />
          )}
        </View>
        <Text variant="subtitle" className="text-2xl font-bold">
          {user?.display_name || user?.username || 'Username'}
        </Text>
        <Text variant="muted">@{user?.username || 'username'}</Text>
      </View>

      <View className="flex-col lg:flex-row gap-6">
        {/* GitHub Connection Status */}
        <Card className="flex-1">
          <CardHeader className="flex-row items-center justify-between">
            <View className="flex-row items-center gap-3">
              <SymbolView name="link" size={20} tintColor={theme.text} />
              <CardTitle>
                <Text variant="subtitle">GitHub Connection</Text>
              </CardTitle>
            </View>
            <Badge
              variant={user?.github_user_id ? "default" : "outline"}
              label={user?.github_user_id ? "Connected" : "Not Connected"}
            />
          </CardHeader>
          <CardContent>
            <Text variant="small" className="text-muted-foreground mb-4">
              {user?.github_user_id
                ? "Your GitHub account is connected. You can now enable autonomous contributions."
                : "Connect your GitHub account to enable autonomous contributions and project discovery."
              }
            </Text>
            {!user?.github_user_id && (
              <Pressable
                className="bg-[#24292e] py-2 px-4 rounded-lg self-start"
                onPress={handleGitHubConnect}
              >
                <Text className="text-white font-semibold">Connect Account</Text>
              </Pressable>
            )}
          </CardContent>
        </Card>

        {/* Contribution Statistics */}
        <Card className="flex-1">
          <CardHeader>
            <CardTitle>
              <Text variant="subtitle">Statistics</Text>
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-row justify-between items-center h-full">
            <View className="items-center flex-1">
              <Text className="text-2xl font-bold">0</Text>
              <Text variant="small" className="text-muted-foreground">Contributions</Text>
            </View>
            <Divider orientation="vertical" className="h-12 mx-2" />
            <View className="items-center flex-1">
              <Text className="text-2xl font-bold">0</Text>
              <Text variant="small" className="text-muted-foreground">Agents Run</Text>
            </View>
            <Divider orientation="vertical" className="h-12 mx-2" />
            <View className="items-center flex-1">
              <Text className="text-2xl font-bold">0</Text>
              <Text variant="small" className="text-muted-foreground">Impact Score</Text>
            </View>
          </CardContent>
        </Card>
      </View>

      {/* Settings Entry */}
      <View className="mt-8">
        <Link href="/settings" asChild>
          <Pressable className="flex-row items-center justify-between p-4 bg-card rounded-xl border border-border active:opacity-70">
            <View className="flex-row items-center gap-3">
              <SymbolView name="gearshape.fill" size={20} tintColor={theme.text} />
              <Text variant="subtitle">Settings</Text>
            </View>
            <SymbolView name="chevron.right" size={16} tintColor={theme.textSecondary} />
          </Pressable>
        </Link>
      </View>
    </ScreenContainer>
  );
}
