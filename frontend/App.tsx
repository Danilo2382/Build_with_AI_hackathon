import { StatusBar } from 'expo-status-bar';
import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Animated,
  Easing,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import Svg, { Path } from 'react-native-svg';

type Reminder = { id: string; icon: string; label: string; time: string };

const REMINDERS_PLACEHOLDER: Reminder[] = [
  { id: '1', icon: '💊', label: 'Aspirin', time: '08:00' },
  { id: '2', icon: '🧘', label: 'Stretching', time: '09:00' },
  { id: '3', icon: '💪', label: 'Exercise', time: '10:30' },
  { id: '4', icon: '🏥', label: 'Checkup', time: '14:00' },
  { id: '5', icon: '👥', label: 'Call Ana', time: '16:00' },
];

const GREEN = '#00E676';
const BG = '#060A06';
const CARD = '#0D160D';
const BORDER = '#1C2B1C';

function PulseRing({ animate, delay = 0 }: { animate: boolean; delay?: number }) {
  const scale = useRef(new Animated.Value(1)).current;
  const opacity = useRef(new Animated.Value(0)).current;
  const loopRef = useRef<Animated.CompositeAnimation | null>(null);

  useEffect(() => {
    if (animate) {
      const t = setTimeout(() => {
        scale.setValue(1);
        opacity.setValue(0.55);
        loopRef.current = Animated.loop(
          Animated.parallel([
            Animated.timing(scale, { toValue: 2.4, duration: 1400, useNativeDriver: true }),
            Animated.timing(opacity, { toValue: 0, duration: 1400, useNativeDriver: true }),
          ])
        );
        loopRef.current.start();
      }, delay);
      return () => clearTimeout(t);
    } else {
      loopRef.current?.stop();
      loopRef.current = null;
      Animated.parallel([
        Animated.timing(scale, { toValue: 1, duration: 250, useNativeDriver: true }),
        Animated.timing(opacity, { toValue: 0, duration: 250, useNativeDriver: true }),
      ]).start();
    }
  }, [animate]);

  // Centered inside a 400x400 wrapper; button is 220x220 → offset = (400-220)/2 = 90
  return (
    <Animated.View
      pointerEvents="none"
      style={{
        position: 'absolute',
        top: 90,
        left: 90,
        width: 220,
        height: 220,
        borderRadius: 110,
        borderWidth: 1.5,
        borderColor: GREEN,
        transform: [{ scale }],
        opacity,
      }}
    />
  );
}

function wavyPath(cx: number, cy: number, r: number, amp: number, waves: number, phase: number): string {
  const steps = 256;
  let d = '';
  for (let i = 0; i <= steps; i++) {
    const t = (i / steps) * Math.PI * 2;
    const radius = r + amp * Math.sin(waves * t + phase);
    const x = (cx + radius * Math.cos(t)).toFixed(2);
    const y = (cy + radius * Math.sin(t)).toFixed(2);
    d += i === 0 ? `M ${x} ${y} ` : `L ${x} ${y} `;
  }
  return d + 'Z';
}

function WavyArc({ duration, clockwise, phase, radius, amplitude, waves, opacity }: {
  duration: number;
  clockwise: boolean;
  phase: number;
  radius: number;
  amplitude: number;
  waves: number;
  opacity: Animated.Value;
}) {
  const rotation = useRef(new Animated.Value(0)).current;
  const activeRef = useRef(false);
  const path = useMemo(() => wavyPath(200, 200, radius, amplitude, waves, phase), []);

  useEffect(() => {
    activeRef.current = true;
    const spin = () => {
      if (!activeRef.current) return;
      rotation.setValue(0);
      Animated.timing(rotation, {
        toValue: 1,
        duration,
        easing: Easing.linear,
        useNativeDriver: true,
      }).start(({ finished }) => { if (finished) spin(); });
    };
    spin();
    return () => { activeRef.current = false; rotation.stopAnimation(); };
  }, []);

  const rotate = rotation.interpolate({
    inputRange: [0, 1],
    outputRange: clockwise ? ['0deg', '360deg'] : ['360deg', '0deg'],
  });

  return (
    <Animated.View
      pointerEvents="none"
      style={{ position: 'absolute', top: 0, left: 0, width: 400, height: 400, transform: [{ rotate }], opacity }}
    >
      <Svg width={400} height={400}>
        <Path d={path} stroke={GREEN} strokeWidth={1.5} fill="none" />
      </Svg>
    </Animated.View>
  );
}

