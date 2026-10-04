from __future__ import annotations
import os, re, shutil, stat, tempfile, zipfile, hashlib
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

IGNORED = {'.git', '.gradle', '.idea', 'build', 'node_modules', '.cxx', '.kotlin', '.venv', 'venv', '__pycache__', 'dist', 'bin', 'obj'}
MAX_BYTES = 8 * 1024**3
MAX_FILES = 100_000

class ProjectError(Exception):
    pass

def safe_parts(name: str):
    name = name.replace('\\', '/')
    parts = PurePosixPath(name).parts
    reserved = {'CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]}
    if not parts or name.startswith('/') or any(p in {'.','..'} or ':' in p or p.endswith((' ', '.')) or p.split('.')[0].upper() in reserved for p in parts):
        raise ProjectError(f'Unsafe archive path: {name}')
    return parts

def extract_zip(source: Path, target: Path, max_bytes=MAX_BYTES):
    """Preflight all entries before writing; reject links, ADS and Windows aliases."""
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source) as z:
        entries = z.infolist()
        if len(entries) > MAX_FILES or sum(i.file_size for i in entries) > max_bytes:
            raise ProjectError('Archive exceeds extraction limits')
        seen = set()
        for i in entries:
            parts = safe_parts(i.filename)
            key = '/'.join(parts).casefold()
            if key in seen: raise ProjectError('Duplicate archive path')
            seen.add(key)
            mode = i.external_attr >> 16
            if stat.S_ISLNK(mode) or (stat.S_IFMT(mode) not in (0,stat.S_IFREG,stat.S_IFDIR)):
                raise ProjectError('Links and special files are not accepted')
            if i.flag_bits & 1: raise ProjectError('Encrypted ZIP is not supported')
        total = 0
        for i in entries:
            out = target.joinpath(*safe_parts(i.filename))
            if i.is_dir(): out.mkdir(parents=True, exist_ok=True); continue
            out.parent.mkdir(parents=True, exist_ok=True)
            with z.open(i) as src, out.open('wb') as dst:
                while chunk := src.read(1024*1024):
                    total += len(chunk)
                    if total > max_bytes: raise ProjectError('Archive exceeds extraction limits')
                    dst.write(chunk)
            # Preserve executable bits in SDK/Gradle archives on Unix.
            if os.name != 'nt' and (i.external_attr >> 16) & 0o111: out.chmod(0o755)

def read(path: Path):
    if not path.is_file(): return ''
    if path.stat().st_size > 2*1024*1024: raise ProjectError(f'Build file too large: {path.name}')
    return path.read_text('utf-8-sig', errors='replace')

def build_file(path: Path):
    return path / ('build.gradle.kts' if (path/'build.gradle.kts').exists() else 'build.gradle')

def literal(text, key):
    m = re.search(r'\b'+re.escape(key)+r'\s*(?:=\s*|\(\s*)?["\']([^"\'\n]+)["\']', text)
    if m: return m.group(1)
    m = re.search(r'\b'+re.escape(key)+r'\s*(?:=\s*|\(\s*)?(\d+)\b', text)
    return m.group(1) if m else None

@dataclass
class Module:
    name: str
    directory: Path
    application_id: str|None
    compile_sdk: str|None
    min_sdk: str|None
    build_tools: str|None
    version: str|None

@dataclass
class Project:
    name: str
    root: Path
    workspace: Path
    modules: list[Module]
    gradle: str
    java: int
    warnings: list[str] = field(default_factory=list)

class Workspace:
    def __init__(self, base: Path):
        self.base = base
        base.mkdir(parents=True, exist_ok=True)
        self.path = Path(tempfile.mkdtemp(prefix='project-', dir=base))
    def close(self): shutil.rmtree(self.path, ignore_errors=True)
    def import_project(self, source: Path, analyzer=None):
        if source.is_symlink(): raise ProjectError('Symbolic links are not supported')
        dest = self.path/'source'
        if source.is_file() and source.suffix.lower()=='.zip':
            extract_zip(source, dest)
        elif source.is_dir():
            if self.base.resolve().is_relative_to(source.resolve()):
                raise ProjectError('Select a project folder, not its workspace parent')
            count = total = 0
            def ignore(folder, names):
                nonlocal count,total
                skipped=[]
                for name in names:
                    p=Path(folder)/name
                    if name in IGNORED: skipped.append(name); continue
                    if p.is_symlink() or (hasattr(p,'is_junction') and p.is_junction()):
                        raise ProjectError(f'Linked path is not supported: {name}')
                    safe_parts(name)
                    if p.is_file():
                        count+=1; total+=p.stat().st_size
                        if count>MAX_FILES or total>MAX_BYTES: raise ProjectError('Project exceeds import limits')
                return skipped
            shutil.copytree(source,dest,ignore=ignore)
        else: raise ProjectError('Choose an Android project folder or ZIP')
        # Never use machine-specific SDK paths from the original computer.
        for folder, dirs, files in os.walk(dest):
            dirs[:]=[d for d in dirs if d not in IGNORED]
            if 'local.properties' in files:
                props=Path(folder)/'local.properties'
                props.write_text('\n'.join(line for line in read(props).splitlines() if not re.match(r'\s*(?:sdk|ndk|cmake)\.dir\s*[=:]',line))+'\n','utf-8')
        return (analyzer or analyze)(dest,self.path)

