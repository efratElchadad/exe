from __future__ import annotations
import hashlib, json, os, re, shutil, ssl, tarfile, tempfile, urllib.request, urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from .project import extract_zip
from .network import java_network

REPOSITORY='https://dl.google.com/android/repository/repository2-1.xml'

class Toolchain:
    def __init__(self, base, runner, consent):
        self.base=Path(base);self.base.mkdir(parents=True,exist_ok=True)
        self.runner=runner;self.consent=consent
        self.sdk=self.base/'sdk';self.env=None;self.java=None
    def data(self,url):
        self.runner.check()
        req=urllib.request.Request(url,headers={'User-Agent':'AndroidCompiler/0.1'})
        with urllib.request.urlopen(req,timeout=40,context=ssl.create_default_context()) as r:
            if not r.url.startswith('https://'): raise ValueError('Insecure redirect refused')
            return r.read(20*1024*1024)
    def download(self,url,dest,checksum,algorithm='sha256'):
        if not url.startswith('https://'): raise ValueError('HTTPS required')
        self.runner.log(f'Downloading {url}')
        temp=dest.with_suffix('.part');h=hashlib.new(algorithm)
        req=urllib.request.Request(url,headers={'User-Agent':'AndroidCompiler/0.1'})
        try:
            with urllib.request.urlopen(req,timeout=45) as response,temp.open('wb') as out:
                if not response.url.startswith('https://'): raise ValueError('Insecure redirect refused')
                total=int(response.headers.get('Content-Length',0));done=0;last=-1
                while chunk:=response.read(1024*1024):
                    self.runner.check();h.update(chunk);out.write(chunk);done+=len(chunk)
                    percent=int(done*100/total) if total else -1
                    if percent!=last:
                        self.runner.stage(f'Download {done//1024**2} MiB'+(f' / {total//1024**2} MiB ({percent}%)' if total else ''));last=percent
            if h.hexdigest().lower()!=checksum.strip().lower(): raise ValueError('Download checksum mismatch')
            temp.replace(dest)
        finally: temp.unlink(missing_ok=True)
    def archive_install(self,url,sha,target,algorithm='sha256'):
        if (target/'.complete').exists(): return
        stage=Path(tempfile.mkdtemp(prefix='install-',dir=self.base))
        archive=stage/'download'
        try:
            self.download(url,archive,sha,algorithm)
            unpack=stage/'unpack';unpack.mkdir()
            if url.split('?')[0].endswith('.zip'): extract_zip(archive,unpack)
            else:
                with tarfile.open(archive) as tar:
                    # Python 3.12 data filter confines extraction, rejects device files.
                    tar.extractall(unpack,filter='data')
            if target.exists(): shutil.rmtree(target)
            unpack.replace(target);(target/'.complete').write_text('verified','utf-8')
        finally: shutil.rmtree(stage,ignore_errors=True)
    def jdk(self,major):
        target=self.base/f'jdk-{major}'
        if not (target/'.complete').exists():
            platform='windows' if os.name=='nt' else 'linux'
            assets=json.loads(self.data(f'https://api.adoptium.net/v3/assets/latest/{major}/hotspot?architecture=x64&image_type=jdk&os={platform}&vendor=eclipse'))
            if not assets: raise ValueError('No supported JDK download available')
            package=assets[0]['binary']['package']
            self.archive_install(package['link'],package['checksum'],target)
        executable='java.exe' if os.name=='nt' else 'java'
        matches=list(target.glob('*/bin/'+executable))
        if len(matches)!=1: raise ValueError('Invalid JDK layout')
        return matches[0].parent.parent
    def prepare(self,project):
        self.runner.stage('Preparing Java')
        home=self.jdk(project.java);self.java=home/'bin'/('java.exe' if os.name=='nt' else 'java')
        # Preserve networking/system configuration but discard JVM and Gradle injection variables.
        self.env={k:v for k,v in os.environ.items() if k.upper() not in {'JAVA_TOOL_OPTIONS','_JAVA_OPTIONS','JDK_JAVA_OPTIONS','GRADLE_OPTS','JAVA_OPTS','CLASSPATH','GRADLE_USER_HOME','JAVA_HOME','ANDROID_HOME','ANDROID_SDK_ROOT'}}
        self.env.update(JAVA_HOME=str(home),ANDROID_HOME=str(self.sdk),ANDROID_SDK_ROOT=str(self.sdk),GRADLE_USER_HOME=str(self.base/'gradle-cache'),PATH=str(home/'bin')+os.pathsep+os.environ.get('PATH',''))
        self.net=java_network(home,self.base,self.runner,self.env)
        self.runner.run([self.java,*self.net,'-version'],self.base,self.env)
        self.runner.stage('Preparing Gradle')
        target=self.base/f'gradle-{project.gradle}'
        if not (target/'.complete').exists():
            url=f'https://services.gradle.org/distributions/gradle-{project.gradle}-bin.zip'
            checksum=self.data(url+'.sha256').decode().strip()
            self.archive_install(url,checksum,target)
        self.gradle=target/f'gradle-{project.gradle}'
        self.prepare_sdk()
        props=project.root/'local.properties'
        with props.open('a',encoding='utf-8') as output:output.write('\nsdk.dir='+str(self.sdk).replace('\\','/').replace(':','\\:')+'\n')
    def prepare_sdk(self):
        self.runner.stage('Preparing Android SDK')
        cmd=self.sdk/'cmdline-tools'/'latest'
        if not (cmd/'lib').exists():
            root=ET.fromstring(self.data(REPOSITORY))
            for node in root.iter(): node.tag=node.tag.split('}')[-1]
            package=next(x for x in root.findall('remotePackage') if x.attrib.get('path')=='cmdline-tools;latest')
            host='windows' if os.name=='nt' else 'linux'
            arch=next(a for a in package.findall('./archives/archive') if a.findtext('host-os')==host)
            relative=arch.findtext('./complete/url')
            check=arch.find('./complete/checksum')
            if not relative or '/' in relative or not relative.endswith('.zip'): raise ValueError('Unexpected SDK archive')
            tooltmp=self.base/'android-commandline'
            self.archive_install('https://dl.google.com/android/repository/'+relative,check.text,tooltmp,check.attrib.get('type','sha1'))
            cmd.parent.mkdir(parents=True,exist_ok=True)
            if cmd.exists(): shutil.rmtree(cmd)
            shutil.move(str(tooltmp/'cmdline-tools'),str(cmd))
            shutil.rmtree(tooltmp,ignore_errors=True)
        # Full official license text is displayed before answering sdkmanager's prompts.
        if not (self.base/'accepted-licenses.json').exists() or not (self.sdk/'licenses').exists():
            root=ET.fromstring(self.data(REPOSITORY))
            for node in root.iter():node.tag=node.tag.split('}')[-1]
            licenses={x.attrib['id']:''.join(x.itertext()) for x in root.findall('license')}
            if not licenses: raise ValueError('Could not retrieve SDK license text')
            if not self.consent('\n\n'.join(k+'\n'+v for k,v in licenses.items())): raise ValueError('SDK licenses were declined')
            self.sdk_run(['--licenses'],stdin='y\n'*200)
            if not (self.sdk/'licenses').exists():raise ValueError('SDK license setup failed; check network connectivity')
            (self.base/'accepted-licenses.json').write_text(json.dumps(licenses),'utf-8')
    def sdk_run(self,args,stdin=None):
        cmd=self.sdk/'cmdline-tools/latest'
        return self.runner.run([self.java,*self.net,'-Dfile.encoding=UTF-8','-cp',str(cmd/'lib/*'),'com.android.sdklib.tool.sdkmanager.SdkManagerCli','--sdk_root='+str(self.sdk),*args],self.base,self.env,stdin=stdin)
    def install_sdk(self,module):
        packages=[]
        if module.compile_sdk and module.compile_sdk.isdigit() and not (self.sdk/'platforms'/('android-'+module.compile_sdk)).exists():packages.append('platforms;android-'+module.compile_sdk)
        if module.build_tools and re.fullmatch(r'\d+\.\d+\.\d+',module.build_tools) and not (self.sdk/'build-tools'/module.build_tools).exists(): packages.append('build-tools;'+module.build_tools)
        if packages:
            self.sdk_run(packages)
            for p in packages:
                if not self.sdk.joinpath(*p.split(';')).exists():raise ValueError('SDK package was not installed: '+p)
    def gradle_run(self,project,args):
        return self.runner.run([self.java,*self.net,'-Dfile.encoding=UTF-8','-cp',str(self.gradle/'lib/*'),'org.gradle.launcher.GradleMain','--no-daemon','--console=plain','--stacktrace','--max-workers=2','-Pkotlin.compiler.execution.strategy=in-process','-Dorg.gradle.java.home='+self.env['JAVA_HOME'],'-Dorg.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8 '+ ' '.join('\"'+a+'\"' for a in self.net),*args],project.root,self.env)
