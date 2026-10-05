"""Runs on GitHub's macOS runner; uses structured config, never shell interpolation."""
import json,os,platform,re,subprocess,sys,zipfile
from pathlib import Path

def run(*args,cwd=None):subprocess.run([str(a) for a in args],cwd=cwd,check=True)

def main():
    base=Path.cwd();config=json.loads((base/'build-config.json').read_text());source=base/'source';source.mkdir(exist_ok=True)
    with zipfile.ZipFile(base/'source.zip') as z:
        for i in z.infolist():
            p=(source/i.filename).resolve()
            if not p.is_relative_to(source.resolve()) or '\\' in i.filename or i.filename.startswith('/'):raise ValueError('Unsafe source path')
        z.extractall(source)
    entry=(source/config['entry']).resolve()
    if not entry.is_relative_to(source.resolve()) or not entry.is_file():raise ValueError('Invalid entry point')
    out=base/'dist';out.mkdir(exist_ok=True)
    if config['engine']=='python':
        run(sys.executable,'-m','venv',base/'venv');python=base/'venv/bin/python'
        run(python,'-m','pip','install','pyinstaller==6.16.0')
        if (source/'requirements.txt').exists():run(python,'-m','pip','install','-r',source/'requirements.txt',cwd=source)
        if any((source/n).exists() for n in ('pyproject.toml','setup.py')):run(python,'-m','pip','install',source,cwd=source)
        args=[python,'-m','PyInstaller','--noconfirm','--clean','--distpath',out,'--workpath',base/'work']
        if entry.suffix!='.spec':args+=['--windowed','--onedir','--name','Application','--specpath',base/'spec']
        run(*args,entry,cwd=source)
        apps=list(out.glob('*.app'))
        if not apps:raise ValueError('No .app produced. For a spec file include a macOS BUNDLE definition.')
        # PyInstaller also emits a companion onedir folder; the .app is self-contained.
        import shutil
        for p in out.iterdir():
            if p not in apps:
                if p.is_dir():shutil.rmtree(p)
                else:p.unlink()
    elif config['engine']=='dotnet':
        rid='osx-arm64' if platform.machine()=='arm64' else 'osx-x64'
        run('dotnet','publish',entry,'-c',config['kind'],'-r',rid,'--self-contained','true','-p:PublishSingleFile=true','-p:UseAppHost=true','-p:PublishAot=false','-p:PublishTrimmed=false','-p:UseSharedCompilation=false','--disable-build-servers','-o',out,cwd=entry.parent)
        if not any(p.is_file() and os.access(p,os.X_OK) and p.suffix=='' for p in out.iterdir()):raise ValueError('No macOS executable produced')
    else:raise ValueError('Unsupported build engine')
    if config.get('smoke'):
        exe=next(out.glob('*.app'))/'Contents/MacOS/Application' if config['engine']=='python' else next(p for p in out.iterdir() if p.is_file() and p.suffix=='' and os.access(p,os.X_OK))
        run(exe,cwd=base)
        if not (base/'smoke-result.txt').exists():raise ValueError('Produced application did not execute successfully')
    (base/'artifacts').mkdir(exist_ok=True)
    # Single-file .NET executables can be sparse; use logical sizes rather than
    # hdiutil's allocated-block estimate, with filesystem overhead/headroom.
    logical=sum(p.lstat().st_size for p in out.rglob('*') if not p.is_symlink())
    size_mb=max(128,(logical*2+1024**2-1)//1024**2+64)
    print(f'Creating DMG: {logical} logical bytes; {size_mb} MiB capacity',flush=True)
    run('hdiutil','create','-volname','Application','-fs','HFS+','-size',str(size_mb)+'m','-srcfolder',out,'-ov','-format','UDZO',base/'artifacts/Application.dmg')
    print('MAC_BUILD_COMPLETED',flush=True)
if __name__=='__main__':main()
