import { View, ScrollView } from 'react-native';
import { Text } from '@/components/ui/text';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface DiffViewerProps {
  diff: string;
  additions: number;
  deletions: number;
  files: string[];
}

export function DiffViewer({ diff, additions, deletions, files }: DiffViewerProps) {

  return (
    <View className="gap-6">
      {/* Stats Summary */}
      <View className="flex-row gap-4 items-center px-1">
        <View className="flex-row items-center gap-1.5">
          <View className="w-3 h-3 rounded-sm bg-green-500" />
          <Text weight="bold" className="text-green-600">+{additions}</Text>
        </View>
        <View className="flex-row items-center gap-1.5">
          <View className="w-3 h-3 rounded-sm bg-red-500" />
          <Text weight="bold" className="text-red-600">-{deletions}</Text>
        </View>
        <Text variant="small" className="text-muted-foreground">in {files.length} files</Text>
      </View>

      {/* Changed Files List */}
      <Card>
        <CardHeader>
          <CardTitle><Text variant="subtitle">Modified Files</Text></CardTitle>
        </CardHeader>
        <CardContent className="gap-2">
          {files.map(f => (
            <View key={f} className="flex-row items-center justify-between py-1">
              <Text variant="small" className="font-mono">{f}</Text>
              <Badge variant="outline" label="MODIFIED" />
            </View>
          ))}
        </CardContent>
      </Card>

      {/* Raw Diff View */}
      <Card className="bg-[#0d1117] border-[#30363d]">
        <CardHeader className="border-b border-[#30363d] py-3">
          <Text className="text-gray-300 font-bold">Raw Unified Diff</Text>
        </CardHeader>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <View className="p-4">
            {diff.split('\n').map((line, i) => {
              let color = 'text-gray-400';
              let bgColor = 'transparent';

              if (line.startsWith('+') && !line.startsWith('+++')) {
                color = 'text-green-400';
                bgColor = 'bg-green-900/20';
              } else if (line.startsWith('-') && !line.startsWith('---')) {
                color = 'text-red-400';
                bgColor = 'bg-red-900/20';
              } else if (line.startsWith('@@')) {
                color = 'text-blue-400';
              }

              return (
                <View key={i} className={`flex-row ${bgColor}`}>
                  <Text
                    variant="small"
                    className={`font-mono ${color}`}
                    style={{ fontSize: 11 }}
                  >
                    {line}
                  </Text>
                </View>
              );
            })}
          </View>
        </ScrollView>
      </Card>
    </View>
  );
}
