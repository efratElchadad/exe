# AndroidCompiler 0.4.0 Preview

- Build Android APK, Python EXE or SDK-style C#/.NET EXE from source folders and ZIPs.
- Choose an output directory before building; each build gets a unique subfolder.
- EXE tools download on demand into private managed directories with SHA512 verification; no global PATH configuration.
- Python 3.12, requirements/project install, entry-point or PyInstaller spec selection, optional hidden console.
- Self-contained Windows x64 .NET 8/9/10 publishing, respecting global.json SDK versions.
- Existing Android signing, live logs, guide, and community credit remain available.

Limitations: Windows x64 EXE builds only. No APK/EXE conversion. Tkinter is not included in managed Python. Native Python extensions without compatible wheels may need compilers; data/dynamic imports may need a spec. Legacy .NET Framework, MAUI and special workloads are not supported automatically. Keep any companion output files. EXEs are not publisher-signed. Online downloads remain enabled; caches are reused.

Windows CI builds and executes real Python/.NET sample EXEs, checks invalid-source failure cleanup and launches the packaged app before publishing.
