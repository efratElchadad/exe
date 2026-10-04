"""Managed Windows builds. No installed Python, .NET or global PATH changes."""
from __future__ import annotations
import base64,json,os,re,shutil,uuid,xml.etree.ElementTree as ET
from dataclasses import dataclass,field
from pathlib import Path
from .project import Module,ProjectError,IGNORED,read
from .toolchain import Toolchain

@dataclass
class DesktopProject:
    name:str
    root:Path
    workspace:Path
    modules:list
    engine:str
    java:str='—'
    gradle:str='—'
    warnings:list=field(default_factory=list)

def analyze_desktop(source,workspace,engine):
    root=source
    while True:
        children=[p for p in root.iterdir() if p.name not in IGNORED]
        if len(children)==1 and children[0].is_dir():root=children[0]
        else:break
    entries=[]
    for folder,dirs,files in os.walk(root):
        dirs[:]=[d for d in dirs if d not in IGNORED]
        if len(Path(folder).relative_to(root).parts)>5:dirs[:]=[];continue
        entries.extend(Path(folder)/f for f in files if f.endswith(('.py','.spec') if engine=='python' else ('.csproj',)))
        if len(entries)>500:raise ProjectError('Too many entry points; select a more specific project folder')
    if not entries:raise ProjectError('No Python .py/.spec or .NET .csproj project found for the selected target')
    if engine=='python':
        entries.sort(key=lambda p:(p.suffix!='.spec',p.name not in ('main.py','app.py','__main__.py'),len(p.parts),str(p)))
    else:entries.sort()
    modules=[]
    for entry in entries:
        tfm='Python 3.12' if engine=='python' else 'Resolved by MSBuild'
        if engine=='dotnet':
            try:
                xml=ET.fromstring(read(entry))
                props={e.tag.split('}')[-1]:e.text for e in xml.iter() if e.text}
                if props.get('OutputType')=='Library':continue
                tfm=props.get('TargetFramework') or props.get('TargetFrameworks') or tfm
            except ET.ParseError:raise ProjectError(f'Invalid project XML: {entry.name}')
        modules.append(Module(str(entry.relative_to(root)),entry,None,tfm,None,'PyInstaller' if engine=='python' else '.NET SDK',None))
    if not modules:raise ProjectError('No executable application project found; class libraries do not produce EXE files')
    return DesktopProject(root.name,root,workspace,modules,engine,warnings=['Windows x64 EXE · Python 3.12 / SDK-style .NET 8–10. Build scripts and dependency installers execute with your permissions.'])

