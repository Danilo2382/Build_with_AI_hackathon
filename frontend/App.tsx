import { useAudioRecorder, RecordingPresets, requestRecordingPermissionsAsync, setAudioModeAsync } from 'expo-audio';
import { Audio } from 'expo-av';
import { CameraView, useCameraPermissions } from 'expo-camera';
import * as Speech from 'expo-speech';
import { StatusBar } from 'expo-status-bar';
import { useCallback, useEffect, useRef, useState } from 'react';
import {
  Animated,
  Easing,
  Image,
  Modal,
  ScrollView,
  Share,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import Svg, { Circle, Path } from 'react-native-svg';

import { C, PHOTO_H, PHOTO_W, pm, ps, s } from './styles';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL ?? 'http://10.157.195.91:8080';
const USER_ID = 'nikola';
const BOT_USERNAME = 'Oonook_Hackathon_Bot';

export type Reminder = {
  id: string;
  icon: string;
  label: string;
  time: string;
  type: 'medication' | 'exercise' | 'people' | 'checkup';
};

export type Person = {
  id: string;
  name: string;
  relationship: string;
  image_base64?: string;
};

const REMINDERS_PLACEHOLDER: Reminder[] = [
  { id: '1', icon: '💊', label: 'Aspirin',    time: '08:00', type: 'medication' },
  { id: '2', icon: '🧘', label: 'Stretching', time: '09:00', type: 'exercise'   },
  { id: '3', icon: '💪', label: 'Exercise',   time: '10:30', type: 'exercise'   },
  { id: '4', icon: '🏥', label: 'Checkup',    time: '14:00', type: 'checkup'    },
  { id: '5', icon: '👥', label: 'Call Ana',   time: '16:00', type: 'people'     },
];

const REMINDER_STYLES: Record<Reminder['type'], { bg: string; border: string; text: string }> = {
  medication: { bg: '#F2C9BB', border: '#D4957F', text: '#5C3D35' },
  exercise:   { bg: '#EDD9D0', border: '#C9B8B0', text: '#5C3D35' },
  people:     { bg: '#F2C9BB', border: '#C9948A', text: '#5C3D35' },
  checkup:    { bg: '#EDD9D0', border: '#C9B8B0', text: '#5C3D35' },
};

// ── Helpers ───────────────────────────────────────────────────────────────────
function getGreeting(): string {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 17) return 'Good afternoon';
  return 'Good evening';
}

function getDateStr(): string {
  return new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
}

function toImgUri(raw: string): string {
  return raw.startsWith('data:') ? raw : `data:image/jpeg;base64,${raw}`;
}

// ── BlushPulseRing ─────────────────────────────────────────────────────────────
function BlushPulseRing({ animate, delay = 0, size }: { animate: boolean; delay?: number; size: number }) {
  const scale   = useRef(new Animated.Value(1)).current;
  const opacity = useRef(new Animated.Value(0)).current;
  const loopRef = useRef<Animated.CompositeAnimation | null>(null);

  useEffect(() => {
    if (animate) {
      const t = setTimeout(() => {
        scale.setValue(1);
        opacity.setValue(0.5);
        loopRef.current = Animated.loop(
          Animated.parallel([
            Animated.timing(scale,   { toValue: 1.9, duration: 1600, useNativeDriver: true, easing: Easing.out(Easing.ease) }),
            Animated.timing(opacity, { toValue: 0,   duration: 1600, useNativeDriver: true }),
          ])
        );
        loopRef.current.start();
      }, delay);
      return () => clearTimeout(t);
    } else {
      loopRef.current?.stop();
      loopRef.current = null;
      Animated.parallel([
        Animated.timing(scale,   { toValue: 1, duration: 300, useNativeDriver: true }),
        Animated.timing(opacity, { toValue: 0, duration: 300, useNativeDriver: true }),
      ]).start();
    }
  }, [animate]);

  return (
    <Animated.View
      pointerEvents="none"
      style={{
        position: 'absolute', width: size, height: size, borderRadius: size / 2,
        borderWidth: 1.5, borderColor: C.blush, transform: [{ scale }], opacity,
      }}
    />
  );
}

