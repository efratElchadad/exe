AndroidCompiler Preview 0.1 — single-file distribution

Run AndroidCompiler.exe. It verifies and extracts its bundled application into
%LOCALAPPDATA%\AndroidCompilerPortable\<package-version>, then opens it.
Subsequent launches reuse that folder. No administrator privileges are requested.
Windows PowerShell and .NET's built-in ZIP extraction are used automatically;
no shell commands, manual extraction, or external installs are needed by users.
No execution-policy override or security-software bypass is used.
The Android build toolchain is still downloaded on first Build with license consent.

The main app is the same Preview previously supplied. Windows execution has not
been tested here. The wrapper was cross-compiled and its PE header and embedded
archive verified. This is not an Authenticode-signed production release.

To rebuild this wrapper, install Zig's Python package version 0.13.0 on a build
computer and run: python build.py <path-to-AndroidCompiler-Windows-x64.zip>
The original application source is in AndroidCompiler-Source.zip.
