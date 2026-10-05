"""Transport contracts only; real engine builds run separately on native CI hosts."""
import base64,json,zipfile
from pathlib import Path
import pytest
from androidcompiler.cloud_build import CloudBuilder,workflow
from androidcompiler.desktop import analyze_desktop
from androidcompiler.project import Workspace
from androidcompiler.runtime import Runner

@pytest.mark.parametrize('target,arch,host,suffix',[('windows','x64','windows-latest','.exe'),('mac','arm64','macos-15','.dmg'),('mac','x64','macos-15-intel','.dmg')])
def test_private_cloud_routes_preserve_companions(tmp_path,monkeypatch,target,arch,host,suffix):
    src=tmp_path/'src';src.mkdir();(src/'main.py').write_text('print(1)')
    w=Workspace(tmp_path/'work');p=w.import_project(src,lambda s,w:analyze_desktop(s,w,'python'));p.cloud_target=target
    cloud=CloudBuilder(tmp_path,Runner(lambda _:None,lambda _:None),'SECRET','builds');calls=[];blobs=[]
    def api(path,data=None,method=None,check=True):
        calls.append((path,data))
        if path=='/user':return {'login':'tester'}
        if path=='/repos/tester/builds':return {'private':True,'default_branch':'main'}
        if '/git/ref/heads/' in path:return {'object':{'sha':'head'}}
        if path.endswith('/git/blobs'):blobs.append(base64.b64decode(data['content']));return {'sha':'blob'}
        if path.endswith(('/git/trees','/git/commits')):return {'sha':'new'}
        if path.endswith('/git/refs') or '/git/refs/heads/' in path:return {}
        if '/actions/runs?' in path:return {'workflow_runs':[{'id':1,'status':'completed','conclusion':'success','html_url':'https://github.com/tester/builds/actions/runs/1'}]}
        if path.endswith('/artifacts'):return {'artifacts':[{'id':2,'name':'build-output','expired':False}]}
        raise AssertionError(path)
    monkeypatch.setattr(cloud,'api',api)
    def download(a,dest):
        with zipfile.ZipFile(dest,'w') as z:
            z.writestr('Application/App'+suffix,b'transport fixture')
            z.writestr('Application/resources/settings.json','{}')
    monkeypatch.setattr(cloud,'download_artifact',download)
    try:
        results=cloud.build(p,p.modules[0],'Release',tmp_path/'output',arch)
        assert (Path(results[0]['outputDirectory'])/'Application/resources/settings.json').is_file()
        assert results[0]['type']=='Cloud' and cloud.token==''
        assert host.encode() in blobs[-1]
        config=json.loads(blobs[-2]);assert config['entry']=='main.py' and config['target']==target
        assert 'SECRET' not in json.dumps(calls)
    finally:w.close()

def test_apk_workflow_runs_on_linux():
    assert 'ubuntu-latest' in workflow('apk')
    assert 'persist-credentials: false' in workflow('apk')