// ── ThinkingRing ───────────────────────────────────────────────────────────────
function ThinkingRing({ visible, size }: { visible: boolean; size: number }) {
  const rotation = useRef(new Animated.Value(0)).current;
  const opacity  = useRef(new Animated.Value(0)).current;
  const activeRef = useRef(false);

  useEffect(() => {
    if (visible) {
      Animated.timing(opacity, { toValue: 1, duration: 300, useNativeDriver: true }).start();
      activeRef.current = true;
      const spin = () => {
        if (!activeRef.current) return;
        rotation.setValue(0);
        Animated.timing(rotation, { toValue: 1, duration: 3000, easing: Easing.linear, useNativeDriver: true })
          .start(({ finished }) => { if (finished) spin(); });
      };
      spin();
    } else {
      activeRef.current = false;
      rotation.stopAnimation();
      Animated.timing(opacity, { toValue: 0, duration: 200, useNativeDriver: true }).start();
    }
  }, [visible]);

  const rotate = rotation.interpolate({ inputRange: [0, 1], outputRange: ['0deg', '360deg'] });
  const r = size / 2 - 3;

  return (
    <Animated.View pointerEvents="none" style={{ position: 'absolute', width: size, height: size, transform: [{ rotate }], opacity }}>
      <Svg width={size} height={size}>
        <Circle cx={size / 2} cy={size / 2} r={r} stroke={C.warm} strokeWidth={2} strokeDasharray="10 7" fill="none" />
      </Svg>
    </Animated.View>
  );
}

// ── MicIcon ───────────────────────────────────────────────────────────────────
function MicIcon({ size = 44, color = '#FFFFFF' }: { size?: number; color?: string }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24">
      <Path d="M12 1a4 4 0 0 1 4 4v6a4 4 0 0 1-8 0V5a4 4 0 0 1 4-4z" fill={color} />
      <Path d="M19 10v1a7 7 0 0 1-14 0v-1M12 18v4M8 22h8" stroke={color} strokeWidth={1.8} strokeLinecap="round" fill="none" />
    </Svg>
  );
}

// ── CameraIcon ────────────────────────────────────────────────────────────────
function CameraIcon({ size = 24, color = '#FFFFFF' }: { size?: number; color?: string }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24">
      <Path d="M15 10.5V7a1 1 0 0 0-1-1H4a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1v-3.5l4 4v-11l-4 4z" fill={color} />
    </Svg>
  );
}

// ── PersonAvatar ──────────────────────────────────────────────────────────────
function PersonAvatar({
  person,
  onPress,
  onLongPress,
}: {
  person: Person;
  onPress: (p: Person) => void;
  onLongPress: (p: Person) => void;
}) {
  const initials = person.name.split(' ').map((w) => w[0]).join('').slice(0, 2).toUpperCase();
  return (
    <TouchableOpacity
      style={ps.avatarWrap}
      onPress={() => onPress(person)}
      onLongPress={() => onLongPress(person)}
      delayLongPress={600}
      activeOpacity={0.75}
    >
      <View style={ps.avatarCircle}>
        {person.image_base64 ? (
          <Image source={{ uri: toImgUri(person.image_base64) }} style={ps.avatarImg} />
        ) : (
          <Text style={ps.avatarInitials}>{initials}</Text>
        )}
      </View>
      <Text style={ps.avatarName} numberOfLines={1}>{person.name.split(' ')[0]}</Text>
    </TouchableOpacity>
  );
}

// ── TypingDots ────────────────────────────────────────────────────────────────
function TypingDots() {
  const dots = [
    useRef(new Animated.Value(0)).current,
    useRef(new Animated.Value(0)).current,
    useRef(new Animated.Value(0)).current,
  ];

  useEffect(() => {
    const anims = dots.map((dot, i) =>
      Animated.loop(
        Animated.sequence([
          Animated.delay(i * 200),
          Animated.timing(dot, { toValue: 1, duration: 300, useNativeDriver: true }),
          Animated.timing(dot, { toValue: 0, duration: 300, useNativeDriver: true }),
          Animated.delay((dots.length - i) * 200),
        ])
      )
    );
    anims.forEach((a) => a.start());
    return () => anims.forEach((a) => a.stop());
  }, []);

  return (
    <View style={{ flexDirection: 'row', marginTop: 14, gap: 6 }}>
      {dots.map((dot, i) => (
        <Animated.View
          key={i}
          style={{
            width: 7, height: 7, borderRadius: 4,
            backgroundColor: C.warm,
            opacity: dot,
            transform: [{ translateY: dot.interpolate({ inputRange: [0, 1], outputRange: [0, -4] }) }],
          }}
        />
      ))}
    </View>
  );
}

