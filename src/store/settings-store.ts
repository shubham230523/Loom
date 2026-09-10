import { create } from 'zustand';

interface SettingsState {
  isMockMode: boolean;
  setMockMode: (isMockMode: boolean) => void;
}

export const useSettingsStore = create<SettingsState>((set) => ({
  isMockMode: true, // Default to true as per user request
  setMockMode: (isMockMode: boolean) => set({ isMockMode }),
}));
