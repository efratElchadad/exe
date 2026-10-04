"""Run after explicit acceptance of SDK terms. Downloads large toolchains."""
import json, sys
from pathlib import Path
from androidcompiler.project import Workspace
from androidcompiler.runtime import Runner, CommandFailed
from androidcompiler.build import BuildManager,Signing
base=Path(sys.argv[1]).resolve();w=Workspace(base/'workspaces');events=[]
r=Runner(lambda s:print(s,flush=True),lambda s:(events.append(s),print('STAGE:',s,flush=True)))
p=w.import_project(Path(__file__).resolve().parents[1]/'sample');m=p.modules[0]
manager=BuildManager(base,r,lambda text:'--accept-sdk-license' in sys.argv)
results={}
try:
 key=base/'test-only-do-not-use.jks'
 signing=Signing(key,'test','test-password-only','test-password-only',not key.exists())
 results['signed_release']=manager.build(p,m,'Release',signing)
 results['repeat_debug']=manager.build(p,m,'Debug')
 src=m.directory/'src/main/java/com/example/hello/MainActivity.java'
 src.write_text(src.read_text()+'\nTHIS IS DELIBERATELY INVALID JAVA;\n')
 try:manager.build(p,m,'Debug')
 except CommandFailed as e:
  assert 'compileDebugJavaWithJavac' in e.tail or 'Compilation failed' in e.tail
  results['real_compile_failure']='correctly surfaced nonzero Gradle result'
 else:raise AssertionError('Invalid Java unexpectedly succeeded')
 (base/'integration-matrix.json').write_text(json.dumps(results,indent=2))
 print('MATRIX PASSED',flush=True)
finally:w.close()
