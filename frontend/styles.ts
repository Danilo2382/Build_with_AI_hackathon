import { Dimensions, StyleSheet } from 'react-native';

const { width: SCREEN_W, height: SCREEN_H } = Dimensions.get('window');

export const PHOTO_W = SCREEN_W * 0.55;
export const PHOTO_H = SCREEN_H * 0.35;

export const C = {
  bg:          '#F7EDE8',
  card:        '#EDD9D0',
  white:       '#FDFAF9',
  blush:       '#F2C9BB',
  warm:        '#D4957F',
  deep:        '#B07060',
  borderDef:   '#C9B8B0',
  borderStr:   '#C9948A',
  textPrimary: '#3A2420',
  textSec:     '#7A5048',
  textHint:    '#A8806E',
};

export const s = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: C.bg,
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingBottom: 36,
    paddingTop: 60,
  },

  // Header
  header: {
    alignItems: 'center',
    marginBottom: 8,
  },
  dateText: {
    fontSize: 14,
    color: C.textSec,
    fontWeight: '400',
    letterSpacing: 0.3,
    marginBottom: 4,
    textAlign: 'center',
  },
  greetText: {
    fontSize: 28,
    color: C.textPrimary,
    fontWeight: '700',
    letterSpacing: -0.5,
    textAlign: 'center',
  },

  // Share button
  shareBtn: {
    position: 'absolute',
    top: 60,
    right: 20,
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: C.card,
    borderWidth: 1,
    borderColor: C.borderDef,
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 10,
  },
  shareBtnIcon: {
    fontSize: 16,
  },

  // Hero
  hero: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  outerRing: {
    backgroundColor: C.blush,
    borderWidth: 1.5,
    borderColor: C.borderStr,
    alignItems: 'center',
    justifyContent: 'center',
  },
  innerCircle: {
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: C.deep,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 16,
    elevation: 8,
    gap: 8,
  },
  holdText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '500',
    letterSpacing: 0.3,
    opacity: 0.9,
  },

  // People
  peopleSection: {
    width: '100%',
    marginBottom: 16,
    alignItems: 'center',
  },
  peopleScroll: {
    paddingHorizontal: 4,
  },

  // Reminders
  remindersSection: {
    width: '100%',
    marginBottom: 24,
    alignItems: 'center',
  },
  remindersLabel: {
    fontSize: 11,
    color: C.textHint,
    fontWeight: '600',
    letterSpacing: 2.5,
    textTransform: 'uppercase',
    marginBottom: 12,
    textAlign: 'center',
  },
  remindersScroll: {
    gap: 10,
    paddingRight: 4,
  },
  reminderBadge: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 12,
    borderWidth: 1,
    minWidth: 80,
    alignItems: 'center',
  },
  reminderBadgeLabel: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 2,
  },
  reminderBadgeTime: {
    fontSize: 12,
    fontWeight: '400',
    opacity: 0.8,
  },

  // Camera button
  cameraSection: {
    alignItems: 'center',
    marginBottom: 4,
  },
  cameraCircle: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: C.warm,
    borderWidth: 1,
    borderColor: C.borderStr,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: C.deep,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 4,
  },
  cameraTap: {
    marginTop: 6,
    fontSize: 11,
    color: C.textHint,
    letterSpacing: 1,
  },

  // Camera modal
  cameraScreen: {
    flex: 1,
    backgroundColor: '#000000',
  },
  cameraPreview: {
    flex: 1,
  },
  cameraLabel: {
    position: 'absolute',
    top: 56,
    alignSelf: 'center',
    backgroundColor: 'rgba(0,0,0,0.5)',
    paddingHorizontal: 20,
    paddingVertical: 8,
    borderRadius: 20,
  },
  cameraLabelText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '600',
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
  closeBtn: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: 'rgba(255,255,255,0.15)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  closeBtnText: {
    fontSize: 22,
    color: '#FFFFFF',
  },
  captureBtn: {
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

  // Photo overlay
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
    borderColor: C.borderStr,
    padding: 4,
    backgroundColor: C.card,
    shadowColor: C.deep,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 20,
    elevation: 12,
  },
  photoImg: {
    width: '100%',
    height: '100%',
    borderRadius: 16,
  },

  // Setup modal
  setupScreen: {
    flex: 1,
    backgroundColor: C.bg,
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
    fontSize: 24,
    fontWeight: '700',
    color: C.textPrimary,
  },
  setupCloseBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: C.card,
    borderWidth: 1,
    borderColor: C.borderDef,
    alignItems: 'center',
    justifyContent: 'center',
  },
  setupCloseTxt: {
    fontSize: 16,
    color: C.textSec,
  },
  setupScroll: {
    flex: 1,
    paddingHorizontal: 20,
  },
  setupSection: {
    fontSize: 14,
    fontWeight: '700',
    color: C.warm,
    letterSpacing: 1,
    textTransform: 'uppercase',
    marginTop: 24,
    marginBottom: 8,
  },
  setupInput: {
    backgroundColor: C.card,
    borderWidth: 1,
    borderColor: C.borderDef,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    color: C.textPrimary,
    fontSize: 15,
    marginBottom: 8,
  },
  setupRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  flex: {
    flex: 1,
    marginRight: 8,
    marginBottom: 0,
  },
  setupSmall: {
    width: 88,
    marginRight: 8,
    marginBottom: 0,
  },
  removeBtn: {
    fontSize: 16,
    color: C.textHint,
    paddingHorizontal: 4,
  },
  addBtn: {
    paddingVertical: 10,
    marginBottom: 4,
  },
  addBtnTxt: {
    fontSize: 14,
    color: C.warm,
    fontWeight: '600',
  },
  saveBtn: {
    marginTop: 32,
    backgroundColor: C.warm,
    borderRadius: 16,
    paddingVertical: 18,
    alignItems: 'center',
  },
  saveBtnTxt: {
    fontSize: 17,
    fontWeight: '700',
    color: '#FFFFFF',
    letterSpacing: 0.3,
  },
});

