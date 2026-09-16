import { create } from 'zustand';

interface SettingsState {
  isMockMode: boolean;
  setMockMode: (isMockMode: boolean) => void;
}

export const useSettingsStore = create<SettingsState>((set) => ({
  isMockMode: false,
  setMockMode: (isMockMode: boolean) => set({ isMockMode }),
}));
