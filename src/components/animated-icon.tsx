import * as SplashScreen from 'expo-splash-screen';
import { useState, useEffect } from 'react';
import { StyleSheet, View } from 'react-native';
import Animated, { FadeIn, FadeOut } from 'react-native-reanimated';
import { scheduleOnRN } from 'react-native-worklets';

const DURATION = 600;

export function AnimatedSplashOverlay() {
  const [visible, setVisible] = useState(true);
  const [shouldUnmount, setShouldUnmount] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      SplashScreen.hideAsync().finally(() => {
        setTimeout(() => {
          setShouldUnmount(true);
        }, 1000);
      });
    }, 500);
    return () => clearTimeout(timer);
  }, []);

  if (!visible) return null;

  return (
    <View style={StyleSheet.absoluteFill} pointerEvents={shouldUnmount ? 'none' : 'auto'}>
      {!shouldUnmount && (
        <Animated.View
          exiting={FadeOut.duration(DURATION).withCallback((finished) => {
            'worklet';
            if (finished) {
              scheduleOnRN(setVisible, false);
            }
          })}
          style={styles.splashOverlay}>
          <View style={styles.contentContainer}>
            <Animated.Text
              entering={FadeIn.duration(800)}
              style={styles.logoText}
            >
              LOOM
            </Animated.Text>
          </View>
        </Animated.View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  contentContainer: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  logoText: {
    fontSize: 48,
    fontWeight: '900',
    color: '#FFFFFF',
    letterSpacing: 8,
    fontFamily: 'system-ui',
  },
  splashOverlay: {
    ...StyleSheet.absoluteFill,
    backgroundColor: '#208AEF',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  },
});
