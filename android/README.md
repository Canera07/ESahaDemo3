# E-Saha Android App

Native Android wrapper application for E-Saha web platform.

## 📱 App Information

- **App Name:** E-Saha
- **Package:** com.esaha.app
- **Min SDK:** 24 (Android 7.0)
- **Target SDK:** 34 (Android 14)
- **Version:** 1.0

## 🌐 Web URL

The app loads: `https://saharezervtr.preview.emergentagent.com/`

## ✨ Features

- ✅ Full-screen WebView (no browser UI)
- ✅ Splash screen with E-Saha branding (#2E7D32 green)
- ✅ JavaScript enabled
- ✅ Local storage & cookies support
- ✅ Geolocation permission handling
- ✅ Portrait orientation locked
- ✅ Back button navigation support
- ✅ Domain security (blocks external navigation)
- ✅ Custom app icon (green with football goal)

## 🛠️ Build Instructions

### Prerequisites

- Android Studio (Arctic Fox or newer)
- JDK 11 or higher
- Android SDK Platform 34
- Gradle 8.0+

### Option 1: Using Android Studio

1. Open Android Studio
2. Select "Open an Existing Project"
3. Navigate to `/app/android/` directory
4. Wait for Gradle sync to complete
5. Click "Build" → "Build Bundle(s) / APK(s)" → "Build APK(s)"
6. APK will be generated at: `app/build/outputs/apk/debug/app-debug.apk`

### Option 2: Using Command Line

```bash
cd /app/android/

# For Linux/Mac
./gradlew assembleDebug

# For Windows
gradlew.bat assembleDebug

# Output: app/build/outputs/apk/debug/app-debug.apk
```

### Installing APK on Device

**Via USB:**
```bash
adb install app/build/outputs/apk/debug/app-debug.apk
```

**Via File Transfer:**
1. Copy APK to phone
2. Open file manager on phone
3. Tap APK file
4. Allow "Install from Unknown Sources" if prompted
5. Install

## 📂 Project Structure

```
android/
├── app/
│   ├── src/main/
│   │   ├── java/com/esaha/app/
│   │   │   ├── MainActivity.kt       # Main WebView activity
│   │   │   └── SplashActivity.kt     # Splash screen
│   │   ├── res/
│   │   │   ├── layout/               # UI layouts
│   │   │   ├── values/               # Colors, strings, styles
│   │   │   └── mipmap-*/             # App icons
│   │   └── AndroidManifest.xml       # App configuration
│   ├── build.gradle                  # App build config
│   └── proguard-rules.pro            # ProGuard rules
├── build.gradle                      # Project build config
├── settings.gradle                   # Project settings
└── gradle.properties                 # Gradle properties
```

## 🔒 Security Features

- Only allows navigation within E-Saha domains
- Blocks external URL redirects
- HTTPS-only (cleartext traffic disabled)
- No data collection or tracking

## 🎨 Branding

- **Primary Color:** #2E7D32 (E-Saha Green)
- **Dark Color:** #1B5E20
- **Icon:** White football goal on green background

## 📝 Permissions

- `INTERNET` - Required for WebView
- `ACCESS_FINE_LOCATION` - Optional, for nearby field search
- `ACCESS_COARSE_LOCATION` - Optional, fallback location

## 🐛 Troubleshooting

**Gradle sync fails:**
- Ensure you have JDK 11+
- Run: `./gradlew --refresh-dependencies`

**APK install fails:**
- Enable "Unknown Sources" in device settings
- Check minimum Android version (7.0+)

**WebView shows blank page:**
- Check internet connection
- Verify URL is accessible
- Check Android System WebView is updated

**Location permission not working:**
- Manually grant location in Settings → Apps → E-Saha → Permissions

## 📱 Testing

1. Install APK on physical device or emulator
2. Launch "E-Saha" app
3. Splash screen appears for 2 seconds
4. Main E-Saha website loads
5. Test navigation, login, and booking features
6. Test back button (should navigate within app)

## 🚀 Production Build

For release build with signing:

```bash
# Generate keystore (first time only)
keytool -genkey -v -keystore esaha-release-key.jks -keyalg RSA -keysize 2048 -validity 10000 -alias esaha

# Build release APK
./gradlew assembleRelease

# Output: app/build/outputs/apk/release/app-release.apk
```

## 📞 Support

For issues or questions, contact the E-Saha development team.

---

**Built with ❤️ for E-Saha Platform**
