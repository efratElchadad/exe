"""Exercise actual Java trust-store creation; do not fake certificate imports."""
import json, os, shutil, ssl
from pathlib import Path
import pytest
from androidcompiler.network import prepare_trust, system_certificates
from androidcompiler.runtime import Runner, Cancelled

@pytest.fixture
def java_home():
    if os.environ.get('JAVA_HOME'):
        home=Path(os.environ['JAVA_HOME'])
    elif shutil.which('java'):
        home=Path(shutil.which('java')).resolve().parent.parent
    else:pytest.skip('A JDK is required for real TLS integration tests')
    if not (home/'lib/security/cacerts').exists():pytest.skip('JDK cacerts missing')
    return home

class RecordingRunner(Runner):
    def __init__(self):
        self.lines=[];self.stages=[];self.calls=[]
        super().__init__(self.lines.append,self.stages.append)
    def run(self,args,*a,**kw):
        self.calls.append(args)
        return super().run(args,*a,**kw)

def roots():
    certs=system_certificates()
    assert certs,'Test machine has no TLS roots'
    return certs

def test_all_roots_one_java_process_and_cached_reuse(tmp_path,java_home):
    r=RecordingRunner();env=os.environ.copy();certs=roots()
    args=prepare_trust(java_home,tmp_path,r,env,certs)
    assert len(r.calls)==1 and not any('keytool' in str(x) for x in r.calls[0])
    assert any('TLS ready:' in line for line in r.lines)
    assert len(r.lines)<len(certs)+5
    cached=prepare_trust(java_home,tmp_path,r,env,certs)
    assert cached==args and len(r.calls)==1
    # A partial/corrupted store must never be silently reused.
    path=Path(args[0].split('=',1)[1]);path.write_bytes(b'incomplete')
    prepare_trust(java_home,tmp_path,r,env,certs)
    assert len(r.calls)==2 and path.stat().st_size>100
    assert not list(tmp_path.glob('trust-build-*'))

def test_cancel_does_not_publish_cache(tmp_path,java_home):
    class CancelAfterJava(RecordingRunner):
        def run(self,*a,**kw):
            result=super().run(*a,**kw);self.cancel.set();return result
    r=CancelAfterJava()
    with pytest.raises(Cancelled):prepare_trust(java_home,tmp_path,r,os.environ.copy(),roots())
    assert not list(tmp_path.glob('os-trust-v2-*'))
    assert not list(tmp_path.glob('trust-build-*'))