function RotatingRing({ listening }: { listening: boolean }) {
  const opacity = useRef(new Animated.Value(0.45)).current;

  useEffect(() => {
    Animated.timing(opacity, {
      toValue: listening ? 0 : 0.45,
      duration: 350,
      useNativeDriver: true,
    }).start();
  }, [listening]);

  return (
    <>
      {/* Two paths same shape, opposite phase — they cross/interlink as they spin at different speeds */}
      <WavyArc duration={11000} clockwise={true}  phase={0}           radius={112} amplitude={8} waves={9} opacity={opacity} />
      <WavyArc duration={15000} clockwise={false} phase={Math.PI}     radius={112} amplitude={8} waves={9} opacity={opacity} />
      {/* Outer ring slightly larger, different frequency */}
      <WavyArc duration={20000} clockwise={true}  phase={Math.PI / 3} radius={122} amplitude={6} waves={6} opacity={opacity} />
    </>
  );
}

export default function App() {
  const [listening, setListening] = useState(false);
  const [remindersOpen, setRemindersOpen] = useState(false);

  const buttonScale = useRef(new Animated.Value(1)).current;
  const breathe = useRef(new Animated.Value(1)).current;
  const hintOpacity = useRef(new Animated.Value(1)).current;
  const glowOpacity = useRef(new Animated.Value(0)).current;

  // Idle breathing
  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(breathe, { toValue: 1.05, duration: 2200, useNativeDriver: true }),
        Animated.timing(breathe, { toValue: 1, duration: 2200, useNativeDriver: true }),
      ])
    );
    loop.start();
    return () => loop.stop();
  }, []);

  const onPressIn = () => {
    setListening(true);
    // Fade hint out → back in with new text handled by state
    Animated.sequence([
      Animated.timing(hintOpacity, { toValue: 0, duration: 150, useNativeDriver: true }),
      Animated.timing(hintOpacity, { toValue: 1, duration: 150, useNativeDriver: true }),
    ]).start();
    // Button squish
    Animated.spring(buttonScale, { toValue: 0.91, useNativeDriver: true, speed: 40, bounciness: 3 }).start();
    // Glow in
    Animated.timing(glowOpacity, { toValue: 1, duration: 300, useNativeDriver: true }).start();
  };

  const onPressOut = () => {
    setListening(false);
    Animated.sequence([
      Animated.timing(hintOpacity, { toValue: 0, duration: 150, useNativeDriver: true }),
      Animated.timing(hintOpacity, { toValue: 1, duration: 150, useNativeDriver: true }),
    ]).start();
    // Button bounce back
    Animated.spring(buttonScale, { toValue: 1, useNativeDriver: true, speed: 18, bounciness: 10 }).start();
    // Glow out
    Animated.timing(glowOpacity, { toValue: 0, duration: 400, useNativeDriver: true }).start();
  };

  const next = REMINDERS_PLACEHOLDER[0];

  return (
    <View style={styles.screen}>
      <StatusBar style="light" />

      <View style={styles.heroArea}>
        {/* micWrapper is 320x320 — rings expand inside here, text is outside */}
        <View style={styles.micWrapper}>
          <Animated.View style={[styles.glow, { opacity: glowOpacity }]} />
          <PulseRing animate={listening} delay={0} />
          <PulseRing animate={listening} delay={450} />
          <PulseRing animate={listening} delay={900} />

          <Animated.View style={{ transform: [{ scale: listening ? buttonScale : breathe }] }}>
            <TouchableOpacity
              style={[styles.micButton, listening && styles.micButtonActive]}
              onPressIn={onPressIn}
              onPressOut={onPressOut}
              activeOpacity={1}
            >
              <Text style={styles.micIcon}>🎙️</Text>
            </TouchableOpacity>
          </Animated.View>

          <RotatingRing listening={listening} />
        </View>

        <Animated.Text style={[styles.micHint, listening && styles.micHintActive, { opacity: hintOpacity }]}>
          {listening ? 'Listening…' : 'Hold to speak'}
        </Animated.Text>
      </View>

      {/* Camera */}
      <TouchableOpacity style={styles.cameraButton} activeOpacity={0.7}>
        <Text style={styles.cameraIcon}>📷</Text>
        <Text style={styles.cameraLabel}>Camera</Text>
      </TouchableOpacity>

      {/* Reminders */}
      <View style={styles.remindersArea}>
        <TouchableOpacity
          style={styles.reminderPill}
          onPress={() => setRemindersOpen((v) => !v)}
          activeOpacity={0.8}
        >
          <Text style={styles.reminderPillIcon}>{next.icon}</Text>
          <Text style={styles.reminderPillText}>{next.label}</Text>
          <Text style={styles.reminderPillTime}>{next.time}</Text>
          <Text style={[styles.reminderChevron, remindersOpen && styles.reminderChevronOpen]}>
            {remindersOpen ? '▲' : '▼'}
          </Text>
        </TouchableOpacity>

        {remindersOpen && (
          <ScrollView style={styles.remindersDropdown} showsVerticalScrollIndicator={false}>
            {REMINDERS_PLACEHOLDER.slice(1).map((r) => (
              <TouchableOpacity key={r.id} style={styles.reminderRow}>
                <Text style={styles.reminderRowIcon}>{r.icon}</Text>
                <Text style={styles.reminderRowLabel}>{r.label}</Text>
                <Text style={styles.reminderRowTime}>{r.time}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: BG,
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingBottom: 44,
    paddingTop: 56,
  },

  heroArea: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },

  // Green radial glow behind button
  glow: {
    position: 'absolute',
    top: 60,   // (400 - 280) / 2
    left: 60,
    width: 280,
    height: 280,
    borderRadius: 140,
    backgroundColor: 'transparent',
    shadowColor: GREEN,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.5,
    shadowRadius: 60,
  },

  micWrapper: {
    width: 400,
    height: 400,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'visible',
    marginBottom: -60,
  },
  micButton: {
    width: 220,
    height: 220,
    borderRadius: 110,
    backgroundColor: CARD,
    borderWidth: 1.5,
    borderColor: BORDER,
    alignItems: 'center',
    justifyContent: 'center',
  },
  micButtonActive: {
    backgroundColor: '#071A0C',
    borderColor: GREEN,
    shadowColor: GREEN,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.7,
    shadowRadius: 28,
    elevation: 20,
  },
  micIcon: {
    fontSize: 84,
  },
  micHint: {
    marginTop: 12,
    fontSize: 13,
    color: '#2E4A2E',
    letterSpacing: 2.5,
    textTransform: 'uppercase',
    fontWeight: '600',
  },
  micHintActive: {
    color: GREEN,
  },

  // Camera
  cameraButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 18,
    paddingHorizontal: 44,
    borderRadius: 40,
    borderWidth: 1,
    borderColor: BORDER,
    marginBottom: 28,
  },
  cameraIcon: {
    fontSize: 26,
  },
  cameraLabel: {
    fontSize: 20,
    color: '#3A5A3A',
    fontWeight: '500',
    letterSpacing: 0.5,
  },

  // Reminders
  remindersArea: {
    width: '100%',
  },
  reminderPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 16,
    backgroundColor: CARD,
    borderWidth: 1,
    borderColor: BORDER,
  },
  reminderPillIcon: {
    fontSize: 18,
  },
  reminderPillText: {
    flex: 1,
    fontSize: 17,
    color: '#4A7A4A',
    fontWeight: '600',
  },
  reminderPillTime: {
    fontSize: 15,
    color: '#2E4A2E',
  },
  reminderChevron: {
    fontSize: 10,
    color: '#2A3A2A',
    marginLeft: 4,
  },
  reminderChevronOpen: {
    color: GREEN,
  },
  remindersDropdown: {
    marginTop: 4,
    maxHeight: 190,
    backgroundColor: CARD,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: BORDER,
    paddingHorizontal: 20,
  },
  reminderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingVertical: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: BORDER,
  },
  reminderRowIcon: {
    fontSize: 16,
  },
  reminderRowLabel: {
    flex: 1,
    fontSize: 16,
    color: '#3A5A3A',
    fontWeight: '500',
  },
  reminderRowTime: {
    fontSize: 14,
    color: '#2A3A2A',
  },
});