def analyze(source: Path, workspace: Path|None=None):
    roots=[]
    for folder, dirs, files in os.walk(source):
        dirs[:]=[d for d in dirs if d not in IGNORED]
        rel=Path(folder).relative_to(source)
        if len(rel.parts)>5: dirs[:]=[]; continue
        if {'settings.gradle','settings.gradle.kts'} & set(files): roots.append(Path(folder))
    top=[p for p in roots if not any(p!=q and p.is_relative_to(q) for q in roots)]
    if len(top)!=1: raise ProjectError(f'Expected one Android Gradle project; found {len(top)}')
    root=top[0]
    settings=read(root/'settings.gradle')+read(root/'settings.gradle.kts')
    # Settings may use executable logic. Only literal include declarations are static evidence.
    declared=set()
    for match in re.finditer(r'(?m)^\s*include\s*(\([^\n]*\)|[^\n]+)',settings):
        declared.update(':'+s.lstrip(':') for s in re.findall(r'["\']([:\w.-]+)["\']',match.group(1)))
    remaps={m.group(1):m.group(2) for m in re.finditer(r'project\(["\'](:[\w:.-]+)["\']\)\.projectDir\s*=\s*(?:file\(|new File\(rootDir,\s*)["\']([^"\']+)',settings)}
    catalog=read(root/'gradle/libs.versions.toml')
    aliases=[]
    try:
        import tomllib
        cat=tomllib.loads(catalog)
        aliases=[k.replace('-','.').replace('_','.') for k,v in cat.get('plugins',{}).items() if isinstance(v,dict) and v.get('id')=='com.android.application']
    except (ValueError,ImportError): pass
    modules=[]
    candidates=[(':',root)]+[(name,root/remaps.get(name,name.strip(':').replace(':','/'))) for name in sorted(declared)]
    for name,path in candidates:
        if not path.resolve().is_relative_to(root.resolve()): raise ProjectError('External module paths are not supported')
        text=read(build_file(path))
        text=re.sub(r'(?:id\s*\(?\s*[\"\']com\.android\.application[\"\']|alias\s*\([^)]*\))[^{}\n]*?\s+apply\s*(?:\(\s*)?false', '', text)
        if not ('com.android.application' in text or any('libs.plugins.'+a in text for a in aliases)): continue
        modules.append(Module(name,path,literal(text,'applicationId'),literal(text,'compileSdk') or literal(text,'compileSdkVersion'),literal(text,'minSdk') or literal(text,'minSdkVersion'),literal(text,'buildToolsVersion'),literal(text,'versionName')))
    if not modules: raise ProjectError('No application module found. Convention plugins/dynamic settings may require project-specific support.')
    wrapper=read(root/'gradle/wrapper/gradle-wrapper.properties')
    m=re.search(r'gradle-(\d+\.\d+(?:\.\d+)?)-(?:bin|all)\.zip',wrapper)
    if not m: raise ProjectError('Cannot determine Gradle version from gradle-wrapper.properties')
    gradle=m.group(1); gv=tuple(map(int,gradle.split('.')))
    if gv<(7,3): raise ProjectError('This release supports Gradle 7.3 or newer')
    java=17
    all_text=read(build_file(root))+'\n'+ '\n'.join(read(build_file(m.directory)) for m in modules)
    versions=[int(v) for v in re.findall(r'(?:VERSION_|JavaLanguageVersion\.of\(\s*|jvmToolchain\(\s*)(\d+)',all_text)]
    if any(v>21 for v in versions): raise ProjectError('Java newer than 21 is not supported in this release')
    if 21 in versions:
        if gv<(8,5): raise ProjectError('Java 21 execution requires Gradle 8.5 or newer')
        java=21
    warnings=['Static analysis cannot resolve all Gradle expressions. Actual variants, dependencies and APK metadata are validated during Build.']
    if any(not m.compile_sdk for m in modules): warnings.append('Compile SDK is dynamic; Gradle will resolve it during Build.')
    if 'includeBuild' in settings: warnings.append('Composite build detected; included builds can execute additional code.')
    if (root/'package.json').exists(): warnings.append('Node/React Native projects need additional tooling and are not supported automatically.')
    return Project(literal(settings,'rootProject.name') or root.name,root,workspace or source,modules,gradle,java,warnings)
