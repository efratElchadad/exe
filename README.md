# AndroidCompiler 0.6 Preview

Native Android online client, Windows desktop compiler and Mac desktop cloud client. Supported source projects build into Android APK, Windows EXE or macOS DMG. No universal source or binary conversion.

[Download directly installable files](https://github.com/efratElchadad/exe/releases/tag/v0.6.0-preview.14) · [Hebrew guide](README-HE.md) · [Forum post](FORUM-POST-HE.md) · [Test report](TEST-REPORT.md)

Cloud builds require internet, GitHub Actions and a classic token with repo/workflow scopes. Source uploads require explicit consent, use a private repository and remain in Git history. Actions quotas and charges apply. The full real-token private-account roundtrip has not yet been verified; see the test report for the precise scope.

## Build from source

For the desktop client, install Python 3.12 and run:

```
python -m pip install -r requirements-dev.txt
python packaging/prepare_assets.py
python main.py
```

Native packaging commands and validation gates are in `.github/workflows/publish.yml`. Mac packaging additionally uses Pillow and `python packaging/package_mac.py` on each native architecture. Android source instructions are in [android-client/README.md](android-client/README.md).

Android supports API 26+, accepts ZIP sources up to 12 MiB and saves outputs up to 1 GiB to a chosen folder. It runs no local build toolchain. The preview APK uses a debug signature. Mac packages are not Apple-notarized.
