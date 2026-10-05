"""Compile the real Android sample through the exact uploaded cloud worker."""
import json,os,subprocess,sys,tempfile,zipfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='cloud-apk-') as d:
    job=Path(d)
    with zipfile.ZipFile(job/'source.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in (root/'sample').rglob('*'):
            if p.is_file() and 'build' not in p.parts:z.write(p,'Project/'+str(p.relative_to(root/'sample')).replace('\\','/'))
    (job/'build-config.json').write_text(json.dumps({'target':'apk','engine':'android','entry':'Project/app/build.gradle.kts','kind':'Debug','accept_android_licenses':True}))
    # Sample uses a Groovy build file on some source revisions.
    if not (root/'sample/app/build.gradle.kts').exists():
        cfg=json.loads((job/'build-config.json').read_text());cfg['entry']='Project/app/build.gradle';(job/'build-config.json').write_text(json.dumps(cfg))
    env=dict(os.environ,PYTHONPATH=str(root))
    subprocess.run([sys.executable,str(root/'androidcompiler/cloud_job.py')],cwd=job,env=env,check=True)
    apks=list((job/'artifacts').rglob('*.apk'));assert apks,'No APK generated'
    for apk in apks:
        with zipfile.ZipFile(apk) as z:assert 'AndroidManifest.xml' in z.namelist() and 'classes.dex' in z.namelist()
    assert not list((job/'workspaces').glob('project-*')),'Workspace was not cleaned'
    print('CLOUD_ANDROID_BUILD_VERIFIED',[(p.name,p.stat().st_size) for p in apks])
