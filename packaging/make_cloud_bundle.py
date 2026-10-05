from pathlib import Path
import zipfile
root=Path(__file__).resolve().parents[1]
files=['__init__.py','project.py','runtime.py','network.py','toolchain.py','build.py','desktop.py','mac_worker.py','cloud_job.py']
dest=root/'androidcompiler/assets/cloud-engine.zip'
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
    for name in files:z.write(root/'androidcompiler'/name,'androidcompiler/'+name)
print(dest)
