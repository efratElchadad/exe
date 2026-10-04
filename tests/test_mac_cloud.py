import json,threading,zipfile
from pathlib import Path
import pytest
from androidcompiler.mac_cloud import MacCloud
from androidcompiler.desktop import analyze_desktop
from androidcompiler.project import Workspace
from androidcompiler.runtime import Runner,Cancelled

def test_private_upload_poll_download(tmp_path,monkeypatch):
    src=tmp_path/'src';src.mkdir();(src/'main.py').write_text('print(1)')
    w=Workspace(tmp_path/'work');p=w.import_project(src,lambda s,w:analyze_desktop(s,w,'python'))
    cloud=MacCloud(tmp_path,Runner(lambda _:None,lambda _:None),'SECRET','mac-builds');calls=[]
    def api(path,data=None,method=None,check=True):
        calls.append((path,data))
        if path=='/user':return {'login':'tester'}
        if path=='/repos/tester/mac-builds':return {'private':True,'default_branch':'main'}
        if '/git/ref/heads/' in path:return {'object':{'sha':'head'}}
        if path.endswith(('/git/blobs','/git/trees','/git/commits')):return {'sha':'new'}
        if path.endswith('/git/refs'):return {}
        if '/actions/runs?' in path:return {'workflow_runs':[{'id':1,'status':'completed','conclusion':'success','html_url':'https://github.com/tester/mac-builds/actions/runs/1'}]}
        if path.endswith('/jobs'):return {'jobs':[]}
        if path.endswith('/artifacts'):return {'artifacts':[{'id':2,'name':'macos-output','expired':False}]}
        raise AssertionError(path)
    monkeypatch.setattr(cloud,'api',api)
    def download(a,dest):
        with zipfile.ZipFile(dest,'w') as z:z.writestr('Application.dmg',b'TEST_TRANSPORT_ONLY')
    monkeypatch.setattr(cloud,'download_artifact',download)
    try:
        results=cloud.build(p,p.modules[0],'Release',tmp_path/'output','arm64')
        assert Path(results[0]['path']).read_bytes()==b'TEST_TRANSPORT_ONLY'
        assert cloud.token==''
        assert 'SECRET' not in json.dumps(calls)
    finally:w.close()

def test_public_repo_rejected_before_upload(tmp_path,monkeypatch):
    src=tmp_path/'src';src.mkdir();(src/'main.py').write_text('print(1)');w=Workspace(tmp_path/'work')
    p=w.import_project(src,lambda s,w:analyze_desktop(s,w,'python'));calls=[]
    cloud=MacCloud(tmp_path,Runner(lambda _:None,lambda _:None),'secret','public-repo')
    def api(path,*a,**k):
        calls.append(path);return {'login':'tester'} if path=='/user' else {'private':False}
    monkeypatch.setattr(cloud,'api',api)
    try:
        with pytest.raises(ValueError,match='private'):cloud.build(p,p.modules[0],'Release',tmp_path/'output','x64')
        assert not any('/git/' in x for x in calls)
    finally:w.close()
