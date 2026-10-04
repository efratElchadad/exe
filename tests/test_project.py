import os, zipfile, stat
from pathlib import Path
import pytest
from androidcompiler.project import analyze, Workspace, ProjectError, extract_zip

SAMPLE=Path(__file__).resolve().parents[1]/'sample'

def test_folder_import_isolated(tmp_path):
    w=Workspace(tmp_path/'work');p=w.import_project(SAMPLE)
    assert p.name=='HelloAndroid'
    assert [m.name for m in p.modules]==[':app']
    assert p.modules[0].compile_sdk=='35' and p.modules[0].min_sdk=='24'
    assert p.modules[0].application_id=='com.example.hello'
    assert p.gradle=='8.9' and p.java==17
    assert p.root!=SAMPLE
    w.close();assert not w.path.exists()

def test_wrapped_zip(tmp_path):
    z=tmp_path/'project.zip'
    with zipfile.ZipFile(z,'w') as archive:
        for p in SAMPLE.rglob('*'):
            if p.is_file():archive.write(p,'repo-main/'+str(p.relative_to(SAMPLE)))
    w=Workspace(tmp_path/'work');p=w.import_project(z)
    assert p.root.name=='repo-main' and len(p.modules)==1
    w.close()

@pytest.mark.parametrize('name',['../escape','/absolute','C:/x','folder/../../escape','..\\escape','test:stream','CON.txt','folder/file.'])
def test_zip_paths_rejected(tmp_path,name):
    z=tmp_path/'bad.zip'
    with zipfile.ZipFile(z,'w') as a:a.writestr(name,'x')
    with pytest.raises(ProjectError):extract_zip(z,tmp_path/'extract')
    assert not (tmp_path/'escape').exists()

def test_zip_links_and_bomb(tmp_path):
    z=tmp_path/'bad.zip'
    with zipfile.ZipFile(z,'w') as a:
        info=zipfile.ZipInfo('link');info.create_system=3;info.external_attr=(stat.S_IFLNK|0o777)<<16;a.writestr(info,'../elsewhere')
    with pytest.raises(ProjectError):extract_zip(z,tmp_path/'extract')
    with zipfile.ZipFile(z,'w') as a:a.writestr('large','x'*100)
    with pytest.raises(ProjectError):extract_zip(z,tmp_path/'extract2',max_bytes=20)

def test_dynamic_fields_are_not_invented(tmp_path):
    w=Workspace(tmp_path/'work');p=w.import_project(SAMPLE)
    f=p.root/'app/build.gradle.kts';f.write_text('plugins { id("com.android.application") }\nandroid { compileSdk = libs.versions.sdk.get().toInt() }')
    p=analyze(p.root);assert p.modules[0].compile_sdk is None
    w.close()

def test_catalog_plugin(tmp_path):
    w=Workspace(tmp_path/'work');p=w.import_project(SAMPLE)
    (p.root/'gradle/libs.versions.toml').write_text('[plugins]\nandroid-application = { id = "com.android.application", version = "8.7.3" }')
    (p.root/'app/build.gradle.kts').write_text('plugins { alias(libs.plugins.android.application) }\nandroid { compileSdk = 35 }')
    p=analyze(p.root);assert p.modules[0].name==':app'
    w.close()

def test_ambiguous_and_invalid(tmp_path):
    with pytest.raises(ProjectError):analyze(tmp_path)
    for name in ['one','two']:
        (tmp_path/name).mkdir();(tmp_path/name/'settings.gradle').write_text('')
    with pytest.raises(ProjectError):analyze(tmp_path)
