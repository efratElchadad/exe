"""Opt-in REAL SDK / Gradle integration. No mocked processes or APK fixtures."""
import sys, threading
from pathlib import Path
from androidcompiler.project import Workspace
from androidcompiler.runtime import Runner
from androidcompiler.build import BuildManager
base=Path(sys.argv[1]).resolve();base.mkdir(parents=True,exist_ok=True)
w=Workspace(base/'workspaces')
try:
 p=w.import_project(Path(__file__).resolve().parents[1]/'sample')
 r=Runner(lambda s:print(s,flush=True),lambda s:print('STAGE:',s,flush=True))
 manager=BuildManager(base,r,lambda text: '--accept-sdk-license' in sys.argv)
 print(manager.build(p,p.modules[0],'Debug'))
finally:w.close()
