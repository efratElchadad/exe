"""Rebuild the self-extracting Windows EXE using the portable ZIP and Zig 0.13."""
import base64, hashlib, json, struct, subprocess, sys, zipfile
from pathlib import Path
base=Path(__file__).resolve().parent
source=Path(sys.argv[1]).resolve()
archive=base/'payload.zip'
with zipfile.ZipFile(source) as original,zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as new:
    assert original.testzip() is None
    for info in original.infolist():new.writestr(info,original.read(info.filename))
    for name in ['launcher.c','extract.ps1','build.py','README.txt']:
        new.write(base/name,'AndroidCompiler/self-extractor-source/'+name)
payload=archive.read_bytes();digest=hashlib.sha256(payload).hexdigest()
encoded=base64.b64encode((base/'extract.ps1').read_text().encode('utf-16le')).decode()
(base/'payload-config.h').write_text('#define PACKAGE_ID L"0.1-'+digest[:16]+'"\n#define PACKAGE_SHA L"'+digest+'"\n#define EXTRACTION_COMMAND L"'+encoded+'"\n')
subprocess.run([sys.executable,'-m','ziglang','cc','-target','x86_64-windows-gnu','-Os','-municode','-Wl,--subsystem,windows',str(base/'launcher.c'),'-o',str(base/'stub.exe'),'-luser32'],check=True)
out=base.parent/'AndroidCompiler.exe'
out.write_bytes((base/'stub.exe').read_bytes()+payload+b'ACEXE001'+struct.pack('<q',len(payload)))
print(json.dumps({'file':str(out),'size':out.stat().st_size,'payload_sha256':digest}))