// Person avatar styles
export const ps = StyleSheet.create({
  avatarWrap: {
    alignItems: 'center',
    marginHorizontal: 8,
    width: 64,
  },
  avatarCircle: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: C.card,
    borderWidth: 1.5,
    borderColor: C.borderStr,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
  avatarImg: {
    width: '100%',
    height: '100%',
  },
  avatarInitials: {
    fontSize: 18,
    fontWeight: '700',
    color: C.deep,
  },
  avatarName: {
    marginTop: 5,
    fontSize: 11,
    color: C.textSec,
    fontWeight: '500',
    textAlign: 'center',
  },
});

// Person modal styles
export const pm = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(58,36,32,0.45)',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
  },
  card: {
    backgroundColor: C.white,
    borderRadius: 24,
    padding: 28,
    alignItems: 'center',
    width: SCREEN_W * 0.72,
    shadowColor: C.deep,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.25,
    shadowRadius: 24,
    elevation: 16,
  },
  closeRow: {
    alignSelf: 'flex-end',
    marginBottom: 4,
    padding: 4,
  },
  closeX: {
    fontSize: 16,
    color: C.textHint,
  },
  photoWrap: {
    width: 160,
    height: 160,
    borderRadius: 80,
    overflow: 'hidden',
    marginBottom: 20,
    borderWidth: 2,
    borderColor: C.borderStr,
  },
  photo: {
    width: '100%',
    height: '100%',
  },
  photoPlaceholder: {
    width: '100%',
    height: '100%',
    backgroundColor: C.card,
    alignItems: 'center',
    justifyContent: 'center',
  },
  photoInitials: {
    fontSize: 52,
    fontWeight: '700',
    color: C.deep,
  },
  name: {
    fontSize: 22,
    fontWeight: '700',
    color: C.textPrimary,
    marginBottom: 6,
  },
  relationship: {
    fontSize: 15,
    color: C.textSec,
    fontWeight: '400',
  },
  description: {
    marginTop: 14,
    fontSize: 14,
    color: C.textSec,
    textAlign: 'center',
    lineHeight: 22,
    fontStyle: 'italic',
  },
  descriptionLoading: {
    marginTop: 14,
    fontSize: 22,
    color: C.textHint,
    letterSpacing: 4,
  },
  hint: {
    marginTop: 14,
    fontSize: 12,
    color: C.textHint,
    fontStyle: 'italic',
  },
});
