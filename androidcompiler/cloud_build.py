"""Hosted builds shared by the desktop and Android clients."""
import json,re,shutil,time,uuid,zipfile
from pathlib import Path
from .mac_cloud import MacCloud
from .runtime import Cancelled
from .project import extract_zip

def workflow(target,arch='arm64'):
    host={'apk':'ubuntu-latest','windows':'windows-latest','mac':'macos-15' if arch=='arm64' else 'macos-15-intel'}[target]
    return f'''name: Source build
on: [push]
permissions:
  contents: read
jobs:
  build:
    runs-on: {host}
    timeout-minutes: 45
    steps:
      - uses: actions/checkout@v4
        with:
          persist-credentials: false
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - uses: actions/setup-dotnet@v4
        with:
          dotnet-version: |
            8.0.x
            9.0.x
            10.0.x
      - name: Build source
        run: |
          python -m zipfile -e engine.zip engine
          python engine/androidcompiler/cloud_job.py
        env:
          PYTHONPATH: engine
      - uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: artifacts/
          if-no-files-found: error
          retention-days: 7
'''

class CloudBuilder(MacCloud):
    def build(self,project,module,kind,output_root,arch='arm64',windowed=False):
        try:return self._build(project,module,kind,output_root,arch,windowed)
        finally:self.token=''
    def _build(self,project,module,kind,output_root,arch,windowed):
        target=project.cloud_target
        if Path(output_root).resolve().is_relative_to(project.workspace.resolve()):raise ValueError('Choose an output directory outside the temporary workspace')
        if target not in ('apk','windows','mac') or arch not in ('arm64','x64'):raise ValueError('Invalid cloud target')
        engine=getattr(project,'engine','android')
        if target=='mac' and engine=='dotnet' and not re.fullmatch(r'net(8|9|10)\.0',module.compile_sdk):raise ValueError('Mac needs a cross-platform .NET target without -windows')
        archive=project.workspace/'cloud-source.zip'
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
            for p in project.root.rglob('*'):
                self.runner.check()
                if p.is_file():z.write(p,p.relative_to(project.root))
        if archive.stat().st_size>25*1024**2:raise ValueError('Source ZIP exceeds the current 25 MiB upload limit')
        self.runner.stage('Connecting to private build repository')
        owner=self.api('/user')['login'];self.repo=owner+'/'+self.repo_name
        try:repo=self.api('/repos/'+self.repo)
        except FileNotFoundError:repo=self.api('/user/repos',{'name':self.repo_name,'private':True,'auto_init':True})
        if not repo.get('private'):raise ValueError('A private build repository is required')
        head=self.api('/repos/'+self.repo+'/git/ref/heads/'+repo.get('default_branch','main'))['object']['sha']
        cfg={'target':target,'engine':engine,'entry':module.name,'kind':kind,'accept_android_licenses':target=='apk','windowed':bool(windowed)}
        files={'source.zip':archive.read_bytes(),'engine.zip':Path(__file__).with_name('assets').joinpath('cloud-engine.zip').read_bytes(),'build-config.json':json.dumps(cfg).encode(),'.github/workflows/build.yml':workflow(target,arch).encode()}
        tree=[]
        for name,data in files.items():tree.append({'path':name,'type':'blob','mode':'100644','sha':self.blob(data)})
        treeid=self.api('/repos/'+self.repo+'/git/trees',{'tree':tree})['sha']
        commit=self.api('/repos/'+self.repo+'/git/commits',{'tree':treeid,'parents':[head],'message':'Build source project'})['sha']
        branch='ac-build-'+uuid.uuid4().hex
        self.api('/repos/'+self.repo+'/git/refs',{'ref':'refs/heads/'+branch,'sha':head})
        self.api('/repos/'+self.repo+'/git/refs/heads/'+branch,{'sha':commit,'force':False},method='PATCH')
        self.runner.log('Source retained in private GitHub repository: https://github.com/'+self.repo+'/tree/'+branch)
        start=time.monotonic();last=''
        try:
            while time.monotonic()-start<3600:
                runs=self.api('/repos/'+self.repo+'/actions/runs?head_sha='+commit)['workflow_runs']
                if runs:
                    run=runs[0];self.run_id=run['id'];url=run['html_url']
                    if run['status']!=last:self.runner.stage('Cloud: '+run['status']);self.runner.log(url);last=run['status']
                    if run['status']=='completed':
                        if run['conclusion']!='success':raise RuntimeError('Build '+str(run['conclusion'])+'. Logs: '+url)
                        break
                    jobs=self.api('/repos/'+self.repo+'/actions/runs/'+str(self.run_id)+'/jobs')['jobs']
                    for j in jobs:
                        for step in j.get('steps',[]):
                            if step['status']=='in_progress':self.runner.stage(step['name'])
                self.pause(10)
            else:raise TimeoutError('Cloud build timed out')
            artifacts=self.api('/repos/'+self.repo+'/actions/runs/'+str(self.run_id)+'/artifacts')['artifacts']
            artifact=next(a for a in artifacts if a['name']=='build-output' and not a['expired'])
            dest=Path(output_root)/('Cloud-'+uuid.uuid4().hex[:10]);dest.mkdir(parents=True)
            try:
                downloaded=project.workspace/'cloud-output.zip';self.download_artifact(artifact,downloaded);extract_zip(downloaded,dest,max_bytes=2*1024**3)
                suffix={'apk':'.apk','windows':'.exe','mac':'.dmg'}[target]
                outputs=list(dest.rglob('*'+suffix))
                if not outputs:raise ValueError('No expected output was found')
                results=[{'path':str(p),'name':p.stem,'type':'Cloud','engine':engine,'variant':target+' / '+(arch if target=='mac' else 'x64' if target=='windows' else kind),'bytes':p.stat().st_size,'run_url':url,'outputDirectory':str(dest)} for p in outputs]
                (dest/'cloud-report.json').write_text(json.dumps(results,indent=2),'utf-8');return results
            except Exception:shutil.rmtree(dest,ignore_errors=True);raise
        except (Cancelled,TimeoutError):
            if self.run_id:
                try:self.api('/repos/'+self.repo+'/actions/runs/'+str(self.run_id)+'/cancel',{},check=False)
                except Exception:self.runner.log('Check remote cancellation at https://github.com/'+self.repo+'/actions')
            else:self.runner.log('Check any queued build at https://github.com/'+self.repo+'/actions')
            raise
