import os, sys, threading, time
import pytest
from androidcompiler.runtime import Runner, CommandFailed, Cancelled, explain

def test_real_process_live_logs(tmp_path):
    logs=[];stages=[];r=Runner(logs.append,stages.append)
    r.run([sys.executable,'-u','-c',"print('> Task :app:compileDebugJavaWithJavac');print('done')"],tmp_path,os.environ.copy())
    assert 'done' in logs and ':app:compileDebugJavaWithJavac' in stages

def test_nonzero_and_friendly_error(tmp_path):
    r=Runner(lambda _:None,lambda _:None)
    with pytest.raises(CommandFailed) as e:r.run([sys.executable,'-c',"print('Compilation failed');exit(2)"],tmp_path,os.environ.copy())
    assert e.value.code==2 and explain(e.value)[0]=='שגיאת קוד בפרויקט'

def test_cancel_process(tmp_path):
    stop=threading.Event();r=Runner(lambda _:None,lambda _:None,stop)
    timer=threading.Timer(.25,stop.set);timer.start();start=time.monotonic()
    with pytest.raises(Cancelled):r.run([sys.executable,'-c','import time;time.sleep(30)'],tmp_path,os.environ.copy())
    assert time.monotonic()-start<4
