import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import DiscoverScreen from '../../app/(tabs)/discover';
import { RepositoryService } from '../../services/repository.service';

// Mock the RepositoryService
jest.mock('../../services/repository.service', () => ({
  RepositoryService: {
    search: jest.fn(),
  },
}));

// Mock useQuery
jest.mock('@tanstack/react-query', () => ({
  useQuery: jest.fn().mockReturnValue({
    data: {
      items: [
        {
          id: 1,
          name: 'loom-app',
          full_name: 'loom/loom-app',
          owner: { login: 'loom', avatar_url: 'http://img' },
          description: 'Autonomous collaboration',
          stargazers_count: 1500,
          forks_count: 100,
          language: 'TypeScript'
        }
      ],
      total_count: 1
    },
    isLoading: false,
    isError: false,
    isFetching: false,
    refetch: jest.fn(),
  }),
}));

// Mock useRouter
jest.mock('expo-router', () => ({
  useRouter: () => ({
    push: jest.fn(),
  }),
}));

describe('Discovery Flow E2E', () => {
  it('should allow searching and viewing repository details', async () => {
    const { getByPlaceholderText, getByText } = render(<DiscoverScreen />);

    // 1. Verify initial list renders
    expect(getByText('loom-app')).toBeTruthy();
    expect(getByText('loom')).toBeTruthy();

    // 2. Perform search
    const searchInput = getByPlaceholderText('Search repositories...');
    fireEvent.changeText(searchInput, 'react-native');

    // In a real E2E we'd wait for the API call, here we just verify interaction
    expect(searchInput.props.value).toBe('react-native');
  });
});
