"""Bounded live log display; the owning window persists the complete raw log."""
from collections import deque
from datetime import datetime
import re
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLineEdit,QComboBox,QCheckBox,QPushButton,QPlainTextEdit,QLabel,QApplication,QFileDialog,QMessageBox

class LogPanel(QWidget):
    def __init__(self,he=True):
        super().__init__();self.he=he;self.rows=deque(maxlen=5000);self.pending=False
        t=lambda a,b:a if he else b
        box=QVBoxLayout(self);box.setContentsMargins(0,0,0,0)
        row=QHBoxLayout();self.search=QLineEdit();self.search.setPlaceholderText(t('חיפוש בלוג…','Search logs…'));self.search.setClearButtonEnabled(True);row.addWidget(self.search,1)
        self.level=QComboBox();self.level.addItems([t('הכול','All'),t('שגיאות','Errors'),t('אזהרות','Warnings')]);row.addWidget(self.level)
        self.follow=QCheckBox(t('גלילה אוטומטית','Auto-scroll'));self.follow.setChecked(True);row.addWidget(self.follow);box.addLayout(row)
        actions=QHBoxLayout()
        for title,fn,hint in [(t('העתק תצוגה','Copy view'),self.copy,t('מעתיק רק שורות שמוצגות לאחר הסינון.','Copy visible filtered lines.')),(t('שמור תצוגה','Save view'),self.save,t('שומר את התצוגה המסוננת כטקסט UTF-8; הלוג המלא נשמר בנפרד.','Save filtered text as UTF-8; the full log is stored separately.'))]:
            button=QPushButton(title);button.clicked.connect(fn);button.setToolTip(hint);actions.addWidget(button)
        self.count=QLabel();actions.addWidget(self.count,1);box.addLayout(actions)
        self.editor=QPlainTextEdit();self.editor.setReadOnly(True);self.editor.setLayoutDirection(Qt.LeftToRight);self.editor.setLineWrapMode(QPlainTextEdit.NoWrap);self.editor.setMinimumHeight(180);box.addWidget(self.editor,1)
        self.search.setToolTip(t('חיפוש בטקסט של עד 5,000 השורות האחרונות.','Search the last 5,000 lines.'));self.level.setToolTip(t('סינון לפי מילות מפתח; אינו קובע אם הבנייה הצליחה.','Keyword filter; does not determine build success.'));self.follow.setToolTip(t('בטל כדי לקרוא שורות קודמות בלי קפיצה לסוף.','Disable to read previous lines without jumping to the end.'))
        self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.setInterval(120);self.timer.timeout.connect(self.render)
        self.search.textChanged.connect(self.schedule);self.level.currentIndexChanged.connect(self.schedule);self.follow.toggled.connect(self.schedule);self.reset()
    def schedule(self,*args):
        if not self.timer.isActive():self.timer.start()
    def reset(self):
        self.timer.stop();self.rows.clear();self.search.clear();self.level.setCurrentIndex(0);self.render()
    def append(self,text):
        stamp=datetime.now().strftime('%H:%M:%S')
        for line in text.splitlines() or ['']:
            line=re.sub(r'\x1b\[[0-9;]*[A-Za-z]','',line)
            self.rows.append((stamp,line))
        # Small batches render immediately; large streams are coalesced to keep UI responsive.
        if len(self.rows)<100:self.render()
        else:self.schedule()
    def render(self):
        query=self.search.text().casefold();level=self.level.currentIndex();shown=[]
        for stamp,line in self.rows:
            lower=line.casefold()
            if query not in lower:continue
            if level==1 and not re.search(r'\b(error|failed|failure|exception)\b',lower):continue
            if level==2 and not re.search(r'\b(warning|warn|deprecated|deprecation)\b',lower):continue
            shown.append(f'[{stamp}] {line}')
        bar=self.editor.verticalScrollBar();old=bar.value();self.editor.setPlainText('\n'.join(shown));bar.setValue(bar.maximum() if self.follow.isChecked() else old)
        self.count.setText((f'{len(shown):,} / {len(self.rows):,} שורות · הלוג המלא נשמר בקובץ' if self.he else f'{len(shown):,} / {len(self.rows):,} lines · full log saved to file'))
    def copy(self):
        self.render();QApplication.clipboard().setText(self.editor.toPlainText())
    def save(self):
        path,_=QFileDialog.getSaveFileName(self,'Save displayed log','build-log.txt','Text (*.txt)')
        if path:
            try:
                from pathlib import Path
                self.render();Path(path).write_text(self.editor.toPlainText(),encoding='utf-8')
            except OSError as error:QMessageBox.warning(self,'Save log',str(error))