class DesktopBuilder:
    def __init__(self,base,runner):
        self.base=Path(base);self.runner=runner;self.tools=Toolchain(self.base/'tools',runner,lambda _:False)
        self.env={k:v for k,v in os.environ.items() if k.upper() not in {'PYTHONHOME','PYTHONPATH','VIRTUAL_ENV','DOTNET_ROOT','DOTNET_ROOT_X64','MSBUILD_EXE_PATH','PYTHONSTARTUP'}}
        self.env.update(PYTHONUTF8='1',PYTHONNOUSERSITE='1',PIP_DISABLE_PIP_VERSION_CHECK='1',PIP_CACHE_DIR=str(self.base/'tools/pip-cache'),NUGET_PACKAGES=str(self.base/'tools/nuget-cache'),DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_CLI_HOME=str(self.base/'tools/dotnet-home'),DOTNET_MULTILEVEL_LOOKUP='0',MSBUILDDISABLENODEREUSE='1')
    def python(self):
        target=self.tools.base/'python-3.12.10'
        checksum=base64.b64decode('u9pNz2iKlCEbYtUJaKkbOPMF0LjR7NkCafdKhvigpPzrt8oWKgdTpHaR6z3wyWQAm9PYGUxv0Zr66NX9AeHMDw==').hex()
        self.tools.archive_install('https://api.nuget.org/v3-flatcontainer/python/3.12.10/python.3.12.10.nupkg',checksum,target,'sha512')
        python=target/'tools/python.exe'
        if not python.is_file():raise ValueError('Managed Python package is incomplete')
        return python
    def dotnet(self,project,module):
        match=re.search(r'net(8|9|10)\.0(?:-windows[\d.]*)?$',module.compile_sdk)
        if not match:raise ProjectError('Supported EXE targets: a single net8.0, net9.0 or net10.0 (optionally -windows). Legacy .NET Framework, MAUI, multi-target and NativeAOT projects are not supported automatically.')
        channel=match[1]+'.0';pinned=None
        # Respect the nearest global.json instead of silently compiling with another SDK.
        for parent in [module.directory.parent,*module.directory.parent.parents]:
            if not parent.is_relative_to(project.root):break
            if (parent/'global.json').exists():
                pinned=json.loads(read(parent/'global.json')).get('sdk',{}).get('version');break
        if pinned:
            if not re.fullmatch(r'(8|9|10)\.0\.\d+',pinned):raise ProjectError('Unsupported global.json SDK version')
            channel=pinned.split('.')[0]+'.0'
        marker=self.tools.base/f'dotnet-channel-{channel}.json'
        if pinned:version=pinned
        elif marker.exists():version=json.loads(marker.read_text())['version']
        else:version=None
        target=self.tools.base/f'dotnet-{version}' if version else None
        if not target or not (target/'.complete').exists():
            data=json.loads(self.tools.data(f'https://builds.dotnet.microsoft.com/dotnet/release-metadata/{channel}/releases.json'))
            version=version or data['latest-sdk'];target=self.tools.base/f'dotnet-{version}'
            sdks=[sdk for r in data['releases'] for sdk in r.get('sdks',[r.get('sdk',{})])]
            sdk=next((s for s in sdks if s.get('version')==version),None)
            if not sdk:raise ProjectError(f'SDK {version} is unavailable in official release metadata')
            package=next(f for f in sdk['files'] if f['rid']=='win-x64' and f['url'].endswith('.zip'))
            self.tools.archive_install(package['url'],package['hash'],target,'sha512')
            marker.write_text(json.dumps({'version':version}))
        self.env.update(DOTNET_ROOT=str(target),DOTNET_ROOT_X64=str(target))
        return target/'dotnet.exe'
    def build(self,project,module,kind='Release',output_root=None,windowed=False):
        if os.name!='nt':raise ProjectError('EXE builds require Windows x64')
        if kind not in ('Debug','Release'):raise ProjectError('Invalid configuration')
        entry=module.directory.resolve()
        if not entry.is_relative_to(project.root.resolve()) or not entry.is_file():raise ProjectError('Entry point is outside the project')
        output_root=Path(output_root or self.base/'Output').resolve()
        if output_root.is_relative_to(project.workspace.resolve()):raise ProjectError('Choose an output folder outside the temporary workspace')
        output_root.mkdir(parents=True,exist_ok=True)
        out=output_root/(re.sub(r'[^\w.-]','_',project.name)+'-'+uuid.uuid4().hex[:10]);out.mkdir()
        try:
            if project.engine=='python':
                self.runner.stage('Preparing managed Python')
                python=self.python();venv=project.workspace/'python-env'
                if venv.exists():shutil.rmtree(venv)
                self.runner.run([python,'-m','venv',venv],project.root,self.env)
                py=venv/'Scripts/python.exe'
                self.runner.stage('Installing Python dependencies')
                self.runner.run([py,'-m','pip','install','pyinstaller==6.16.0'],project.root,self.env)
                requirements=project.root/'requirements.txt'
                if requirements.exists():self.runner.run([py,'-m','pip','install','-r',requirements],project.root,self.env)
                if (project.root/'pyproject.toml').exists() or (project.root/'setup.py').exists():self.runner.run([py,'-m','pip','install',project.root],project.root,self.env)
                self.runner.stage('Packaging Windows EXE')
                args=[py,'-m','PyInstaller','--noconfirm','--clean','--distpath',out,'--workpath',project.workspace/'pyinstaller-work']
                if entry.suffix!='.spec':
                    args+=['--onefile','--specpath',project.workspace/'spec','--name',entry.stem if entry.stem!='__main__' else 'Application']
                    if windowed:args+=['--windowed']
                self.runner.run([*args,entry],project.root,self.env)
            else:
                self.runner.stage('Preparing managed .NET SDK');dotnet=self.dotnet(project,module)
                self.runner.stage('Restoring and publishing Windows EXE')
                self.runner.run([dotnet,'publish',entry,'-c',kind,'-r','win-x64','--self-contained','true','-p:UseAppHost=true','-p:PublishSingleFile=true','-p:IncludeNativeLibrariesForSelfExtract=true','-p:PublishAot=false','-p:PublishTrimmed=false','-p:UseSharedCompilation=false','--disable-build-servers','-o',out],entry.parent,self.env)
            self.runner.check();self.runner.stage('Verifying EXE outputs')
            executables=sorted(out.glob('*.exe'))
            if not executables:raise ProjectError('Build completed without a top-level EXE. Check the selected entry point or publish settings.')
            results=[]
            for exe in executables:
                with exe.open('rb') as f:
                    if f.read(2)!=b'MZ':raise ProjectError('Invalid Windows executable output')
                results.append({'path':str(exe),'name':exe.stem,'applicationId':'—','version':'—','type':'EXE','variant':kind,'signed':False,'bytes':exe.stat().st_size,'engine':project.engine})
            (out/'build-report.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),'utf-8')
            self.runner.stage('Build completed');return results
        except Exception:
            shutil.rmtree(out,ignore_errors=True);raise
