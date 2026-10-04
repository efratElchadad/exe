# Components and source availability

The application code and launcher are MIT licensed. Third-party runtimes retain
all their own licenses. No Android SDK, JDK or Gradle binaries are redistributed
inside the portable ZIP: they are downloaded from their suppliers on demand.

The portable package includes unmodified CPython 3.12.10, PySide6 Essentials and
Shiboken6 6.8.3 binaries (the Qt Core/Gui/Widgets subset), their runtime support
DLLs and Python metadata. Qt DLLs remain dynamically linked and replaceable.
You may modify/relink these libraries and reverse engineer the application to
debug those modifications, consistent with the applicable licenses.

- CPython: Python Software Foundation license, included as runtime/LICENSE.txt.
  Exact source: https://www.python.org/ftp/python/3.12.10/Python-3.12.10.tgz
- Qt for Python: LGPLv3/GPL/commercial alternatives; this distribution uses the
  open-source LGPLv3 terms for the relevant libraries.
  Exact source: https://github.com/pyside/pyside-setup/archive/refs/tags/v6.8.3.tar.gz
  Repository: https://code.qt.io/cgit/pyside/pyside-setup.git/tag/?h=v6.8.3
- QtBase 6.8.3 (Core/Gui/Widgets): LGPLv3 with third-party permissive components.
  Exact source: https://download.qt.io/official_releases/qt/6.8/6.8.3/submodules/qtbase-everywhere-src-6.8.3.tar.xz
  License overview: https://doc.qt.io/qt-6.8/licenses-used-in-qt.html
- Qt source license texts are in LICENSES/. The included wheel metadata retains
  upstream license references; commercial license text in metadata is not a
  claim that this application has a commercial Qt license.
- Microsoft runtime support DLLs are included as supplied in the official Qt
  for Python Windows wheel; their supplier's redistribution terms apply.
- Downloaded Eclipse Temurin: https://adoptium.net/about/ (GPLv2 + Classpath Exception).
- Downloaded Gradle: https://github.com/gradle/gradle/blob/master/LICENSE (Apache 2.0).
- Android SDK terms are fetched and displayed in the app before license acceptance.
  https://developer.android.com/studio/terms

Builds contact supplier repositories. Private repositories still require their
own authorized credentials. No certificates are bypassed and no telemetry is
added by AndroidCompiler. A project's own Gradle scripts/plugins may perform
network operations of their own.
