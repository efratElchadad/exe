"""Build, launch and package the real desktop client on each native Mac runner."""
from pathlib import Path
import json,subprocess,sys,platform,shutil
from PIL import Image
root=Path(__file__).resolve().parents[1]
def run(*args):subprocess.run([str(a) for a in args],cwd=root,check=True)
run(sys.executable,'packaging/prepare_assets.py')
icon=root/'androidcompiler/assets/app.icns'
Image.open(root/'androidcompiler/assets/app.png').save(icon,format='ICNS')
run(sys.executable,'-m','PyInstaller','--noconfirm','--clean','--windowed','--onedir','--paths','.','--name','AndroidCompiler','--icon',icon,'--add-data','androidcompiler/assets:androidcompiler/assets','--add-data','androidcompiler/mac_worker.py:androidcompiler','--add-data','LICENSES:LICENSES','--add-data','THIRD-PARTY.md:.','packaging/entry.py')
app=root/'dist/AndroidCompiler.app'
run(app/'Contents/MacOS/AndroidCompiler','--smoke-test')
result=json.loads((root/'smoke-test.json').read_text())
assert result['opened'] and result['frozen'] and result['icon_loaded']
logical=sum(p.lstat().st_size for p in app.rglob('*') if not p.is_symlink())
mb=max(128,(logical*2+1024**2-1)//1024**2+64)
stage=root/'dist/dmg-stage';stage.mkdir(exist_ok=True)
shutil.move(str(app),str(stage/app.name))
(stage/'Applications').symlink_to('/Applications',target_is_directory=True)
arch='arm64' if platform.machine()=='arm64' else 'x64'
run('hdiutil','create','-volname','AndroidCompiler','-fs','HFS+','-size',str(mb)+'m','-srcfolder',stage,'-ov','-format','UDZO',root/f'dist/AndroidCompiler-Mac-{arch}.dmg')

# Verify the delivered image contains a runnable .app at its root.
mount=root/'dmg-check';mount.mkdir(exist_ok=True)
run('hdiutil','attach',root/f'dist/AndroidCompiler-Mac-{arch}.dmg','-nobrowse','-readonly','-mountpoint',mount)
try:
    executable=mount/'AndroidCompiler.app/Contents/MacOS/AndroidCompiler'
    assert executable.is_file(),'DMG must contain the app, not its unpacked contents'
    run(executable,'--smoke-test')
finally:run('hdiutil','detach',mount)
