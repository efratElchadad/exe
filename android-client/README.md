# AndroidCompiler Android client
Native Java Android 8+ client. No Gradle, Java compiler, Python interpreter or Android SDK runs on the phone. All project builds use the user's private GitHub Actions repository.

## Build from repository root
Install JDK 17, Gradle 8.11.1, Android SDK platform 35 and build tools 35.0.0 on the development machine. These are development requirements only, not end-user requirements.

```
python packaging/prepare_assets.py
gradle -p android-client :app:assembleDebug
```
The installable preview APK is `android-client/app/build/outputs/apk/debug/app-debug.apk`.
CI additionally launches an Android API 35 emulator and runs `connectedDebugAndroidTest`. Release APK currently uses the CI debug signature, not a production signing key.

Supported routes: Android source → APK; Python or supported .NET source → Windows EXE or Mac DMG. Choose ZIP (12 MiB maximum), entry/module, output folder, then approve upload and supply a GitHub classic token with repo/workflow. No token is saved to disk. Source is retained in private Git history. Actions quotas/charges apply. The full private-account transaction has not yet been tested with a real user token.
