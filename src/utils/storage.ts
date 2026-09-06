import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';

/**
 * A cross-platform storage utility.
 * Uses SecureStore on native platforms for encrypted storage.
 * Falls back to localStorage on web (Note: not encrypted).
 */
export const storage = {
  /**
   * Saves a value to storage.
   */
  setItem: async (key: string, value: string): Promise<void> => {
    if (Platform.OS === 'web') {
      try {
        localStorage.setItem(key, value);
      } catch (e) {
        console.error('Error saving to localStorage', e);
      }
    } else {
      await SecureStore.setItemAsync(key, value);
    }
  },

  /**
   * Retrieves a value from storage.
   */
  getItem: async (key: string): Promise<string | null> => {
    if (Platform.OS === 'web') {
      try {
        return localStorage.getItem(key);
      } catch (e) {
        console.error('Error reading from localStorage', e);
        return null;
      }
    } else {
      return await SecureStore.getItemAsync(key);
    }
  },

  /**
   * Deletes a value from storage.
   */
  deleteItem: async (key: string): Promise<void> => {
    if (Platform.OS === 'web') {
      try {
        localStorage.removeItem(key);
      } catch (e) {
        console.error('Error deleting from localStorage', e);
      }
    } else {
      await SecureStore.deleteItemAsync(key);
    }
  },
};
