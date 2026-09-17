import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Text } from '../../components/ui/text';
import { EmptyState } from '../../components/ui/empty-state';
import { ErrorState } from '../../components/ui/error-state';
import { LoadingState } from '../../components/ui/loading-state';
import { RetryButton } from '../../components/ui/retry-button';
import { LoadingIndicator } from '../../components/ui/loading-indicator';
import { Input } from '../../components/ui/input';

describe('UI Components', () => {
  describe('Card', () => {
    it('renders card with children', () => {
      const { getByText } = render(
        <Card>
          <CardHeader><CardTitle><Text>Title</Text></CardTitle></CardHeader>
          <CardContent><Text>Content</Text></CardContent>
          <CardFooter><Text>Footer</Text></CardFooter>
        </Card>
      );
      expect(getByText('Title')).toBeTruthy();
      expect(getByText('Content')).toBeTruthy();
      expect(getByText('Footer')).toBeTruthy();
    });
  });

  describe('Badge', () => {
    it('renders badge label', () => {
      const { getByText } = render(<Badge label="New" />);
      expect(getByText('New')).toBeTruthy();
    });
  });

  describe('EmptyState', () => {
    it('renders title and description', () => {
      const { getByText } = render(
        <EmptyState title="Empty" description="Nothing here" />
      );
      expect(getByText('Empty')).toBeTruthy();
      expect(getByText('Nothing here')).toBeTruthy();
    });
  });

  describe('ErrorState', () => {
    it('renders message and retry button', () => {
      const onRetry = jest.fn();
      const { getByText } = render(
        <ErrorState title="Oops" message="Error" onRetry={onRetry} />
      );
      expect(getByText('Oops')).toBeTruthy();
      expect(getByText('Error')).toBeTruthy();

      fireEvent.press(getByText('Retry'));
      expect(onRetry).toHaveBeenCalled();
    });
  });

  describe('LoadingState', () => {
    it('renders message', () => {
      const { getByText } = render(<LoadingState message="Loading..." />);
      expect(getByText('Loading...')).toBeTruthy();
    });
  });

  describe('RetryButton', () => {
    it('handles press', () => {
      const onPress = jest.fn();
      const { getByText } = render(<RetryButton onPress={onPress} />);
      fireEvent.press(getByText('Retry'));
      expect(onPress).toHaveBeenCalled();
    });
  });

  describe('LoadingIndicator', () => {
      it('renders without crashing', () => {
          render(<LoadingIndicator />);
      });
  });

  describe('Input', () => {
      it('handles focus and blur', () => {
          const { getByPlaceholderText } = render(<Input placeholder="Type here" />);
          const input = getByPlaceholderText('Type here');

          fireEvent(input, 'focus');
          fireEvent(input, 'blur');
      });
  });
});
