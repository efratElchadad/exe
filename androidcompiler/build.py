from __future__ import annotations
import json, os, re, shutil, uuid, zipfile
from dataclasses import dataclass
from pathlib import Path
from .toolchain import Toolchain
from .runtime import CommandFailed

@dataclass
class Signing:
    path: Path
    alias: str
    store_password: str
    key_password: str
    create: bool=False

class BuildManager:
    def __init__(self,base,runner,consent):
        self.base=Path(base);self.runner=runner
        self.tools=Toolchain(self.base/'tools',runner,consent)
    def build(self,project,module,kind='Debug',signing=None,output_root=None):
        if kind not in ('Debug','Release'):raise ValueError('Unsupported build type')
        if signing and kind!='Release':raise ValueError('Custom signing is for Release builds')
        if output_root and Path(output_root).resolve().is_relative_to(project.workspace.resolve()):raise ValueError('Output must be outside the temporary workspace')
        self.tools.prepare(project)
        self.runner.stage('Checking SDK packages')
        self.tools.install_sdk(module)
        # Discard outputs from previous failed attempts: never report a stale APK.
        apkdir=module.directory/'build/outputs/apk'
        if apkdir.exists():shutil.rmtree(apkdir)
        task=(module.name.rstrip(':')+':assemble'+kind)
        self.runner.stage('Resolving dependencies / compiling')
        try:self.tools.gradle_run(project,[task])
        except CommandFailed as error:
            # One narrow repair only. Never rewrite build scripts or source code.
            missing=re.findall(r'(?:platforms;android-\d+|build-tools;\d+\.\d+\.\d+)',error.tail)
            if not missing or not any(x in error.tail.lower() for x in ['not installed','failed to find','missing']):raise
            self.runner.stage('Repairing missing SDK packages; one retry')
            self.tools.sdk_run(sorted(set(missing)))
            self.tools.gradle_run(project,[task])
        self.runner.check();self.runner.stage('Verifying APK outputs')
        outputs=[]
        for meta in sorted(apkdir.rglob('output-metadata.json')):
            data=json.loads(meta.read_text('utf-8'))
            variant=data.get('variantName','')
            if not variant.lower().endswith(kind.lower()):continue
            for element in data.get('elements',[]):
                apk=(meta.parent/element.get('outputFile','')).resolve()
                if not apk.is_relative_to(apkdir.resolve()) or apk.suffix!='.apk' or not apk.is_file():raise ValueError('Invalid APK output metadata')
                outputs.append((apk,data,element))
        if not outputs:raise ValueError('Gradle completed but produced no APK metadata for the selected build type')
        toolsdirs=sorted((self.tools.sdk/'build-tools').glob('*'),key=lambda p:tuple(int(x) for x in re.findall(r'\d+',p.name)))
        toolsdirs=[p for p in toolsdirs if (p/'lib/apksigner.jar').exists()]
        if not toolsdirs:raise ValueError('Android signing verification tool was not installed')
        bt=toolsdirs[-1]
        if signing and signing.create:self.create_key(signing)
        outdir=Path(output_root or self.base/'Output')/f'{re.sub(r"[^\w.-]","_",project.name)}-{uuid.uuid4().hex[:10]}'
        outdir.mkdir(parents=True)
        results=[]
        try:
            for index,(apk,data,element) in enumerate(outputs):
                filename=apk.name.replace('-unsigned.apk','-signed.apk') if signing else apk.name
                dst=outdir/f'{index+1}-{filename}'
                shutil.copy2(apk,dst)
                if signing:self.sign(dst,bt,signing)
                signed=True
                try:self.tools.runner.run([self.tools.java,'-jar',bt/'lib/apksigner.jar','verify','--verbose',dst],outdir,self.tools.env)
                except CommandFailed as e:
                    if kind=='Debug' or signing:raise
                    if 'DOES NOT VERIFY' not in e.tail:raise
                    signed=False
                with zipfile.ZipFile(dst) as z:
                    if 'AndroidManifest.xml' not in z.namelist():raise ValueError('Not an Android APK')
                    if z.testzip() is not None:raise ValueError('Corrupt APK')
                aapt=bt/('aapt.exe' if os.name=='nt' else 'aapt')
                badging=self.runner.run([aapt,'dump','badging',dst],outdir,self.tools.env)
                package=re.search(r"package: name='([^']+)' versionCode='([^']+)' versionName='([^']*)'",badging)
                label=re.search(r"application-label:'([^']*)'",badging)
                results.append({'path':str(dst),'name':label.group(1) if label else project.name,'applicationId':package.group(1) if package else data.get('applicationId'),'version':package.group(3) if package else element.get('versionName'),'type':kind,'variant':data.get('variantName'),'signed':signed,'bytes':dst.stat().st_size,'filters':element.get('filters',[])})
            (outdir/'build-report.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),'utf-8')
            self.runner.stage('Build completed')
            return results
        except Exception:
            shutil.rmtree(outdir,ignore_errors=True)
            raise
    def create_key(self,s):
        if s.path.exists():raise ValueError('Keystore already exists; refusing to overwrite')
        if not s.alias.strip() or len(s.store_password)<6 or len(s.key_password)<6:raise ValueError('Keystore passwords must have at least six characters')
        s.path.parent.mkdir(parents=True,exist_ok=True)
        env={**self.tools.env,'AC_STORE_PASS':s.store_password,'AC_KEY_PASS':s.key_password}
        keytool=Path(env['JAVA_HOME'])/'bin'/('keytool.exe' if os.name=='nt' else 'keytool')
        self.runner.stage('Creating signing key — keep a backup')
        self.runner.run([keytool,'-genkeypair','-keystore',s.path,'-storetype','JKS','-alias',s.alias,'-storepass:env','AC_STORE_PASS','-keypass:env','AC_KEY_PASS','-keyalg','RSA','-keysize','3072','-validity','10000','-dname','CN=AndroidCompiler User'],self.base,env)
    def sign(self,apk,bt,s):
        self.runner.stage('Aligning and signing APK')
        env={**self.tools.env,'AC_STORE_PASS':s.store_password,'AC_KEY_PASS':s.key_password}
        aligned=apk.with_suffix('.aligned.apk')
        zipalign=bt/('zipalign.exe' if os.name=='nt' else 'zipalign')
        self.runner.run([zipalign,'-f','-p','4',apk,aligned],apk.parent,env)
        aligned.replace(apk)
        self.runner.run([self.tools.java,'-jar',bt/'lib/apksigner.jar','sign','--ks',s.path,'--ks-key-alias',s.alias,'--ks-pass','env:AC_STORE_PASS','--key-pass','env:AC_KEY_PASS',apk],apk.parent,env)