// ── PersonModal ───────────────────────────────────────────────────────────────
function PersonModal({ person, onClose }: { person: Person | null; onClose: () => void }) {
  const [description, setDescription] = useState<string | null>(null);
  const [loading,     setLoading]     = useState(false);

  useEffect(() => {
    if (!person) { setDescription(null); return; }
    setLoading(true);
    setDescription(null);
    fetch(`${BACKEND_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: USER_ID,
        message: `In 2-3 warm, personal sentences remind me who ${person.name} is — they are my ${person.relationship}. Be specific, affectionate, and encouraging. No greetings, just the description.`,
      }),
    })
      .then((r) => r.json())
      .then((d) => setDescription(d.response ?? d.fallback_response ?? null))
      .catch(() => setDescription(null))
      .finally(() => setLoading(false));
  }, [person?.id]);

  if (!person) return null;
  const initials = person.name.split(' ').map((w) => w[0]).join('').slice(0, 2).toUpperCase();
  const imgUri = person.image_base64 ? toImgUri(person.image_base64) : null;

  return (
    <Modal visible transparent animationType="fade" onRequestClose={onClose}>
      <View style={pm.backdrop}>
        <TouchableOpacity style={pm.card} activeOpacity={1} onPress={() => {}}>
          <TouchableOpacity style={pm.closeRow} onPress={onClose} activeOpacity={0.7}>
            <Text style={pm.closeX}>✕</Text>
          </TouchableOpacity>
          <View style={pm.photoWrap}>
            {imgUri ? (
              <Image source={{ uri: imgUri }} style={pm.photo} />
            ) : (
              <View style={pm.photoPlaceholder}>
                <Text style={pm.photoInitials}>{initials}</Text>
              </View>
            )}
          </View>
          <Text style={pm.name}>{person.name}</Text>
          <Text style={pm.relationship}>{person.relationship}</Text>
          {loading ? (
            <TypingDots />
          ) : description ? (
            <Text style={pm.description}>{description}</Text>
          ) : null}
          {!person.image_base64 && (
            <Text style={pm.hint}>Hold avatar to add a photo</Text>
          )}
        </TouchableOpacity>
      </View>
    </Modal>
  );
}

// ── App ───────────────────────────────────────────────────────────────────────
export default function App() {
  const [listening,      setListening]      = useState(false);
  const [thinking,       setThinking]       = useState(false);
  const [setupOpen,      setSetupOpen]      = useState(false);
  const [cameraOpen,     setCameraOpen]     = useState(false);
  const [processing,     setProcessing]     = useState(false);
  const [capturedUri,    setCapturedUri]    = useState<string | null>(null);
  const [people,         setPeople]         = useState<Person[]>([]);
  const [photoTarget,    setPhotoTarget]    = useState<Person | null>(null);
  const [selectedPerson, setSelectedPerson] = useState<Person | null>(null);
  const [reminders,      setReminders]      = useState<Reminder[]>(REMINDERS_PLACEHOLDER);
  const [permission,     requestPermission] = useCameraPermissions();

  type Medication  = { name: string; dose: string; time: string };
  type Contact     = { name: string; relationship: string };
  type Appointment = { doctor: string; date: string };
  const [patientName,  setPatientName]  = useState('');
  const [medications,  setMedications]  = useState<Medication[]>([{ name: '', dose: '', time: '' }]);
  const [contacts,     setContacts]     = useState<Contact[]>([{ name: '', relationship: '' }]);
  const [appointments, setAppointments] = useState<Appointment[]>([{ doctor: '', date: '' }]);

  const recorder    = useAudioRecorder(RecordingPresets.HIGH_QUALITY);
  const cameraRef   = useRef<CameraView>(null);
  const buttonScale = useRef(new Animated.Value(1)).current;
  const breathe     = useRef(new Animated.Value(1)).current;
  const photoScale  = useRef(new Animated.Value(1)).current;
  const photoOpacity = useRef(new Animated.Value(1)).current;

  // ── People ───────────────────────────────────────────────────────────────
  const fetchPeople = useCallback(async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/contacts?user_id=${USER_ID}`);
      const data = await res.json();
      if (data.contacts) setPeople(data.contacts);
    } catch (e) {
      console.warn('[PEOPLE] fetch failed:', e);
    }
  }, []);

  useEffect(() => { fetchPeople(); }, [fetchPeople]);

  // ── Reminders ────────────────────────────────────────────────────────────
  useEffect(() => {
    const fetchReminders = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/reminders?user_id=${USER_ID}`);
        if (res.ok) {
          const data = await res.json();
          if (data.reminders) {
            const mapped = data.reminders.map((r: any) => ({
              ...r,
              type: ['medication', 'exercise', 'people', 'checkup'].includes(r.type) ? r.type : 'medication',
            }));
            setReminders(mapped);
          }
        }
      } catch (err) {
        console.error('Failed to fetch reminders:', err);
      }
    };
    fetchReminders();
    const interval = setInterval(fetchReminders, 10000);
    return () => clearInterval(interval);
  }, []);

  const openCameraForPerson = async (person: Person) => {
    if (!permission?.granted) {
      const result = await requestPermission();
      if (!result.granted) return;
    }
    setPhotoTarget(person);
    setCameraOpen(true);
  };

  // ── Idle breathing ───────────────────────────────────────────────────────
  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(breathe, { toValue: 1.04, duration: 2200, useNativeDriver: true, easing: Easing.inOut(Easing.sine) }),
        Animated.timing(breathe, { toValue: 1.00, duration: 2200, useNativeDriver: true, easing: Easing.inOut(Easing.sine) }),
      ])
    );
    loop.start();
    return () => loop.stop();
  }, []);

  // ── Camera ───────────────────────────────────────────────────────────────
  const openCamera = async () => {
    if (!permission?.granted) {
      const result = await requestPermission();
      if (!result.granted) { Speech.speak('Camera permission is required.'); return; }
    }
    setCameraOpen(true);
  };

  const takePicture = async () => {
    if (!cameraRef.current || processing) return;
    setProcessing(true);
    try {
      const photo = await cameraRef.current.takePictureAsync({ base64: true, quality: 0.5 });
      setCameraOpen(false);

      if (photoTarget) {
        const target = photoTarget;
        setPhotoTarget(null);
        await fetch(`${BACKEND_URL}/contacts/${target.id}/image`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ image_base64: photo?.base64 }),
        });
        await fetchPeople();
      } else {
        photoScale.setValue(1);
        photoOpacity.setValue(0);
        setCapturedUri(photo?.uri ?? null);
        Animated.timing(photoOpacity, { toValue: 1, duration: 300, useNativeDriver: true }).start(() => {
          setTimeout(() => {
            Animated.parallel([
              Animated.timing(photoOpacity, { toValue: 0,      duration: 500, useNativeDriver: true }),
              Animated.spring(photoScale,   { toValue: 1 / 10, useNativeDriver: true, speed: 3, bounciness: 0 }),
            ]).start(() => setCapturedUri(null));
          }, 2500);
        });
        Speech.speak('Let me take a look at that…');
        const res  = await fetch(`${BACKEND_URL}/vision/image`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: USER_ID, image_base64: photo?.base64 }),
        });
        const data = await res.json();
        Speech.speak(data.fallback_response ?? data.response ?? 'Sorry, I could not analyse that.');
      }
    } catch {
      Speech.speak('Sorry, I cannot connect. Please try again.');
    } finally {
      setProcessing(false);
    }
  };

  // ── Mic ──────────────────────────────────────────────────────────────────
  const onPressIn = async () => {
    setListening(true);
    Animated.spring(buttonScale, { toValue: 0.92, useNativeDriver: true, speed: 40, bounciness: 3 }).start();
    try {
      const { granted } = await requestRecordingPermissionsAsync();
      if (!granted) { Speech.speak('Microphone permission is required.'); return; }
      await setAudioModeAsync({ allowsRecording: true, playsInSilentMode: true });
      await recorder.prepareToRecordAsync();
      recorder.record();
    } catch (e) {
      console.error('[MIC] onPressIn error:', e);
      Speech.speak('Could not start recording.');
    }
  };

  const onPressOut = async () => {
    setListening(false);
    Animated.spring(buttonScale, { toValue: 1, useNativeDriver: true, speed: 18, bounciness: 10 }).start();
    try {
      await recorder.stop();
      const uri = recorder.uri;
      if (!uri) return;
      setThinking(true);
      const response = await fetch(uri);
      const blob     = await response.blob();
      const mimeType = blob.type || 'audio/mp4';
      const base64   = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve((reader.result as string).split(',')[1]);
        reader.onerror   = reject;
        reader.readAsDataURL(blob);
      });
      try {
        const res  = await fetch(`${BACKEND_URL}/chat/voice`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: USER_ID, audio_base64: base64, mime_type: mimeType }),
        });
        const data = await res.json();
        await setAudioModeAsync({ allowsRecording: false, playsInSilentMode: true });
        if (data.audio_base64) {
          const { sound } = await Audio.Sound.createAsync(
            { uri: `data:audio/mp3;base64,${data.audio_base64}` },
            { shouldPlay: true, volume: 1.0 }
          );
          sound.setOnPlaybackStatusUpdate((st) => {
            if (st.isLoaded && st.didJustFinish) sound.unloadAsync();
          });
        } else {
          const text = data.fallback_response ?? data.response;
          if (text) Speech.speak(text);
        }
      } catch {
        Speech.speak('Sorry, I cannot connect. Please try again.');
      } finally {
        setThinking(false);
      }
    } catch {
      setThinking(false);
      Speech.speak('Sorry, something went wrong.');
    }
  };

  const OUTER    = 240;
  const INNER    = 180;
  const innerBg  = listening ? C.deep : C.warm;
  const hintText = listening ? 'Listening…' : thinking ? 'Thinking…' : 'Hold to speak';

  return (
    <View style={s.screen}>
      <StatusBar style="dark" />

      {/* Share button */}
      <TouchableOpacity
        style={s.shareBtn}
        onPress={async () => {
          try {
            const link = `https://t.me/${BOT_USERNAME}?start=${USER_ID}`;
            await Share.share({ message: `Please click this link and press START in Telegram to become my Oonook Caretaker: ${link}` });
          } catch { /* cancelled */ }
        }}
        onLongPress={() => setSetupOpen(true)}
        delayLongPress={5000}
      >
        <Text style={s.shareBtnIcon}>🔗</Text>
      </TouchableOpacity>

      {/* Header */}
      <View style={s.header}>
        <Text style={s.dateText}>{getDateStr()}</Text>
        <Text style={s.greetText}>{getGreeting()}, Nikola</Text>
      </View>

      {/* People */}
      {people.length > 0 && (
        <View style={s.peopleSection}>
          <Text style={s.remindersLabel}>PEOPLE</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={s.peopleScroll}>
            {people.map((person) => (
              <PersonAvatar
                key={person.id}
                person={person}
                onPress={setSelectedPerson}
                onLongPress={openCameraForPerson}
              />
            ))}
          </ScrollView>
        </View>
      )}

      {/* Mic hero */}
      <View style={s.hero}>
        <BlushPulseRing animate={listening} delay={0}   size={OUTER} />
        <BlushPulseRing animate={listening} delay={400} size={OUTER} />
        <BlushPulseRing animate={listening} delay={800} size={OUTER} />
        <ThinkingRing visible={thinking} size={OUTER + 20} />

        <View style={[s.outerRing, { width: OUTER, height: OUTER, borderRadius: OUTER / 2 }]}>
          <Animated.View style={{ transform: [{ scale: listening || thinking ? buttonScale : breathe }] }}>
            <TouchableOpacity
              activeOpacity={1}
              onPressIn={onPressIn}
              onPressOut={onPressOut}
              disabled={thinking}
              style={[s.innerCircle, { width: INNER, height: INNER, borderRadius: INNER / 2, backgroundColor: innerBg }]}
            >
              <MicIcon size={46} color="#FFFFFF" />
              <Text style={s.holdText}>{hintText}</Text>
            </TouchableOpacity>
          </Animated.View>
        </View>
      </View>

      {/* Reminders */}
      <View style={s.remindersSection}>
        <Text style={s.remindersLabel}>REMINDERS</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={s.remindersScroll}>
          {reminders.map((r) => {
            const rs = REMINDER_STYLES[r.type];
            return (
              <View key={r.id} style={[s.reminderBadge, { backgroundColor: rs.bg, borderColor: rs.border }]}>
                <Text style={[s.reminderBadgeLabel, { color: rs.text }]}>{r.label}</Text>
                <Text style={[s.reminderBadgeTime,  { color: rs.text }]}>{r.time}</Text>
              </View>
            );
          })}
        </ScrollView>
      </View>

      {/* Camera button */}
      <View style={s.cameraSection}>
        <TouchableOpacity style={s.cameraCircle} onPress={openCamera} activeOpacity={0.75}>
          <CameraIcon size={22} color="#FFFFFF" />
        </TouchableOpacity>
        <Text style={s.cameraTap}>tap · hold</Text>
      </View>

      {/* Person detail modal */}
      <PersonModal person={selectedPerson} onClose={() => setSelectedPerson(null)} />

      {/* Camera modal */}
      <Modal visible={cameraOpen} animationType="slide" onRequestClose={() => { setCameraOpen(false); setPhotoTarget(null); }}>
        <View style={s.cameraScreen}>
          <CameraView ref={cameraRef} style={s.cameraPreview} facing="back" />
          {photoTarget && (
            <View style={s.cameraLabel}>
              <Text style={s.cameraLabelText}>Photo for {photoTarget.name}</Text>
            </View>
          )}
          <View style={s.cameraControls}>
            <TouchableOpacity style={s.closeBtn} onPress={() => { setCameraOpen(false); setPhotoTarget(null); }}>
              <Text style={s.closeBtnText}>✕</Text>
            </TouchableOpacity>
            <TouchableOpacity style={s.captureBtn} onPress={takePicture} disabled={processing}>
              <View style={s.captureInner} />
            </TouchableOpacity>
            <View style={{ width: 56 }} />
          </View>
        </View>
      </Modal>

      {/* Setup modal */}
      <Modal visible={setupOpen} animationType="slide" onRequestClose={() => setSetupOpen(false)}>
        <View style={s.setupScreen}>
          <View style={s.setupHeader}>
            <Text style={s.setupTitle}>Caretaker Setup</Text>
            <TouchableOpacity style={s.setupCloseBtn} onPress={() => setSetupOpen(false)}>
              <Text style={s.setupCloseTxt}>✕</Text>
            </TouchableOpacity>
          </View>
          <ScrollView style={s.setupScroll} showsVerticalScrollIndicator={false}>
            <Text style={s.setupSection}>👤 Patient Name</Text>
            <TextInput style={s.setupInput} placeholder="e.g. Nikola"
              placeholderTextColor={C.textHint} value={patientName} onChangeText={setPatientName} />

            <Text style={s.setupSection}>💊 Medications</Text>
            {medications.map((med, i) => (
              <View key={i} style={s.setupRow}>
                <TextInput style={[s.setupInput, s.flex]} placeholder="Name" placeholderTextColor={C.textHint}
                  value={med.name} onChangeText={v => setMedications(p => p.map((m, j) => j === i ? { ...m, name: v } : m))} />
                <TextInput style={[s.setupInput, s.setupSmall]} placeholder="Dose" placeholderTextColor={C.textHint}
                  value={med.dose} onChangeText={v => setMedications(p => p.map((m, j) => j === i ? { ...m, dose: v } : m))} />
                <TextInput style={[s.setupInput, s.setupSmall]} placeholder="Time" placeholderTextColor={C.textHint}
                  value={med.time} onChangeText={v => setMedications(p => p.map((m, j) => j === i ? { ...m, time: v } : m))} />
                {medications.length > 1 && (
                  <TouchableOpacity onPress={() => setMedications(p => p.filter((_, j) => j !== i))}>
                    <Text style={s.removeBtn}>✕</Text>
                  </TouchableOpacity>
                )}
              </View>
            ))}
            <TouchableOpacity style={s.addBtn} onPress={() => setMedications(p => [...p, { name: '', dose: '', time: '' }])}>
              <Text style={s.addBtnTxt}>+ Add Medication</Text>
            </TouchableOpacity>

            <Text style={s.setupSection}>👥 Family &amp; Friends</Text>
            {contacts.map((c, i) => (
              <View key={i} style={s.setupRow}>
                <TextInput style={[s.setupInput, s.flex]} placeholder="Name" placeholderTextColor={C.textHint}
                  value={c.name} onChangeText={v => setContacts(p => p.map((m, j) => j === i ? { ...m, name: v } : m))} />
                <TextInput style={[s.setupInput, s.flex]} placeholder="Relationship" placeholderTextColor={C.textHint}
                  value={c.relationship} onChangeText={v => setContacts(p => p.map((m, j) => j === i ? { ...m, relationship: v } : m))} />
                {contacts.length > 1 && (
                  <TouchableOpacity onPress={() => setContacts(p => p.filter((_, j) => j !== i))}>
                    <Text style={s.removeBtn}>✕</Text>
                  </TouchableOpacity>
                )}
              </View>
            ))}
            <TouchableOpacity style={s.addBtn} onPress={() => setContacts(p => [...p, { name: '', relationship: '' }])}>
              <Text style={s.addBtnTxt}>+ Add Contact</Text>
            </TouchableOpacity>

            <Text style={s.setupSection}>🏥 Upcoming Appointments</Text>
            {appointments.map((a, i) => (
              <View key={i} style={s.setupRow}>
                <TextInput style={[s.setupInput, s.flex]} placeholder="Doctor / Specialist" placeholderTextColor={C.textHint}
                  value={a.doctor} onChangeText={v => setAppointments(p => p.map((m, j) => j === i ? { ...m, doctor: v } : m))} />
                <TextInput style={[s.setupInput, s.setupSmall]} placeholder="Date" placeholderTextColor={C.textHint}
                  value={a.date} onChangeText={v => setAppointments(p => p.map((m, j) => j === i ? { ...m, date: v } : m))} />
                {appointments.length > 1 && (
                  <TouchableOpacity onPress={() => setAppointments(p => p.filter((_, j) => j !== i))}>
                    <Text style={s.removeBtn}>✕</Text>
                  </TouchableOpacity>
                )}
              </View>
            ))}
            <TouchableOpacity style={s.addBtn} onPress={() => setAppointments(p => [...p, { doctor: '', date: '' }])}>
              <Text style={s.addBtnTxt}>+ Add Appointment</Text>
            </TouchableOpacity>

            <TouchableOpacity style={s.saveBtn} onPress={() => setSetupOpen(false)}>
              <Text style={s.saveBtnTxt}>Save &amp; Close</Text>
            </TouchableOpacity>
            <View style={{ height: 48 }} />
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
      {next && (
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
            {reminders.slice(1).map((r) => (
              <TouchableOpacity key={r.id} style={styles.reminderRow}>
                <Text style={styles.reminderRowIcon}>{r.icon}</Text>
                <Text style={styles.reminderRowLabel}>{r.label}</Text>
                <Text style={styles.reminderRowTime}>{r.time}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        )}
      </View>
      )}

      {/* Photo shrink animation overlay */}
      {capturedUri && (
        <Animated.View
          pointerEvents="none"
          style={[s.photoOverlay, { transform: [{ scale: photoScale }], opacity: photoOpacity }]}
        >
          <View style={s.photoFrame}>
            <Image source={{ uri: capturedUri }} style={s.photoImg} />
          </View>
        </Animated.View>
      )}
    </View>
  );
}
