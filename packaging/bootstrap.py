"""Entry point for the Windows portable distribution."""
import os, sys, json, traceback
from pathlib import Path

def run():
    from androidcompiler.ui import main, Window, STYLE
    if '--smoke-test' in sys.argv:
        import tempfile
        from PySide6.QtWidgets import QApplication
        os.environ['QT_QPA_PLATFORM']='offscreen'
        app=QApplication([]);app.setStyleSheet(STYLE)
        with tempfile.TemporaryDirectory() as temp:
            window=Window(Path(temp));window.show();app.processEvents()
            result={'opened':window.isVisible(),'drop_enabled':window.drop.acceptDrops(),'python':sys.version,'platform':sys.platform}
            window.close()
        Path('smoke-test.json').write_text(json.dumps(result,indent=2),'utf-8')
        return 0
    return main()

try:
    code=run()
except Exception:
    details=traceback.format_exc()
    directory=Path(os.environ.get('LOCALAPPDATA',str(Path.home())))/'AndroidCompiler'
    directory.mkdir(parents=True,exist_ok=True);log=directory/'startup-error.log';log.write_text(details,'utf-8')
    if sys.platform=='win32':
        import ctypes
        ctypes.windll.user32.MessageBoxW(None,'Startup failed. Diagnostic log:\n'+str(log),'AndroidCompiler',0x10)
    code=1
raise SystemExit(code)
