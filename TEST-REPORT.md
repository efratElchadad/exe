# Preview 0.2 regression update — 2026-10-04

23 automated tests passed locally on Linux, including three new regressions:
Build click asks for consent; a worker failure is shown and logged; import results
arrive on the GUI thread only after QThread has finished. The new UI was rendered
and inspected. All 23 regression tests also passed on Windows, and the generated single-file
EXE started successfully in Qt offscreen mode. Verified run:
https://github.com/efratElchadad/exe/actions/runs/37206504804
This does not establish full interactive or Android Build acceptance on Windows.

## Historical 0.1 engine verification

# Test report — 2026-10-04

Status: functional Preview; Windows release qualification is **not complete**.

## Executed successfully in the Linux development environment

| Test | Evidence / result |
|---|---|
| Automated tests | 20 passed; test-evidence/unit-tests.txt |
| Application startup | Actual PySide6 window initialized and rendered with Qt offscreen |
| Drag & Drop folder | Actual Qt drag-enter and drop events delivered; imported project and review displayed |
| Drag & Drop ZIP | Actual Qt drop event delivered; ZIP extracted and module detected |
| Folder import | Copied to independent workspace; source not modified |
| Wrapped project ZIP | Nested project root discovered correctly |
| Project/module detection | settings.gradle.kts, :app, catalog alias, SDK 35/min 24, Gradle 8.9 |
| Confirmation gate | Start disabled until trust checkbox checked; import does not run Gradle |
| ZIP safety | Rejected traversal, absolute paths, drive/ADS, reserved names, links and size overflow |
| Real subprocess logs | stdout streamed; actual Gradle task events displayed and log file written |
| Cancellation | A running real child process terminated within 4 seconds |
| Actual Android Debug build | AGP 8.7.3, Gradle 8.9, Java 17, Android SDK 35; APK 6,665 bytes |
| APK verification | AndroidManifest.xml present, ZIP integrity checked, apksigner verification succeeded |
| Real release signing | keytool generated test key; zipalign and apksigner signed/verified Release, 12,871 bytes |
| Repeat Debug build | Reused downloaded toolchain and Gradle cache; succeeded |
| Real compilation failure | Deliberately invalid Java caused nonzero Gradle failure; surfaced as failure |
| Full UI → engine → result | Ran the real BuildManager through the Qt worker and reached the result screen |
| Error screen / retry navigation | Error diagnostics, persistent logs and return-to-review exercised |
| English switch | Layout switched to LTR; localized interface rebuilt |
| Output buttons | Verified dispatch of exact local APK/folder URLs; OS launch not tested |
| Windows binary format | Cross-compiled launcher is PE32+ Windows GUI x86-64 |

Actual Android integration outputs are recorded in
`test-evidence/integration-results.json`. No Android build process or APK output
was mocked in the integration checks. Unit subprocess fixtures are identified
as such in tests/test_runtime.py.

## What has NOT been verified

- Running the Windows EXE and bundled Python/Qt on real Windows.
- Physical mouse Drag & Drop from Windows Explorer; automated Qt events were used.
- Explorer opening the Output folder and a Windows application opening an APK.
- Windows process-tree cancellation, Windows native certificate store behavior,
  Windows SDK downloads/tool invocation and Windows filesystem edge cases.
- The alternative PyInstaller build script and GitHub Actions workflow.
- Every Android project, AGP version, custom plugin, native dependency or flavor.
- APK installation/launch on a physical Android device or emulator.
- SmartScreen reputation, antivirus compatibility, Authenticode signing or installer.

## Remaining Windows acceptance test

On a Windows 10/11 x64 test computer without Android Studio/Python/Java:
extract the entire portable ZIP, run AndroidCompiler.exe, import the sample both
as a folder and ZIP, build Debug, verify logs/output, create a Release keystore,
build/sign Release, cancel an active build, trigger a Java compilation error,
retry after correcting the source, open Output in Explorer and restart the app.
Do not label the package production-ready until this checklist passes.

The source package includes screenshots of actual Qt screens. These are Linux
Qt offscreen renders, **not screenshots of a verified Windows installation**.
