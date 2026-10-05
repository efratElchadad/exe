"""Shared hosted runner: APK, Windows EXE and macOS DMG from source."""
import json,os,shutil,subprocess,sys,zipfile
from pathlib import Path
from androidcompiler.project import Workspace,analyze,build_file
from androidcompiler.desktop import analyze_desktop,DesktopBuilder
from androidcompiler.build import BuildManager
from androidcompiler.runtime import Runner

def main():
    base=Path.cwd();cfg=json.loads((base/'build-config.json').read_text())
    target=cfg['target'];engine=cfg['engine']
    if target not in ('apk','windows','mac') or engine not in ('android','python','dotnet'):raise ValueError('Unsupported build target')
    if (target=='apk')!=(engine=='android'):raise ValueError('Project type does not match the target')
    work=Workspace(base/'workspaces');runner=Runner(lambda t:print(t,flush=True),lambda t:print('STAGE: '+t,flush=True))
    artifacts=base/'artifacts';artifacts.mkdir(exist_ok=True)
    try:
        project=work.import_project(base/'source.zip',None if engine=='android' else lambda s,w:analyze_desktop(s,w,engine))
        selected=cfg.get('entry','');modules=project.modules
        matches=[m for m in modules if m.name==selected or str((build_file(m.directory) if engine=='android' else m.directory).relative_to(work.path/'source')).replace('\\','/')==selected]
        if len(matches)!=1:raise ValueError('Choose a valid application module or entry file. Available: '+', '.join(m.name for m in modules))
        module=matches[0];kind=cfg.get('kind','Debug' if target=='apk' else 'Release')
        if target=='apk':
            if not cfg.get('accept_android_licenses'):raise ValueError('Android SDK license approval is required')
            BuildManager(base/'managed',runner,lambda _:True).build(project,module,kind,output_root=artifacts)
        elif target=='windows':DesktopBuilder(base/'managed',runner).build(project,module,kind,artifacts,cfg.get('windowed',False))
        else:
            if engine=='dotnet':
                import re
                if not re.fullmatch(r'net(8|9|10)\.0',module.compile_sdk):raise ValueError('Mac .NET requires a single net8.0, net9.0 or net10.0 target without Windows frameworks')
            job=base/'mac-job';job.mkdir()
            with zipfile.ZipFile(job/'source.zip','w',zipfile.ZIP_DEFLATED) as z:
                for p in project.root.rglob('*'):
                    if p.is_file():z.write(p,p.relative_to(project.root))
            (job/'build-config.json').write_text(json.dumps({'engine':engine,'entry':module.name,'kind':kind}))
            subprocess.run([sys.executable,str(Path(__file__).with_name('mac_worker.py'))],cwd=job,check=True)
            shutil.copy2(job/'artifacts/Application.dmg',artifacts/'Application.dmg')
    finally:work.close()
if __name__=='__main__':main()
