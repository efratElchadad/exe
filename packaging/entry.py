"""Frozen Windows entry point with an unattended EXE startup test."""
import sys, os, json, tempfile
from pathlib import Path
from androidcompiler.ui import main, Window, STYLE
if '--smoke-test' in sys.argv:
    os.environ['QT_QPA_PLATFORM']='offscreen'
    from PySide6.QtWidgets import QApplication
    app=QApplication([]);app.setStyleSheet(STYLE)
    with tempfile.TemporaryDirectory() as d:
        w=Window(Path(d));w.show();app.processEvents()
        assert w.isVisible() and w.drop.acceptDrops()
        result={'opened':True,'drop_enabled':True,'version':'0.2.1','platform':sys.platform,'frozen':getattr(sys,'frozen',False)}
        w.close()
    Path('smoke-test.json').write_text(json.dumps(result,indent=2),'utf-8')
else:
    raise SystemExit(main())
