import { useAudioRecorder, RecordingPresets, requestRecordingPermissionsAsync, setAudioModeAsync } from 'expo-audio';
import { Audio } from 'expo-av';
import { CameraView, useCameraPermissions } from 'expo-camera';
import * as Speech from 'expo-speech';
import { StatusBar } from 'expo-status-bar';
import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Animated,
  Dimensions,
  Easing,
  Image,
  Modal,
  ScrollView,
  Share,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

const { width: SCREEN_W, height: SCREEN_H } = Dimensions.get('window');
const PHOTO_W = SCREEN_W * 0.55;
const PHOTO_H = SCREEN_H * 0.35;
import Svg, { Path } from 'react-native-svg';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL ?? 'http://localhost:8080';
const USER_ID = 'nikola';
const BOT_USERNAME = 'Oonook_Hackathon_Bot';

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
  const [setupOpen, setSetupOpen] = useState(false);

  type Medication = { name: string; dose: string; time: string };
  type Contact = { name: string; relationship: string };
  type Appointment = { doctor: string; date: string };

  const [patientName, setPatientName] = useState('');
  const [medications, setMedications] = useState<Medication[]>([{ name: '', dose: '', time: '' }]);
  const [contacts, setContacts] = useState<Contact[]>([{ name: '', relationship: '' }]);
  const [appointments, setAppointments] = useState<Appointment[]>([{ doctor: '', date: '' }]);
  const [thinking, setThinking] = useState(false);
  const [remindersOpen, setRemindersOpen] = useState(false);
  const [cameraOpen, setCameraOpen] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [capturedUri, setCapturedUri] = useState<string | null>(null);
  const [permission, requestPermission] = useCameraPermissions();
  const cameraRef = useRef<CameraView>(null);
  const recorder = useAudioRecorder(RecordingPresets.HIGH_QUALITY);
  const photoScale = useRef(new Animated.Value(1)).current;
  const photoOpacity = useRef(new Animated.Value(1)).current;
  const micTranslateY = useRef(new Animated.Value(0)).current;

  const openCamera = async () => {
    if (!permission?.granted) {
      const result = await requestPermission();
      if (!result.granted) {
        Speech.speak('Camera permission is required.');
        return;
      }
    }
    setCameraOpen(true);
  };

  const takePicture = async () => {
    if (!cameraRef.current || processing) return;
    setProcessing(true);
    try {
      const photo = await cameraRef.current.takePictureAsync({ base64: true, quality: 0.7 });
      setCameraOpen(false);

      // Appear at natural size, linger, then shrink away
      photoScale.setValue(1);
      photoOpacity.setValue(0);
      micTranslateY.setValue(0);
      setCapturedUri(photo?.uri ?? null);

      Animated.timing(photoOpacity, { toValue: 1, duration: 300, useNativeDriver: true }).start(() => {
        setTimeout(() => {
          Animated.parallel([
            Animated.timing(photoOpacity, { toValue: 0, duration: 500, useNativeDriver: true }),
            Animated.spring(photoScale, { toValue: 1 / 10, useNativeDriver: true, speed: 3, bounciness: 0 }),
          ]).start(() => setCapturedUri(null));
        }, 2500);
      });

      Speech.speak('Let me take a look at that…');
      console.log('[CAM] base64 length:', photo?.base64?.length);
      console.log('[CAM] posting to backend...');
      const res = await fetch(`${BACKEND_URL}/vision/image`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: USER_ID, image_base64: photo?.base64 }),
      });
      console.log('[CAM] backend status:', res.status);
      const data = await res.json();
      console.log('[CAM] backend response:', data);
      const text = data.fallback_response ?? data.response ?? 'Sorry, I could not analyse that.';
      Speech.speak(text);
    } catch (e) {
      console.error('[CAM] error:', e);
      Speech.speak('Sorry, I cannot connect. Please try again.');
    } finally {
      setProcessing(false);
    }
  };

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

  const onPressIn = async () => {
    setListening(true);
    Animated.sequence([
      Animated.timing(hintOpacity, { toValue: 0, duration: 150, useNativeDriver: true }),
      Animated.timing(hintOpacity, { toValue: 1, duration: 150, useNativeDriver: true }),
    ]).start();
    Animated.spring(buttonScale, { toValue: 0.91, useNativeDriver: true, speed: 40, bounciness: 3 }).start();
    Animated.timing(glowOpacity, { toValue: 1, duration: 300, useNativeDriver: true }).start();

    try {
      const { granted } = await requestRecordingPermissionsAsync();
      console.log('[MIC] permission granted:', granted);
      if (!granted) { Speech.speak('Microphone permission is required.'); return; }
      await setAudioModeAsync({ allowsRecording: true, playsInSilentMode: true });
      await recorder.prepareToRecordAsync();
      console.log('[MIC] prepared, starting record');
      recorder.record();
      console.log('[MIC] recording started');
    } catch (e) {
      console.error('[MIC] onPressIn error:', e);
      Speech.speak('Could not start recording.');
    }
  };

  const onPressOut = async () => {
    setListening(false);
    Animated.sequence([
      Animated.timing(hintOpacity, { toValue: 0, duration: 150, useNativeDriver: true }),
      Animated.timing(hintOpacity, { toValue: 1, duration: 150, useNativeDriver: true }),
    ]).start();
    Animated.spring(buttonScale, { toValue: 1, useNativeDriver: true, speed: 18, bounciness: 10 }).start();
    Animated.timing(glowOpacity, { toValue: 0, duration: 400, useNativeDriver: true }).start();
    Animated.sequence([
      Animated.timing(hintOpacity, { toValue: 0, duration: 150, useNativeDriver: true }),
      Animated.timing(hintOpacity, { toValue: 1, duration: 150, useNativeDriver: true }),
    ]).start();

    try {
      await recorder.stop();
      const uri = recorder.uri;
      console.log('[MIC] stopped, uri:', uri);
      if (!uri) { console.warn('[MIC] no URI after stop'); return; }

      setThinking(true);
      Animated.sequence([
        Animated.timing(hintOpacity, { toValue: 0, duration: 150, useNativeDriver: true }),
        Animated.timing(hintOpacity, { toValue: 1, duration: 150, useNativeDriver: true }),
      ]).start();
      // thinking indicator — audio response replaces spoken feedback

      console.log('[MIC] fetching audio file...');
      const response = await fetch(uri);
      console.log('[MIC] fetch status:', response.status);
      const blob = await response.blob();
      console.log('[MIC] blob size:', blob.size, 'type:', blob.type);
      const mimeType = blob.type || 'audio/mp4';
      const base64 = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => {
          const result = (reader.result as string).split(',')[1];
          console.log('[MIC] base64 length:', result?.length);
          resolve(result);
        };
        reader.onerror = reject;
        reader.readAsDataURL(blob);
      });

      try {
        console.log('[MIC] posting to backend...');
        const res = await fetch(`${BACKEND_URL}/chat/voice`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: USER_ID, audio_base64: base64, mime_type: mimeType }),
        });
        console.log('[MIC] backend status:', res.status);
        const data = await res.json();
        console.log('[MIC] backend response:', data);
        await setAudioModeAsync({ allowsRecording: false, playsInSilentMode: true });
        if (data.audio_base64) {
          const { sound } = await Audio.Sound.createAsync(
            { uri: `data:audio/mp3;base64,${data.audio_base64}` },
            { shouldPlay: true, volume: 1.0 }
          );
          sound.setOnPlaybackStatusUpdate((status) => {
            if (status.isLoaded && status.didJustFinish) sound.unloadAsync();
          });
        } else {
          const text = data.fallback_response ?? data.response;
          if (text) Speech.speak(text);
        }
      } catch (e) {
        console.error('[MIC] backend error:', e);
        Speech.speak('Sorry, I cannot connect. Please try again.');
      } finally {
        setThinking(false);
        Animated.sequence([
          Animated.timing(hintOpacity, { toValue: 0, duration: 150, useNativeDriver: true }),
          Animated.timing(hintOpacity, { toValue: 1, duration: 150, useNativeDriver: true }),
        ]).start();
      }
    } catch {
      setThinking(false);
      Speech.speak('Sorry, something went wrong.');
    }
  };

  const next = REMINDERS_PLACEHOLDER[0];

  return (
    <View style={styles.screen}>
      <StatusBar style="light" />

      <TouchableOpacity
        style={styles.shareButton}
        onPress={async () => {
          try {
            const link = `https://t.me/${BOT_USERNAME}?start=${USER_ID}`;
            await Share.share({ message: `Please click this link and press START in Telegram to become my Oonook Caretaker: ${link}` });
          } catch {
            // user cancelled or error — no feedback needed
          }
        }}
        onLongPress={() => setSetupOpen(true)}
        delayLongPress={5000}
      >
        <Text style={styles.shareIcon}>🔗</Text>
      </TouchableOpacity>

      <Modal visible={setupOpen} animationType="slide" onRequestClose={() => setSetupOpen(false)}>
        <View style={styles.setupScreen}>
          <View style={styles.setupHeader}>
            <Text style={styles.setupTitle}>Caretaker Setup</Text>
            <TouchableOpacity style={styles.setupClose} onPress={() => setSetupOpen(false)}>
              <Text style={styles.setupCloseText}>✕</Text>
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.setupScroll} showsVerticalScrollIndicator={false}>

            {/* Patient name */}
            <Text style={styles.setupSectionLabel}>👤 Patient Name</Text>
            <TextInput
              style={styles.setupInput}
              placeholder="e.g. John"
              placeholderTextColor="#3A5A3A"
              value={patientName}
              onChangeText={setPatientName}
            />

            {/* Medications */}
            <Text style={styles.setupSectionLabel}>💊 Medications</Text>
            {medications.map((med, i) => (
              <View key={i} style={styles.setupRow}>
                <TextInput style={[styles.setupInput, styles.setupInputFlex]} placeholder="Name" placeholderTextColor="#3A5A3A" value={med.name}
                  onChangeText={v => setMedications(prev => prev.map((m, j) => j === i ? { ...m, name: v } : m))} />
                <TextInput style={[styles.setupInput, styles.setupInputSmall]} placeholder="Dose" placeholderTextColor="#3A5A3A" value={med.dose}
                  onChangeText={v => setMedications(prev => prev.map((m, j) => j === i ? { ...m, dose: v } : m))} />
                <TextInput style={[styles.setupInput, styles.setupInputSmall]} placeholder="Time" placeholderTextColor="#3A5A3A" value={med.time}
                  onChangeText={v => setMedications(prev => prev.map((m, j) => j === i ? { ...m, time: v } : m))} />
                {medications.length > 1 && (
                  <TouchableOpacity onPress={() => setMedications(prev => prev.filter((_, j) => j !== i))}>
                    <Text style={styles.setupRemove}>✕</Text>
                  </TouchableOpacity>
                )}
              </View>
            ))}
            <TouchableOpacity style={styles.setupAddBtn} onPress={() => setMedications(prev => [...prev, { name: '', dose: '', time: '' }])}>
              <Text style={styles.setupAddText}>+ Add Medication</Text>
            </TouchableOpacity>

            {/* Contacts */}
            <Text style={styles.setupSectionLabel}>👥 Family & Friends</Text>
            {contacts.map((c, i) => (
              <View key={i} style={styles.setupRow}>
                <TextInput style={[styles.setupInput, styles.setupInputFlex]} placeholder="Name" placeholderTextColor="#3A5A3A" value={c.name}
                  onChangeText={v => setContacts(prev => prev.map((m, j) => j === i ? { ...m, name: v } : m))} />
                <TextInput style={[styles.setupInput, styles.setupInputFlex]} placeholder="Relationship" placeholderTextColor="#3A5A3A" value={c.relationship}
                  onChangeText={v => setContacts(prev => prev.map((m, j) => j === i ? { ...m, relationship: v } : m))} />
                {contacts.length > 1 && (
                  <TouchableOpacity onPress={() => setContacts(prev => prev.filter((_, j) => j !== i))}>
                    <Text style={styles.setupRemove}>✕</Text>
                  </TouchableOpacity>
                )}
              </View>
            ))}
            <TouchableOpacity style={styles.setupAddBtn} onPress={() => setContacts(prev => [...prev, { name: '', relationship: '' }])}>
              <Text style={styles.setupAddText}>+ Add Contact</Text>
            </TouchableOpacity>

            {/* Appointments */}
            <Text style={styles.setupSectionLabel}>🏥 Upcoming Appointments</Text>
            {appointments.map((a, i) => (
              <View key={i} style={styles.setupRow}>
                <TextInput style={[styles.setupInput, styles.setupInputFlex]} placeholder="Doctor / Specialist" placeholderTextColor="#3A5A3A" value={a.doctor}
                  onChangeText={v => setAppointments(prev => prev.map((m, j) => j === i ? { ...m, doctor: v } : m))} />
                <TextInput style={[styles.setupInput, styles.setupInputSmall]} placeholder="Date" placeholderTextColor="#3A5A3A" value={a.date}
                  onChangeText={v => setAppointments(prev => prev.map((m, j) => j === i ? { ...m, date: v } : m))} />
                {appointments.length > 1 && (
                  <TouchableOpacity onPress={() => setAppointments(prev => prev.filter((_, j) => j !== i))}>
                    <Text style={styles.setupRemove}>✕</Text>
                  </TouchableOpacity>
                )}
              </View>
            ))}
            <TouchableOpacity style={styles.setupAddBtn} onPress={() => setAppointments(prev => [...prev, { doctor: '', date: '' }])}>
              <Text style={styles.setupAddText}>+ Add Appointment</Text>
            </TouchableOpacity>

            {/* Save */}
            <TouchableOpacity style={styles.setupSaveBtn} onPress={() => setSetupOpen(false)}>
              <Text style={styles.setupSaveText}>Save & Close</Text>
            </TouchableOpacity>

            <View style={{ height: 40 }} />
          </ScrollView>
        </View>
      </Modal>

      <View style={styles.heroArea}>
        {/* micWrapper is 320x320 — rings expand inside here, text is outside */}
        <View style={styles.micWrapper}>
          <Animated.View style={[styles.glow, { opacity: glowOpacity }]} />
          <PulseRing animate={listening || thinking} delay={0} />
          <PulseRing animate={listening || thinking} delay={450} />
          <PulseRing animate={listening || thinking} delay={900} />

          <Animated.View style={{ transform: [{ scale: listening ? buttonScale : breathe }] }}>
            <TouchableOpacity
              style={[styles.micButton, listening && styles.micButtonActive]}
              onPressIn={onPressIn}
              onPressOut={onPressOut}
              activeOpacity={1}
              disabled={thinking}
            >
              <Text style={styles.micIcon}>🎙️</Text>
            </TouchableOpacity>
          </Animated.View>

          <RotatingRing listening={listening} />
        </View>

        <Animated.Text style={[styles.micHint, (listening || thinking) && styles.micHintActive, { opacity: hintOpacity }]}>
          {listening ? 'Listening…' : thinking ? 'Thinking…' : 'Hold to speak'}
        </Animated.Text>
      </View>

      {/* Camera */}
      <TouchableOpacity style={styles.cameraButton} activeOpacity={0.7} onPress={openCamera}>
        <Text style={styles.cameraIcon}>📷</Text>
        <Text style={styles.cameraLabel}>Camera</Text>
      </TouchableOpacity>

      {/* Camera modal */}
      <Modal visible={cameraOpen} animationType="slide" onRequestClose={() => setCameraOpen(false)}>
        <View style={styles.cameraScreen}>
          <CameraView ref={cameraRef} style={styles.cameraPreview} facing="back" />
          <View style={styles.cameraControls}>
            <TouchableOpacity style={styles.closeButton} onPress={() => setCameraOpen(false)}>
              <Text style={styles.closeButtonText}>✕</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.captureButton} onPress={takePicture} disabled={processing}>
              <View style={styles.captureInner} />
            </TouchableOpacity>
            <View style={{ width: 56 }} />
          </View>
        </View>
      </Modal>

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

      {/* Photo shrink animation overlay */}
      {capturedUri && (
        <Animated.View
          pointerEvents="none"
          style={[styles.photoOverlay, { transform: [{ scale: photoScale }], opacity: photoOpacity }]}
        >
          <View style={styles.photoFrame}>
            <Image source={{ uri: capturedUri }} style={styles.photoOverlayImage} />
          </View>
        </Animated.View>
      )}
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

  // Camera modal
  cameraScreen: {
    flex: 1,
    backgroundColor: '#000000',
  },
  cameraPreview: {
    flex: 1,
  },
  cameraControls: {
    position: 'absolute',
    bottom: 48,
    left: 0,
    right: 0,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 40,
  },
  closeButton: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: 'rgba(255,255,255,0.15)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  closeButtonText: {
    fontSize: 22,
    color: '#FFFFFF',
  },
  captureButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    borderWidth: 3,
    borderColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  captureInner: {
    width: 62,
    height: 62,
    borderRadius: 31,
    backgroundColor: '#FFFFFF',
  },

  photoOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    alignItems: 'center',
    justifyContent: 'center',
  },
  photoFrame: {
    width: PHOTO_W,
    height: PHOTO_H,
    borderRadius: 20,
    borderWidth: 1.5,
    borderColor: GREEN,
    padding: 4,
    backgroundColor: CARD,
    shadowColor: GREEN,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.5,
    shadowRadius: 20,
    elevation: 12,
  },
  photoOverlayImage: {
    width: '100%',
    height: '100%',
    borderRadius: 16,
  },

  shareButton: {
    position: 'absolute',
    top: 56,
    right: 20,
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: CARD,
    borderWidth: 1,
    borderColor: BORDER,
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 10,
  },
  shareIcon: {
    fontSize: 20,
  },

  setupScreen: {
    flex: 1,
    backgroundColor: BG,
    paddingTop: 56,
  },
  setupHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    marginBottom: 16,
  },
  setupTitle: {
    fontSize: 26,
    fontWeight: '700',
    color: GREEN,
    letterSpacing: 0.5,
  },
  setupClose: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: CARD,
    borderWidth: 1,
    borderColor: BORDER,
    alignItems: 'center',
    justifyContent: 'center',
  },
  setupCloseText: {
    fontSize: 18,
    color: '#FFFFFF',
  },
  setupScroll: {
    flex: 1,
    paddingHorizontal: 20,
  },
  setupSectionLabel: {
    fontSize: 16,
    fontWeight: '700',
    color: GREEN,
    letterSpacing: 1,
    textTransform: 'uppercase',
    marginTop: 24,
    marginBottom: 8,
  },
  setupInput: {
    backgroundColor: CARD,
    borderWidth: 1,
    borderColor: BORDER,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    color: '#DDDDDD',
    fontSize: 16,
    marginBottom: 8,
  },
  setupInputFlex: {
    flex: 1,
    marginRight: 8,
    marginBottom: 0,
  },
  setupInputSmall: {
    width: 90,
    marginRight: 8,
    marginBottom: 0,
  },
  setupRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  setupRemove: {
    fontSize: 16,
    color: '#555555',
    paddingHorizontal: 4,
  },
  setupAddBtn: {
    paddingVertical: 10,
    marginBottom: 4,
  },
  setupAddText: {
    fontSize: 15,
    color: '#3A5A3A',
    fontWeight: '600',
  },
  setupSaveBtn: {
    marginTop: 32,
    backgroundColor: GREEN,
    borderRadius: 16,
    paddingVertical: 18,
    alignItems: 'center',
  },
  setupSaveText: {
    fontSize: 18,
    fontWeight: '700',
    color: '#000000',
    letterSpacing: 0.5,
  },
});
