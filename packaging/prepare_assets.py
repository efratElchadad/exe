"""Generate mobile resources from the same engine and icon as desktop."""
from pathlib import Path
import runpy,shutil,sys
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
runpy.run_path(str(root/'packaging/make_cloud_bundle.py'))
from androidcompiler.cloud_build import workflow
assets=root/'android-client/app/src/main/assets';assets.mkdir(parents=True,exist_ok=True)
shutil.copy2(root/'androidcompiler/assets/cloud-engine.zip',assets/'cloud-engine.zip')
(assets/'workflow.yml').write_text(workflow('apk').replace('ubuntu-latest','RUNNER'),'utf-8')
draw=root/'android-client/app/src/main/res/drawable';draw.mkdir(parents=True,exist_ok=True)
shutil.copy2(root/'androidcompiler/assets/app.png',draw/'app_logo.png')
