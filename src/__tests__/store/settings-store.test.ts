import { useSettingsStore } from '../../store/settings-store';

describe('Settings Store', () => {
  it('should have initial mock mode as false', () => {
    const { isMockMode } = useSettingsStore.getState();
    expect(isMockMode).toBe(false);
  });

  it('should update mock mode', () => {
    useSettingsStore.getState().setMockMode(true);
    expect(useSettingsStore.getState().isMockMode).toBe(true);

    useSettingsStore.getState().setMockMode(false);
    expect(useSettingsStore.getState().isMockMode).toBe(false);
  });
});
