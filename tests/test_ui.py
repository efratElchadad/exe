import os, time
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
from PySide6.QtCore import QMimeData,QUrl,QPointF,QPoint,Qt
from PySide6.QtGui import QDragEnterEvent,QDropEvent
from PySide6.QtWidgets import QApplication
from androidcompiler.ui import Window,STYLE

SAMPLE=Path(__file__).resolve().parents[1]/'sample'
app=QApplication.instance() or QApplication([]);app.setStyleSheet(STYLE)

def wait_job(w):
    deadline=time.monotonic()+15
    while time.monotonic()<deadline:
        app.processEvents()
        if w.job and w.job.isFinished():app.processEvents();return
        time.sleep(.01)
    raise AssertionError('Worker did not finish')

def test_drag_folder_review_logs(tmp_path):
    w=Window(tmp_path);w.show();app.processEvents()
    mime=QMimeData();mime.setUrls([QUrl.fromLocalFile(str(SAMPLE))])
    enter=QDragEnterEvent(QPoint(20,20),Qt.CopyAction,mime,Qt.LeftButton,Qt.NoModifier)
    QApplication.sendEvent(w.drop,enter);assert enter.isAccepted()
    drop=QDropEvent(QPointF(20,20),Qt.CopyAction,mime,Qt.LeftButton,Qt.NoModifier)
    QApplication.sendEvent(w.drop,drop);wait_job(w)
    assert w.stack.currentIndex()==1 and w.modules.currentText()==':app'
    assert w.start.isEnabled();assert not w.trust.isChecked();w.trust.setChecked(True)
    w.busy('Test');w.log('actual output');assert 'actual output' in w.logpath.read_text(encoding="utf-8")
    w.failed('Compilation failed');assert w.retry.isVisible()
    w.review();assert w.stack.currentIndex()==1
    w.close()

def test_zip_drop(tmp_path):
    import zipfile
    z=tmp_path/'sample.zip'
    with zipfile.ZipFile(z,'w') as a:
        for p in SAMPLE.rglob('*'):
            if p.is_file():a.write(p,p.relative_to(SAMPLE))
    w=Window(tmp_path/'app');w.show();app.processEvents()
    mime=QMimeData();mime.setUrls([QUrl.fromLocalFile(str(z))])
    enter=QDragEnterEvent(QPoint(20,20),Qt.CopyAction,mime,Qt.LeftButton,Qt.NoModifier);QApplication.sendEvent(w.drop,enter)
    drop=QDropEvent(QPointF(20,20),Qt.CopyAction,mime,Qt.LeftButton,Qt.NoModifier);QApplication.sendEvent(w.drop,drop);wait_job(w)
    assert w.project.modules[0].compile_sdk=='35'
    w.toggle_language();assert w.layoutDirection()==Qt.LeftToRight
    w.close()

def test_output_actions_dispatch_exact_paths(tmp_path,monkeypatch):
    from androidcompiler.ui import QDesktopServices
    paths=[]
    monkeypatch.setattr(QDesktopServices,'openUrl',lambda url:paths.append(url.toLocalFile()) or True)
    w=Window(tmp_path/'app');apk=tmp_path/'Output/sample.apk';apk.parent.mkdir();apk.write_bytes(b'not used as build evidence')
    w.results=[{'path':str(apk)}]
    w.open_output();w.open_apk()
    assert [Path(value) for value in paths]==[apk.parent,apk]
    w.close()

def test_click_requests_trust_and_explains_decline(tmp_path,monkeypatch):
    from PySide6.QtWidgets import QMessageBox
    w=Window(tmp_path);w.show();w.import_path(str(SAMPLE));wait_job(w)
    calls=[]
    monkeypatch.setattr(QMessageBox,'question',lambda *a,**k:calls.append(a) or QMessageBox.No)
    w.start.click();app.processEvents()
    assert calls and w.stack.currentIndex()==1
    assert 'לא התחיל' in w.review_notice.text()
    w.close()

def test_click_reaches_engine_and_shows_failure(tmp_path,monkeypatch):
    from PySide6.QtWidgets import QMessageBox
    from androidcompiler import ui
    reached=[]
    class FailingEngine:
        def __init__(self,*args):pass
        def build(self,*args):
            reached.append(args)
            raise RuntimeError('REGRESSION: engine failure must be visible')
    monkeypatch.setattr(ui,'BuildManager',FailingEngine)
    monkeypatch.setattr(QMessageBox,'question',lambda *a,**k:QMessageBox.Yes)
    w=Window(tmp_path);w.show();w.import_path(str(SAMPLE));wait_job(w)
    w.start.click()
    assert w.stack.currentIndex()==2
    wait_job(w)
    assert reached and 'REGRESSION' in w.logs.toPlainText()
    assert 'REGRESSION' in w.logpath.read_text(encoding="utf-8")
    assert w.retry.isVisible() and not w.clock.isActive()
    w.close()

def test_import_result_delivered_after_worker_finished(tmp_path):
    from PySide6.QtCore import QThread
    w=Window(tmp_path);observed=[]
    w.busy('testing')
    w.launch(lambda job:42,lambda result:observed.append((result,w.job.isRunning(),QThread.currentThread()==app.thread())))
    wait_job(w)
    assert observed==[(42,False,True)]
    w.close()

def test_log_filter_export_and_full_log(tmp_path,monkeypatch):
    from androidcompiler.logview import QFileDialog
    w=Window(tmp_path/'app');w.logpath=tmp_path/'full.log'
    w.log('normal output');w.log('WARNING: deprecated API');w.log('ERROR: missing item')
    w.logpanel.level.setCurrentIndex(1);w.logpanel.render()
    assert 'missing item' in w.logs.toPlainText() and 'normal output' not in w.logs.toPlainText()
    w.logpanel.copy();assert 'missing item' in QApplication.clipboard().text()
    dest=tmp_path/'filtered.txt';monkeypatch.setattr(QFileDialog,'getSaveFileName',lambda *a:(str(dest),'Text'))
    w.logpanel.save();assert 'missing item' in dest.read_text('utf-8')
    assert 'normal output' in w.logpath.read_text('utf-8')
    w.logpanel.search.setText('absent');w.logpanel.render();assert not w.logs.toPlainText()
    w.close()

def test_log_bounded_and_credit_link(tmp_path,monkeypatch):
    from androidcompiler.ui import QDesktopServices
    from androidcompiler.guide import CREDIT_URL,GUIDE_HE,GUIDE_EN
    calls=[];monkeypatch.setattr(QDesktopServices,'openUrl',lambda url:calls.append(url.toString()) or True)
    w=Window(tmp_path);w.open_credit();assert calls==[CREDIT_URL] or calls==[QUrl(CREDIT_URL).toString()]
    w.logpanel.append('\n'.join(str(i) for i in range(5100)));w.logpanel.render()
    assert len(w.logpanel.rows)==5000 and w.logpanel.rows[0][1]=='100'
    assert 'Offline' in GUIDE_HE and 'Offline' in GUIDE_EN
    w.close()
