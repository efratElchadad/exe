"""Private GitHub build transport. Credentials stay in memory on this computer."""
import base64,hashlib,json,re,time,urllib.request,urllib.error,uuid,zipfile,shutil
from pathlib import Path
from .runtime import Cancelled

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

WORKFLOW='''name: AndroidCompiler macOS
on: [push]
permissions:
  contents: read
jobs:
  build:
    runs-on: RUNNER
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
        with:
          persist-credentials: false
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - uses: actions/setup-dotnet@v4
        with:
          dotnet-version: SDK
      - name: Build macOS output
        run: python mac_worker.py
      - uses: actions/upload-artifact@v4
        with:
          name: macos-output
          path: artifacts/*.dmg
          if-no-files-found: error
          retention-days: 7
'''

class MacCloud:
    def __init__(self,base,runner,token,repo_name):
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,70}',repo_name):raise ValueError('Invalid repository name')
        self.base=Path(base);self.runner=runner;self.token=token;self.repo_name=repo_name;self.repo=None;self.run_id=None
    def api(self,path,data=None,method=None,check=True):
        if check:self.runner.check()
        req=urllib.request.Request('https://api.github.com'+path,data=json.dumps(data).encode() if data is not None else None,headers={'Authorization':'Bearer '+self.token,'Accept':'application/vnd.github+json','User-Agent':'AndroidCompiler','Content-Type':'application/json'},method=method or ('POST' if data is not None else 'GET'))
        try:
            with urllib.request.build_opener(NoRedirect).open(req,timeout=45) as r:
                body=r.read();return json.loads(body) if body else {}
        except urllib.error.HTTPError as e:
            # Do not include request headers or the token in diagnostics.
            if e.code==404:raise FileNotFoundError('GitHub resource not found') from None
            raise RuntimeError(f'GitHub HTTP {e.code}: check token permissions, Actions access and account quota') from None
    def blob(self,content):return self.api('/repos/'+self.repo+'/git/blobs',{'content':base64.b64encode(content).decode(),'encoding':'base64'})['sha']
    def pause(self,seconds=5):
        if self.runner.cancel.wait(seconds):raise Cancelled()
    def build(self,project,module,kind,output_root,arch):
        if arch not in ('arm64','x64'):raise ValueError('Invalid Mac architecture')
        out=Path(output_root).resolve();out.mkdir(parents=True,exist_ok=True)
        if out.is_relative_to(project.workspace.resolve()):raise ValueError('Output is inside the temporary workspace')
        entry=module.directory.resolve()
        if not entry.is_relative_to(project.root.resolve()):raise ValueError('Invalid entry point')
        sdk='8.0.x'
        if project.engine=='dotnet':
            m=re.fullmatch(r'net(8|9|10)\.0',module.compile_sdk)
            if not m:raise ValueError('Mac .NET builds support a single net8.0/net9.0/net10.0 target without -windows; WPF/WinForms/MAUI are not supported')
            sdk=m[1]+'.0.x'
            for parent in [entry.parent,*entry.parent.parents]:
                if not parent.is_relative_to(project.root):break
                p=parent/'global.json'
                if p.exists():
                    version=json.loads(p.read_text()).get('sdk',{}).get('version')
                    if not re.fullmatch(r'(8|9|10)\.0\.\d+',version or ''):raise ValueError('Unsupported global.json SDK')
                    sdk=version;break
        archive=project.workspace/'mac-source.zip'
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
            for p in project.root.rglob('*'):
                self.runner.check()
                if p.is_file():z.write(p,p.relative_to(project.root))
        if archive.stat().st_size>25*1024**2:raise ValueError('Mac cloud upload currently supports source archives up to 25 MiB')
        self.runner.stage('Connecting to private Mac build repository')
        owner=self.api('/user')['login'];self.repo=owner+'/'+self.repo_name
        try:repo=self.api('/repos/'+self.repo)
        except FileNotFoundError:repo=self.api('/user/repos',{'name':self.repo_name,'private':True,'auto_init':True,'description':'Private AndroidCompiler macOS builds'})
        if not repo.get('private'):raise ValueError('Mac builds require a private repository. Choose a new repository name.')
        default=repo.get('default_branch','main');head=self.api('/repos/'+self.repo+'/git/ref/heads/'+default)['object']['sha']
        branch='ac-macos-'+uuid.uuid4().hex;config={'entry':str(entry.relative_to(project.root)).replace('\\','/'),'engine':project.engine,'kind':kind}
        workflow=WORKFLOW.replace('RUNNER','macos-15' if arch=='arm64' else 'macos-15-intel').replace('SDK',"'"+sdk+"'")
        files={'source.zip':archive.read_bytes(),'build-config.json':json.dumps(config).encode(),'mac_worker.py':Path(__file__).with_name('mac_worker.py').read_bytes(),'.github/workflows/mac-build.yml':workflow.encode()}
        self.runner.stage('Uploading source to private GitHub repository')
        tree=[]
        for name,content in files.items():tree.append({'path':name,'mode':'100644','type':'blob','sha':self.blob(content)})
        tree_sha=self.api('/repos/'+self.repo+'/git/trees',{'tree':tree})['sha']
        commit=self.api('/repos/'+self.repo+'/git/commits',{'message':'Build macOS application','tree':tree_sha,'parents':[head]})['sha']
        self.api('/repos/'+self.repo+'/git/refs',{'ref':'refs/heads/'+branch,'sha':commit})
        self.runner.log('Source uploaded to private repository: https://github.com/'+self.repo+'/tree/'+branch)
        self.runner.log('Sources remain in GitHub history. Artifacts expire after 7 days. Account Actions quotas apply.')
        start=time.monotonic();last=''
        try:
            while time.monotonic()-start<2400:
                self.runner.check()
                runs=self.api('/repos/'+self.repo+'/actions/runs?head_sha='+commit)['workflow_runs']
                if runs:
                    run=runs[0];self.run_id=run['id']
                    jobs=self.api('/repos/'+self.repo+'/actions/runs/'+str(self.run_id)+'/jobs')['jobs']
                    status=' · '.join(s['name']+': '+s['status'] for j in jobs for s in j.get('steps',[]) if s['status'] in ('in_progress','queued')) or run['status']
                    if status!=last:self.runner.stage('Mac: '+status);self.runner.log(status);last=status
                    if run['status']=='completed':
                        self.runner.log(run['html_url'])
                        if run['conclusion']!='success':raise RuntimeError('Mac build '+str(run['conclusion'])+'. Full GitHub logs: '+run['html_url'])
                        break
                else:self.runner.stage('Waiting for GitHub Actions to start')
                self.pause()
            else:raise TimeoutError('Mac cloud build timed out')
            artifacts=self.api('/repos/'+self.repo+'/actions/runs/'+str(self.run_id)+'/artifacts')['artifacts']
            artifact=next((a for a in artifacts if a['name']=='macos-output' and not a['expired']),None)
            if not artifact:raise RuntimeError('No macOS artifact was produced')
            self.runner.stage('Downloading macOS output')
            resultdir=out/('Mac-'+uuid.uuid4().hex[:10]);resultdir.mkdir()
            try:
                self.download_artifact(artifact,project.workspace/'mac-artifact.zip')
                with zipfile.ZipFile(project.workspace/'mac-artifact.zip') as z:
                    names=[i for i in z.infolist() if i.filename.endswith('.dmg') and not i.is_dir()]
                    if len(names)!=1 or names[0].file_size>2*1024**3:raise ValueError('Unexpected Mac output archive')
                    dmg=resultdir/'Application.dmg'
                    with z.open(names[0]) as src,dmg.open('wb') as dst:
                        while chunk:=src.read(1024**2):self.runner.check();dst.write(chunk)
                return [{'path':str(dmg),'name':project.name,'type':'Mac','engine':project.engine,'variant':arch,'signed':False,'bytes':dmg.stat().st_size,'run_url':run['html_url']}]
            except Exception:shutil.rmtree(resultdir,ignore_errors=True);raise
        except (Cancelled,TimeoutError):
            if self.run_id:
                try:self.api('/repos/'+self.repo+'/actions/runs/'+str(self.run_id)+'/cancel',{},check=False)
                except Exception:self.runner.log('Could not confirm remote cancellation. Check GitHub Actions: https://github.com/'+self.repo+'/actions')
            else:self.runner.log('No run ID yet. Check GitHub Actions and cancel any queued build: https://github.com/'+self.repo+'/actions')
            raise
        finally:self.token=''
    def download_artifact(self,artifact,dest):
        url='https://api.github.com/repos/'+self.repo+'/actions/artifacts/'+str(artifact['id'])+'/zip'
        req=urllib.request.Request(url,headers={'Authorization':'Bearer '+self.token,'User-Agent':'AndroidCompiler'})
        try:urllib.request.build_opener(NoRedirect).open(req,timeout=40);raise RuntimeError('Expected artifact download redirect')
        except urllib.error.HTTPError as e:
            if e.code!=302:raise RuntimeError('Artifact download failed: '+str(e.code)) from None
            location=e.headers['Location']
        if not location.startswith('https://'):raise ValueError('Insecure artifact URL')
        # Signed storage URL needs no GitHub token; never forward Authorization.
        h=hashlib.sha256();total=0
        with urllib.request.urlopen(location,timeout=60) as response,dest.open('wb') as output:
            while chunk:=response.read(1024**2):
                self.runner.check();total+=len(chunk)
                if total>2*1024**3:raise ValueError('Artifact exceeds download limit')
                h.update(chunk);output.write(chunk)
        digest=artifact.get('digest')
        if digest and digest!='sha256:'+h.hexdigest():raise ValueError('Artifact checksum mismatch')
