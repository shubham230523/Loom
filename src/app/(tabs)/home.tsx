import { View } from 'react-native';
import { ScreenContainer } from '@/components/ui/screen-container';
import { Text } from '@/components/ui/text';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { EmptyState } from '@/components/ui/empty-state';
import { Divider } from '@/components/ui/divider';
import { Button } from '@/components/ui/button';

export default function HomeScreen() {
  return (
    <ScreenContainer scrollable className="py-6" maxWidth={1200}>
      <View className="mb-8">
        <Text variant="title">Dashboard</Text>
        <Text variant="muted">Overview of your autonomous collaboration.</Text>
      </View>

      <View className="flex-col lg:flex-row gap-8">
        {/* Main Content Area: Repositories & Activity */}
        <View className="flex-[2] gap-8">
          {/* Quick Actions / Featured Sections */}
          <View className="flex-row gap-4 flex-wrap">
            <Card className="flex-1 min-w-[300px]">
              <CardHeader>
                <CardTitle>
                  <Text variant="subtitle">Auto Contribute</Text>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Text variant="small" className="mb-4">
                  Automate your contribution workflow with intelligent agents.
                </Text>
                <Button variant="outline" size="sm" label="Setup Workflow" />
              </CardContent>
            </Card>

            <Card className="flex-1 min-w-[300px]">
              <CardHeader>
                <CardTitle>
                  <Text variant="subtitle">Discover Projects</Text>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Text variant="small" className="mb-4">
                  Find repositories where your contributions can make an impact.
                </Text>
                <Button variant="outline" size="sm" label="Explore Feed" />
              </CardContent>
            </Card>
          </View>

          <Divider />

          {/* Code/Repos Section (Prioritized for Desktop) */}
          <View>
            <Text variant="subtitle" className="mb-4">Monitored Repositories</Text>
            <EmptyState
              title="No repositories connected"
              description="Connect repositories to monitor code changes and diffs."
              icon="tray"
              className="min-h-[240px] border border-dashed border-border rounded-xl"
            />
          </View>

          {/* Recent Contributions (Mobile Priority) */}
          <View className="lg:hidden">
            <Text variant="subtitle" className="mb-4">Recent Contributions</Text>
            <EmptyState
              title="No recent contributions"
              description="Start contributing to see your activity here."
              icon="plus.square.fill"
              className="min-h-[200px] border border-dashed border-border rounded-xl"
            />
          </View>
        </View>

        {/* Desktop Sidebar Area: Agents & Activity Monitoring */}
        <View className="flex-1 gap-8">
          {/* Recent Contributions (Desktop Secondary) */}
          <View className="hidden lg:flex">
            <Text variant="subtitle" className="mb-4">Recent Contributions</Text>
            <EmptyState
              title="No activity"
              description="Your contributions will appear here."
              icon="plus.square.fill"
              className="min-h-[160px] border border-dashed border-border rounded-xl"
            />
          </View>

          {/* Active Agents (Prioritized for Desktop) */}
          <View>
            <Text variant="subtitle" className="mb-4">Active Agents</Text>
            <EmptyState
              title="No agents running"
              description="Active autonomous agents."
              icon="cpu"
              className="min-h-[200px] border border-dashed border-border rounded-xl"
            />
          </View>

          {/* Pull Requests */}
          <View>
            <Text variant="subtitle" className="mb-4">Pull Requests</Text>
            <EmptyState
              title="No open PRs"
              icon="arrow.triangle.pull"
              className="min-h-[200px] border border-dashed border-border rounded-xl"
            />
          </View>
        </View>
      </View>
    </ScreenContainer>
  );
}
