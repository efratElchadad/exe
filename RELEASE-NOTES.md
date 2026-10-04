# AndroidCompiler 0.5.0 Preview

- Optional macOS cloud builds for Python and cross-platform SDK-style .NET projects.
- Select Apple Silicon or Intel; download the resulting DMG into your chosen output directory.
- Explicit upload confirmation; private user-owned GitHub repository required, public repositories rejected.
- A classic GitHub token with repo/workflow permissions is entered per job, never saved to preferences or passed to runners.
- Source remains in private Git history. Actions quotas/charges apply. 25 MiB compressed-source limit.
- Real remote step status and Actions log link; no line-by-line remote log streaming.
- No Apple Developer ID signing or notarization. Windows-specific frameworks are not portable. .NET output is a macOS executable, not an automatically generated app GUI.
- APK and EXE continue to build locally.
