$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path '.venv\Scripts\python.exe')) { py -3.12 -m venv .venv }
$python = (Resolve-Path '.venv\Scripts\python.exe').Path
& $python -m pip install -r requirements-dev.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
$env:QT_QPA_PLATFORM = 'offscreen'
& $python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw 'Tests failed' }
Remove-Item Env:QT_QPA_PLATFORM
& $python -m PyInstaller --noconfirm --clean --windowed --onedir --name AndroidCompiler --add-data "androidcompiler/mac_worker.py;androidcompiler" --icon androidcompiler/assets/app.ico --add-data "androidcompiler/assets;androidcompiler/assets" --collect-data PySide6 main.py
if ($LASTEXITCODE -ne 0) { throw 'EXE packaging failed' }
Copy-Item README-HE.md,THIRD-PARTY.md,TEST-REPORT.md,LICENSE dist\AndroidCompiler
Copy-Item -Recurse LICENSES,sample dist\AndroidCompiler
Compress-Archive -Path dist\AndroidCompiler -DestinationPath dist\AndroidCompiler-Windows-x64.zip -Force
Write-Host 'Ready: dist\AndroidCompiler\AndroidCompiler.exe'
