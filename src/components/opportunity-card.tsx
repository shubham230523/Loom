import { View } from 'react-native';
import { SymbolView } from 'expo-symbols';
import { Opportunity } from '@/types/opportunity';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Text } from '@/components/ui/text';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Divider } from '@/components/ui/divider';
import { useTheme } from '@/hooks/use-theme';

interface OpportunityCardProps {
  opportunity: Opportunity;
  isAnalyzing?: boolean;
  onAnalyze: (id: string) => void;
  onStart: (id: string) => void;
}

export function OpportunityCard({ opportunity, isAnalyzing, onAnalyze, onStart }: OpportunityCardProps) {
  const theme = useTheme();

  const getScoreColor = (score: number) => {
    if (score >= 80) return '#22C55E'; // green-500
    if (score >= 50) return '#EAB308'; // yellow-500
    return '#EF4444'; // red-500
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'bug': return 'ladybug.fill';
      case 'feature': return 'plus.circle.fill';
      case 'refactor': return 'hammer.fill';
      case 'documentation': return 'doc.text.fill';
      case 'testing': return 'checkmark.shield.fill';
      default: return 'lightbulb.fill';
    }
  };

  return (
    <Card className="mb-4">
      <CardHeader className="flex-row items-center justify-between pb-2">
        <View className="flex-row items-center gap-2">
          <SymbolView
            name={getTypeIcon(opportunity.type)}
            size={18}
            tintColor={theme.primary}
          />
          <Badge variant="outline" label={opportunity.type.toUpperCase()} />
        </View>
        <View className="flex-row items-center gap-1">
          <Text variant="small" weight="bold" style={{ color: getScoreColor(opportunity.score) }}>
            {opportunity.score > 0 ? `${Math.round(opportunity.score)}` : 'Pending Audit'}
          </Text>
          {opportunity.score > 0 && (
             <SymbolView name="bolt.fill" size={12} tintColor={getScoreColor(opportunity.score)} />
          )}
        </View>
      </CardHeader>

      <CardContent>
        <Text weight="bold" className="text-lg mb-2">{opportunity.title}</Text>
        <Text variant="small" className="text-muted-foreground mb-4" numberOfLines={3}>
          {opportunity.description}
        </Text>

        <View className="flex-row flex-wrap gap-4 mb-4">
          <Metric label="Impact" value={opportunity.impact} />
          <Metric label="Difficulty" value={opportunity.difficulty} />
          <Metric
            label="Confidence"
            value={`${Math.round(opportunity.confidence * 100)}%`}
          />
        </View>

        <Divider className="mb-4" />

        <View className="flex-row gap-3">
          <Button
            variant="outline"
            size="sm"
            className="flex-1"
            label={isAnalyzing ? "Analyzing..." : "Analyze"}
            loading={isAnalyzing}
            disabled={isAnalyzing}
            onPress={() => onAnalyze(opportunity.id)}
          />
          <Button
            size="sm"
            className="flex-1"
            label="Start Contribution"
            disabled={isAnalyzing}
            onPress={() => onStart(opportunity.id)}
          />
        </View>
      </CardContent>
    </Card>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <View>
      <Text variant="small" className="text-muted-foreground mb-0.5">{label}</Text>
      <Text weight="medium">{value}</Text>
    </View>
  );
}
