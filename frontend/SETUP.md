# Oonook Frontend — Setup Guide

## Requirements
- Node.js 18+
- Android phone with **Expo Go** app installed (from Play Store)
- The backend running (see `backend/SETUP.md`)

## 1. Install dependencies

```bash
cd frontend
npm install --legacy-peer-deps
```

## 2. Find your PC's IP address

Your phone and PC must be on the same network. The easiest way is to use your **phone's mobile hotspot**:

1. On your phone: turn on **Mobile Hotspot**
2. On your PC: connect to that hotspot WiFi
3. Open PowerShell and run:
   ```powershell
   ipconfig
   ```
4. Find the IPv4 address for the adapter connected to the phone's hotspot (typically under "Wireless LAN adapter Wi-Fi" — looks like `10.x.x.x` or `192.168.x.x`)

> Note: `172.x.x.x` entries are Windows' own hotspot adapter — skip those.

## 3. Create .env file

Create a file called `.env` in the `frontend/` folder:

```
EXPO_PUBLIC_BACKEND_URL=http://<YOUR_PC_IP>:8080
```

Replace `<YOUR_PC_IP>` with the IP you found in step 2. Example:
```
EXPO_PUBLIC_BACKEND_URL=http://10.192.124.197:8080
```

## 4. Allow port 8080 through Windows Firewall

Run this in PowerShell **as Administrator**:

```powershell
netsh advfirewall firewall add rule name="Spring Boot 8080" dir=in action=allow protocol=TCP localport=8080
```

## 5. Start Expo

```bash
npx expo start
```

Scan the QR code with the **Expo Go** app on your phone.

## Notes
- If you switch networks, your PC's IP changes — update `.env` and restart Expo
- The backend must be running before the app can send/receive data
- The default user ID is `demo_user` (hardcoded in `App.tsx`)
