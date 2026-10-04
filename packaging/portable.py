"""Create Windows x64 portable distribution on Windows OR Linux.
Run: python packaging/portable.py --downloads <dir> --launcher <compiled exe>
Trusted Python/Qt downloads are supplied explicitly. Build instructions in README.
"""
import argparse, hashlib, json, shutil, zipfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--downloads',type=Path,required=True);p.add_argument('--launcher',type=Path,required=True);p.add_argument('--output',type=Path,default=Path('dist/AndroidCompiler'));a=p.parse_args()
root=Path(__file__).resolve().parents[1];out=a.output.resolve()
if out.exists():shutil.rmtree(out)
(out/'runtime/site-packages').mkdir(parents=True);(out/'app').mkdir()
python=a.downloads/'python-3.12.10-embed-amd64.zip'
with zipfile.ZipFile(python) as z:z.extractall(out/'runtime')
manifest=[]
for whl in sorted(a.downloads.glob('*.whl')):
    with zipfile.ZipFile(whl) as z:
        for name in z.namelist():
            # Ship only the Qt Core/Gui/Widgets subset used by the app.
            if name.startswith('PySide6/'):
                rel=name[len('PySide6/'):]
                keep=(rel in {'QtCore.pyd','QtGui.pyd','QtWidgets.pyd','Qt6Core.dll','Qt6Gui.dll','Qt6Widgets.dll','pyside6.abi3.dll','__init__.py','_config.py','_git_pyside_version.py'}
                      or rel.startswith(('support/','typesystems/'))
                      or rel.startswith(('msvcp','vcruntime','concrt'))
                      or rel in {'plugins/platforms/qwindows.dll','plugins/platforms/qoffscreen.dll','plugins/styles/qmodernwindowsstyle.dll','plugins/imageformats/qjpeg.dll','plugins/imageformats/qico.dll','plugins/imageformats/qgif.dll'})
                if not keep:continue
            z.extract(name,out/'runtime/site-packages')
    manifest.append({'file':whl.name,'sha256':hashlib.sha256(whl.read_bytes()).hexdigest()})
manifest.append({'file':python.name,'sha256':hashlib.sha256(python.read_bytes()).hexdigest()})
(out/'runtime/python312._pth').write_text('python312.zip\n.\nsite-packages\n../app\nimport site\n','utf-8')
shutil.copytree(root/'androidcompiler',out/'app/androidcompiler',ignore=shutil.ignore_patterns('__pycache__'))
shutil.copy2(root/'packaging/bootstrap.py',out/'app/bootstrap.py');shutil.copy2(a.launcher,out/'AndroidCompiler.exe')
for name in ['README-HE.md','THIRD-PARTY.md','TEST-REPORT.md','LICENSE']:
    if (root/name).exists():shutil.copy2(root/name,out/name)
shutil.copytree(root/'LICENSES',out/'LICENSES');shutil.copytree(root/'sample',out/'sample')
(out/'runtime-manifest.json').write_text(json.dumps(manifest,indent=2),'utf-8')
shutil.make_archive(str(out.parent/'AndroidCompiler-Windows-x64'),'zip',out.parent,out.name)
print(out.parent/'AndroidCompiler-Windows-x64.zip')
