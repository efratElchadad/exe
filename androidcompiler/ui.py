from __future__ import annotations
import os, sys, threading, traceback, uuid, time, json
from .guide import GUIDE_HE, GUIDE_EN, CREDIT_URL
from .logview import LogPanel
from pathlib import Path
from PySide6.QtCore import Qt, QThread, Signal, QUrl, QStandardPaths, QLockFile, QTimer
from PySide6.QtGui import QDesktopServices, QFont, QColor, QIcon, QPixmap
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QFileDialog,QStackedWidget,QFrame,QComboBox,QFormLayout,QCheckBox,QProgressBar,QPlainTextEdit,QMessageBox,QDialog,QDialogButtonBox,QLineEdit,QScrollArea,QTextBrowser)
from .project import Workspace
from .runtime import Runner, Cancelled, explain
from .build import BuildManager, Signing
from .desktop import DesktopBuilder,analyze_desktop
from .mac_cloud import MacCloud
from .cloud_build import CloudBuilder

ASSETS=Path(__file__).resolve().parent/'assets'
VERSION='0.6.0'

STYLE="""
QToolTip {background:#213750;color:#ffffff;border:1px solid #4bddce;padding:8px;}
QTextBrowser {background:#101c2d;border:1px solid #2a4059;border-radius:12px;padding:20px;font-size:15px;}
QWidget { background:#090f1d; color:#e9edf7; font-family:"Segoe UI"; font-size:14px; }
QFrame#sidebar {background:#101d30;border:1px solid #252d40;border-radius:18px;}
QFrame#sidebar QLabel {background:transparent;}
QLabel#brand {font-size:21px;font-weight:700;}
QLabel#eyebrow {color:#5bdbd1;font-size:12px;font-weight:600;letter-spacing:2px;}
QLabel#title {font-size:30px;font-weight:700;}
QLabel#subtitle {color:#99a5bc;font-size:14px;}
QLabel#step {padding:17px 12px;color:#7c89a4;border-radius:10px;}
QLabel#step[active="true"] {background:#283354;color:#dce3ff;border:1px solid #415381;}
QLabel#notice {background:#22263b;color:#c7d3ff;border:1px solid #424f76;border-radius:10px;padding:14px;}
QLabel#metric {font-size:16px;font-weight:600;color:#d3dcf3;padding:18px;background:#192132;border-radius:12px;}
QFrame#card {background:#171f2f;border:1px solid #2a354d;border-radius:16px;}
QFrame#card QLabel,QFrame#card QCheckBox {background:transparent;}
QFrame#drop {background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #143449,stop:0.5 #152840,stop:1 #242043);border:2px dashed #429caa;border-radius:20px;}
QFrame#drop QLabel {background:transparent;}
QPushButton {background:#202b40;border:1px solid #384762;border-radius:10px;padding:12px 20px;font-weight:600;min-height:21px;}
QPushButton:hover {background:#31415f;border-color:#94a5ff;}
QPushButton:pressed {background:#3c4b75;}
QPushButton:disabled {color:#68758b;background:#181e2b;border-color:#283246;}
QPushButton#primary {background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #45e0d0,stop:1 #68a8ff);color:#061321;border:0;font-weight:700;}
QPushButton#primary:hover {background:#b0bcff;}
QPushButton#quiet {background:transparent;border:0;color:#a0afca;}
QComboBox,QLineEdit {background:#101827;border:1px solid #3c4a63;border-radius:8px;padding:8px;min-height:22px;}
QComboBox QAbstractItemView {background:#24334e;selection-background-color:#495d96;}
QPlainTextEdit {background:#090e18;color:#bdcce5;border:1px solid #2e3c56;border-radius:10px;font-family:"Consolas";font-size:12px;padding:10px;}
QProgressBar {background:#26334b;border:0;border-radius:5px;min-height:9px;max-height:9px;}
QProgressBar::chunk {background:#4bddce;border-radius:5px;}
QCheckBox {spacing:9px;} QCheckBox::indicator {width:19px;height:19px;border:1px solid #6a7d9f;border-radius:5px;background:#0f1725;}
QCheckBox::indicator:checked {background:#a7b5ff;border:3px solid #5266ba;}
QScrollArea {border:0;} QScrollBar:vertical {background:#151e2d;width:8px;} QScrollBar::handle:vertical {background:#435777;border-radius:4px;min-height:25px;}
"""

class Job(QThread):
    success=Signal(object);failure=Signal(str);line=Signal(str);stage=Signal(str);license=Signal(str)
    def __init__(self,fn):
        super().__init__();self.fn=fn;self.cancel=threading.Event();self.answer=threading.Event();self.accepted=False;self.result=None;self.error=None
    def consent(self,text):
        self.answer.clear();self.license.emit(text)
        while not self.answer.wait(.2):
            if self.cancel.is_set():return False
        return self.accepted
    def run(self):
        try:self.result=self.fn(self)
        except Cancelled:self.error='CANCELLED'
        except Exception:self.error=traceback.format_exc()
        finally:self.fn=None

class DropZone(QFrame):
    chosen=Signal(str)
    def __init__(self,text,sub):
        super().__init__();self.setObjectName('drop');self.setAcceptDrops(True);self.setMinimumHeight(235)
        box=QVBoxLayout(self);box.setContentsMargins(25,38,25,38)
        for title,name in [('↓','title'),(text,'title'),(sub,'subtitle')]:
            label=QLabel(title);label.setObjectName(name);label.setAlignment(Qt.AlignCenter);box.addWidget(label)
    def dragEnterEvent(self,e):
        urls=e.mimeData().urls()
        if len(urls)==1 and urls[0].isLocalFile():e.acceptProposedAction()
    def dropEvent(self,e):
        urls=e.mimeData().urls()
        if len(urls)==1 and urls[0].isLocalFile():self.chosen.emit(urls[0].toLocalFile());e.acceptProposedAction()

class Window(QMainWindow):
    def __init__(self,base=None):
        super().__init__();self.he=True;self.job=None;self.workspace=None;self.project=None;self.results=[];self.logpath=None
        self.base=Path(base or QStandardPaths.writableLocation(QStandardPaths.AppLocalDataLocation));self.base.mkdir(parents=True,exist_ok=True)
        self.setWindowIcon(QIcon(str(ASSETS/'app.ico')));self.setWindowTitle('AndroidCompiler · Android build studio');self.resize(1250,900);self.setMinimumSize(1000,780)
        self.started_at=0;self.last_event=0;self.output_root=self.base/'Output'
        self.clock=QTimer(self);self.clock.setInterval(1000);self.clock.timeout.connect(self.tick)
        self.draw()
    def t(self,he,en):return he if self.he else en
    def button(self,text,fn,primary=False):
        b=QPushButton(text);b.setProperty('action',getattr(fn,'__name__',''));b.setAccessibleName(text);b.setCursor(Qt.PointingHandCursor);b.clicked.connect(lambda checked=False:self.invoke(fn))
        if primary:b.setObjectName('primary')
        return b
    def label(self,text,name=None):
        q=QLabel(text);q.setWordWrap(True);q.setTextFormat(Qt.PlainText)
        if name:q.setObjectName(name)
        return q
    def page(self,eyebrow,title,subtitle):
        w=QWidget();b=QVBoxLayout(w);b.setSpacing(14);b.setContentsMargins(6,8,6,8)
        b.addWidget(self.label(eyebrow,'eyebrow'));b.addWidget(self.label(title,'title'));b.addWidget(self.label(subtitle,'subtitle'))
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(w)
        self.stack.addWidget(scroll);return w,b
    def draw(self):
        self.setLayoutDirection(Qt.RightToLeft if self.he else Qt.LeftToRight)
        shell=QWidget();self.setCentralWidget(shell);outer=QHBoxLayout(shell);outer.setContentsMargins(22,22,22,22);outer.setSpacing(28)
        side=QFrame();side.setObjectName('sidebar');side.setFixedWidth(205);sb=QVBoxLayout(side);sb.setContentsMargins(16,25,16,22);sb.setSpacing(12)
        logo=QLabel();logo.setObjectName('brandLogo');logo.setAlignment(Qt.AlignCenter);logo.setPixmap(QPixmap(str(ASSETS/'app.png')).scaled(160,160,Qt.KeepAspectRatio,Qt.SmoothTransformation));logo.setAccessibleName('AndroidCompiler');sb.addWidget(logo)
        sb.addWidget(self.label('ANDROID COMPILER','eyebrow'));sb.addSpacing(30)
        self.steps=[]
        for title in [self.t('01   בחירת פרויקט','01   Import project'),self.t('02   בדיקה ואישור','02   Review & confirm'),self.t('03   קימפול','03   Build'),self.t('04   תוצרים','04   Output')]:
            label=self.label(title,'step');sb.addWidget(label);self.steps.append(label)
        sb.addStretch();sb.addWidget(self.label('LOCAL BUILD ENGINE','eyebrow'));sb.addWidget(self.label(self.t('הכלים מנוהלים כאן.\nאתה בוחר מה לבנות.','Your tools, managed.\nYour project, ready.'),'subtitle'))
        outer.addWidget(side);content=QWidget();outer.addWidget(content,1);layout=QVBoxLayout(content);layout.setContentsMargins(0,0,0,0);layout.setSpacing(18)
        top=QHBoxLayout();header_logo=QLabel();header_logo.setPixmap(QPixmap(str(ASSETS/'app.png')).scaled(44,44,Qt.KeepAspectRatio,Qt.SmoothTransformation));header_logo.setAccessibleName('AndroidCompiler logo');top.addWidget(header_logo);brand=self.label('AndroidCompiler','brand');brand.setLayoutDirection(Qt.LeftToRight);brand.setWordWrap(False);top.addWidget(brand);top.addStretch()
        self.lang=self.button('English' if self.he else 'עברית',self.toggle_language);top.addWidget(self.lang);top.addWidget(self.button(self.t('מדריך ועזרה','Guide & help'),self.show_guide))
        layout.addLayout(top)
        self.stack=QStackedWidget();self.stack.currentChanged.connect(self.mark_step);layout.addWidget(self.stack,1)
        _,b=self.page('ANDROID BUILD STUDIO',self.t('מהקוד שלך — לאפליקציה','From your code to an application'),self.t('סביבת קימפול פרטית. הכלים מוכנים עבורך, בלי Android Studio.','A managed build environment. No Android Studio required.'))
        self.target=QComboBox();self.target.addItems(['Android → APK','Python → EXE','C# / .NET → EXE','Python → Mac (Cloud)','C# / .NET → Mac (Cloud)']);self.target.setToolTip(self.t('בחר את סוג קוד המקור לפני הייבוא. אין המרת APK או EXE קיימים.','Select the source project type before import. Existing APK/EXE conversion is not supported.'));b.addWidget(self.target)
        self.remote=QCheckBox(self.t('בנייה בענן (נדרש GitHub פרטי)','Cloud build (private GitHub required)'));self.remote.setChecked(sys.platform=='darwin');self.remote.setEnabled(sys.platform!='darwin');b.addWidget(self.remote)
        self.drop=DropZone(self.t('גרור לכאן פרויקט מקור','Drop a source project here'),self.t('תיקיית פרויקט או קובץ ZIP','Project folder or ZIP archive'));self.drop.chosen.connect(self.import_path);b.addWidget(self.drop)
        row=QHBoxLayout();row.addStretch();row.addWidget(self.button(self.t('בחר תיקייה','Choose folder'),self.choose_folder,True));row.addWidget(self.button(self.t('בחר ZIP','Choose ZIP'),self.choose_zip));row.addStretch();b.addLayout(row)
        metrics=QHBoxLayout()
        for text in [self.t('SDK אוטומטי','Managed SDK'),self.t('חתימת APK','APK signing'),self.t('Logs בזמן אמת','Live build logs')]:metrics.addWidget(self.label(text,'metric'))
        b.addLayout(metrics);b.addWidget(self.label(self.t('01  ייבוא  →  02  אישור  →  03  קימפול  →  04  APK','01  IMPORT  →  02  REVIEW  →  03  BUILD  →  04  APK'),'notice'));b.addWidget(self.label(self.t('הכנה ראשונה דורשת אינטרנט. כלים ותלויות נשמרים לשימוש חוזר; פרויקט חדש עשוי להזדקק להורדות נוספות.','First setup requires internet. Tools and dependencies are cached; new projects may need more downloads.'),'subtitle'));b.addStretch()
        _,b=self.page('PROJECT REVIEW',self.t('מה הבנתי','What I understood'),self.t('ניתוח ראשוני בלבד. תלויות וערכים דינמיים ייבדקו בזמן הקימפול.','Initial analysis. Dynamic values and dependencies are validated during Build.'))
        card=QFrame();card.setObjectName('card');form=QFormLayout(card);self.project_form=form;form.setContentsMargins(24,20,24,20);form.setSpacing(10)
        self.project_label=self.label('');form.addRow(self.t('פרויקט','Project'),self.project_label)
        self.modules=QComboBox();self.modules.currentIndexChanged.connect(self.module_changed);form.addRow(self.t('מודול / קובץ כניסה','Module / entry point'),self.modules)
        self.fields={}
        for key,title in [('application_id','Application ID'),('compile_sdk','SDK / Runtime'),('min_sdk','Min SDK'),('build_tools','Build Tools'),('version',self.t('גרסה','Version')),('java','Java / Gradle (APK)')]:
            label=self.label('—');label.setLayoutDirection(Qt.LeftToRight);self.fields[key]=label;form.addRow(title,label)
        self.kind=QComboBox();self.kind.addItems(['Debug','Release']);form.addRow('Build type',self.kind);b.addWidget(card)
        destrow=QHBoxLayout();self.destination=QLineEdit(str(self.output_root));self.destination.setReadOnly(True);self.destination.setLayoutDirection(Qt.LeftToRight);destrow.addWidget(self.destination,1);destrow.addWidget(self.button(self.t('בחר תיקיית יעד','Choose output folder'),self.choose_output));b.addLayout(destrow)
        self.macarch=QComboBox();self.macarch.addItems(['Apple Silicon (M1/M2/M3/M4) · arm64','Intel · x64']);self.macarch.hide();b.addWidget(self.macarch)
        self.windowed=QCheckBox(self.t('EXE ללא חלון קונסולה (Python בלבד)','Hide console window (Python only)'));b.addWidget(self.windowed)
        self.warnings=self.label('','subtitle');b.addWidget(self.warnings)
        self.trust=QCheckBox(self.t('אני סומך על הפרויקט ומאשר הרצת קוד Build.','I trust this project and allow its build scripts to execute on this computer.'));b.addWidget(self.trust)
        self.sign=QCheckBox(self.t('חתום Release באמצעות Keystore אישי','Sign Release with a personal keystore'));self.sign.setEnabled(False);self.kind.currentTextChanged.connect(lambda k:self.sign.setEnabled(k=='Release'));b.addWidget(self.sign)
        row=QHBoxLayout();self.start=self.button(self.t('התחל Build','Start Build'),self.start_build,True);self.start.setToolTip(self.t('בדיקת הפרויקט והתחלת הקימפול','Review and begin compilation'));row.addWidget(self.start);row.addWidget(self.button(self.t('חזרה','Back'),self.go_home));row.addStretch();b.addLayout(row)
        self.review_notice=self.label(self.t('מוכן לבדיקה. לחיצה על קימפול תבקש אישור אם עדיין לא סומן.','Ready for review. Build will ask for trust confirmation if needed.'),'notice');b.addWidget(self.review_notice)
        _,b=self.page('LIVE BUILD',self.t('בונים את האפליקציה','Building your application'),self.t('השלב מוצג לפי הפעולה שמתבצעת בפועל. אין אחוזי קימפול משוערים.','Stages reflect actual work. No estimated compilation percentages.'))
        self.current=self.label('','brand');b.addWidget(self.current);self.elapsed=self.label('','notice');b.addWidget(self.elapsed);self.progress=QProgressBar();self.progress.setRange(0,0);self.progress.setTextVisible(False);b.addWidget(self.progress)
        self.activity=QPlainTextEdit();self.activity.setReadOnly(True);self.activity.setMaximumBlockCount(100);self.activity.setMaximumHeight(75);b.addWidget(self.activity)
        logrow=QHBoxLayout();self.logtoggle=self.button(self.t('הצג / הסתר Logs','Show / hide logs'),lambda:self.logpanel.setVisible(not self.logpanel.isVisible()));logrow.addWidget(self.logtoggle);logrow.addStretch();self.cancelbutton=self.button(self.t('בטל','Cancel'),self.cancel_build);logrow.addWidget(self.cancelbutton);b.addLayout(logrow)
        self.logpanel=LogPanel(self.he);self.logs=self.logpanel.editor;b.addWidget(self.logpanel,1)
        self.endrow=QHBoxLayout();self.retry=self.button(self.t('נסה שוב','Try again'),self.review);self.endrow.addWidget(self.retry);self.endrow.addWidget(self.button(self.t('פתח קובץ Logs','Open log file'),self.open_log));self.backbutton=self.button(self.t('חזרה לפרויקט','Back to project'),self.review);self.endrow.addWidget(self.backbutton);b.addLayout(self.endrow)
        _,b=self.page('BUILD OUTPUT',self.t('התוצר שלך מוכן','Your build is ready'),self.t('הקבצים נשמרו בתיקיית היעד, יחד עם דוח הבנייה.','Files are saved in your output folder with a build report.'))
        self.resultselect=QComboBox();self.resultselect.currentIndexChanged.connect(self.result_changed);b.addWidget(self.resultselect)
        self.resulttext=self.label('');self.resulttext.setTextInteractionFlags(Qt.TextSelectableByMouse);b.addWidget(self.resulttext)
        row=QHBoxLayout();row.addWidget(self.button(self.t('פתח קובץ','Open file'),self.open_apk,True));row.addWidget(self.button(self.t('פתח תיקיית תוצרים','Open output folder'),self.open_output));row.addWidget(self.button(self.t('Build נוסף','Another build'),self.review));row.addWidget(self.button(self.t('פרויקט אחר','New project'),self.go_home));b.addLayout(row);b.addStretch()
        footer=QHBoxLayout();footer.addWidget(self.label(self.t('APK · EXE · Mac | בנייה בענן לאחר אישור','APK · EXE · Mac | Cloud builds with consent'),'subtitle'));footer.addStretch();footer.addWidget(self.label('PREVIEW '+VERSION,'eyebrow'));layout.addLayout(footer)
        credit=self.button(self.t('קרדיט: מוקד המערכות · מתמחים טופ ↗','Credit: Moked Hama’arachot · Mitmachim Top ↗'),self.open_credit);credit.setObjectName('quiet');layout.addWidget(credit)
        self.apply_hints()
    def open_credit(self):
        QDesktopServices.openUrl(QUrl(CREDIT_URL))
    def show_guide(self):
        dlg=QDialog(self);dlg.setWindowTitle(self.t('המדריך ל־AndroidCompiler','AndroidCompiler guide'));dlg.resize(850,700)
        box=QVBoxLayout(dlg);browser=QTextBrowser();browser.setOpenExternalLinks(True);browser.setMarkdown(GUIDE_HE if self.he else GUIDE_EN);box.addWidget(browser)
        close=self.button(self.t('סגור מדריך','Close guide'),dlg.accept);box.addWidget(close);dlg.exec()
    def apply_hints(self):
        hints={
            'choose_output':('בוחר היכן לשמור את תוצרי הבנייה. כל בנייה מקבלת תת־תיקייה נפרדת.','Choose where build outputs are saved. Each build gets a separate subfolder.'),
            'choose_folder':('בחירת תיקיית המקור. העבודה נעשית בעותק זמני.','Select a source folder. Build works on a temporary copy.'),
            'choose_zip':('בחירת ארכיון ZIP לחילוץ ובדיקת פרויקט.','Extract and analyze a project ZIP.'),
            'start_build':('מאשר את הפרויקט ומתחיל הכנת כלים וקימפול.','Confirm project trust, prepare tools and compile.'),
            'cancel_build':('מבקש להפסיק את המשימה ותהליכי הבנייה. המתן לסיום הביטול.','Stop the current job and build processes. Wait for cancellation to finish.'),
            'review':('חזרה לפרטי הפרויקט לבחירת סוג בנייה ולניסיון נוסף.','Review the project and build options before another attempt.'),
            'open_apk':('מפעיל EXE או פותח APK ביישום משויך. Windows אינו מתקין APK בעצמו.','Run the EXE or open the APK with an associated app. Windows cannot install APK itself.'),
            'open_output':('פותח את התיקייה שבה נשמרו ה־APK ודוח הבנייה.','Open the folder containing APK files and the build report.'),
            'open_log':('פותח את הלוג המלא בעורך טקסט.','Open the complete build log in a text editor.'),
            'go_home':('בחירת פרויקט אחר וניקוי עותק העבודה הזמני. התוצרים נשמרים.','Choose another project and clean the temporary copy. Output files remain.'),
            'toggle_language':('מעבר בין עברית לאנגלית כשאין משימה פעילה.','Switch Hebrew/English while no job is running.'),
            'show_guide':('הסבר על כל הכפתורים, המושגים, האינטרנט ותהליך הקימפול.','Read about every control, terminology, internet and the build process.'),
            'open_credit':('פתיחת הפרופיל של מוקד המערכות בפורום מתמחים טופ.','Open the credited Mitmachim Top profile.')}
        for button in self.findChildren(QPushButton):
            key=button.property('action')
            if key in hints:button.setToolTip(self.t(*hints[key]))
        self.modules.setToolTip(self.t('מודול Android שמייצר אפליקציה; בפרויקט יכולים להיות כמה מודולים.','The Android application module to build.'))
        self.kind.setToolTip(self.t('Debug לבדיקה, עם חתימת פיתוח. Release להפצה; ייתכן שתידרש חתימה אישית.','Debug is for testing with a development signature. Release is for distribution and may need your signing key.'))
        self.sign.setToolTip(self.t('חתימת Release במפתח שלך. שמור את המפתח והסיסמאות לעדכונים עתידיים.','Sign Release using your own key. Keep the key and passwords for future updates.'))
        self.trust.setToolTip(self.t('Gradle מריץ קוד מהפרויקט בהרשאות המשתמש. תיקייה זמנית אינה ארגז חול אבטחתי.','Gradle executes project code with your user permissions. A temporary folder is not a security sandbox.'))
    def toggle_language(self):
        if self.job and self.job.isRunning():return
        self.he=not self.he;self.draw()
        if self.project:self.populate()
    def choose_output(self):
        path=QFileDialog.getExistingDirectory(self,self.t('תיקיית יעד ל־APK / EXE','APK / EXE output folder'),str(self.output_root))
        if path:self.output_root=Path(path);self.destination.setText(path)
    def choose_folder(self):
        path=QFileDialog.getExistingDirectory(self,self.t('בחר פרויקט','Choose project'))
        if path:self.import_path(path)
    def choose_zip(self):
        path,_=QFileDialog.getOpenFileName(self,'ZIP','','ZIP (*.zip)')
        if path:self.import_path(path)
    def import_path(self,path):
        if self.job and self.job.isRunning():return
        if self.workspace:self.workspace.close();self.workspace=None;self.project=None
        self.busy(self.t('מייבא ומנתח את הפרויקט','Importing and analyzing project'))
        target_index=self.target.currentIndex();remote=self.remote.isChecked() or target_index>=3;engine=['android','python','dotnet','python','dotnet'][target_index]
        def work(job):
            w=Workspace(self.base/'workspaces')
            try:
                project=w.import_project(Path(path),None if engine=='android' else lambda source,workspace:analyze_desktop(source,workspace,engine))
                if remote:project.cloud_target='mac' if target_index>=3 else ('apk' if target_index==0 else 'windows')
                if target_index>=3:project.mac_cloud=True
                if engine!='android' and project.name=='source':project.name=Path(path).stem if Path(path).is_file() else Path(path).name
                return w,project
            except Exception:w.close();raise
        self.launch(work,self.imported)
    def imported(self,result):
        self.workspace,self.project=result;self.populate()
    def populate(self):
        self.modules.blockSignals(True);self.modules.clear()
        self.modules.addItems([m.name for m in self.project.modules]);self.modules.blockSignals(False)
        desktop=hasattr(self.project,'engine')
        for key in ('application_id','min_sdk','version','java'):self.project_form.setRowVisible(self.fields[key],not desktop)
        self.sign.setVisible(not desktop and not getattr(self.project,'cloud_target',None));self.sign.setChecked(False);self.windowed.setVisible(desktop and self.project.engine=='python' and not getattr(self.project,'mac_cloud',False));self.windowed.setChecked(False)
        self.macarch.setVisible(getattr(self.project,'mac_cloud',False))
        self.kind.setCurrentText('Release' if desktop else 'Debug')
        self.project_label.setText(self.project.name);self.module_changed(0)
        translations={
            'Static analysis cannot resolve all Gradle expressions. Actual variants, dependencies and APK metadata are validated during Build.':'הניתוח הראשוני אינו מריץ Gradle. אימות התלויות והנתונים הסופיים יבוצע בזמן הבנייה.',
            'Compile SDK is dynamic; Gradle will resolve it during Build.':'גרסת SDK נקבעת באופן דינמי ותזוהה בזמן הבנייה.',
            'Composite build detected; included builds can execute additional code.':'זוהה פרויקט הכולל פרויקטי Build נוספים, שגם בהם יכול לרוץ קוד.',
            'Node/React Native projects need additional tooling and are not supported automatically.':'פרויקטי Node / React Native דורשים כלים נוספים ואינם נתמכים אוטומטית.'}
        translations['Windows x64 EXE · Python 3.12 / SDK-style .NET 8–10. Build scripts and dependency installers execute with your permissions.']='EXE ל־Windows x64 · Python 3.12 או ‎.NET 8–10. סקריפטים והתקנת תלויות יפעלו בהרשאות שלך.'
        if getattr(self.project,'mac_cloud',False):self.project.warnings=[self.t('בנייה מרוחקת ב־Mac: נדרש GitHub פרטי. הקוד יועלה רק לאחר אישור. תוצר ללא אימות Apple.','Remote Mac build: private GitHub required. Upload requires confirmation. Output is not Apple-notarized.')]
        self.warnings.setText('\n'.join(translations.get(x,x) if self.he else x for x in self.project.warnings));self.trust.setChecked(False);self.stack.setCurrentIndex(1)
    def module_changed(self,index):
        if not self.project or index<0:return
        m=self.project.modules[index]
        for key,label in self.fields.items():
            val=f'{self.project.java} / {self.project.gradle}' if key=='java' else getattr(m,key)
            label.setText(str(val) if val else self.t('לא ידוע — ייפתר ב־Build','Unknown — resolved during Build'))
    def busy(self,stage):
        self.started_at=self.last_event=time.monotonic();self.clock.start();self.elapsed.setText(self.t('הבקשה התקבלה — מתחיל כעת','Request received — starting now'))
        self.logpanel.reset();self.activity.clear();self.current.setText(stage);self.activity.appendPlainText('● '+stage);self.progress.setRange(0,0)
        self.retry.hide();self.backbutton.hide();self.cancelbutton.setEnabled(True);self.lang.setEnabled(False);self.stack.setCurrentIndex(2)
    def launch(self,fn,success):
        logdir=self.base/'Logs';logdir.mkdir(exist_ok=True);self.logpath=logdir/(uuid.uuid4().hex+'.log')
        job=Job(fn);self.job=job
        job.line.connect(self.log);job.stage.connect(self.stage);job.license.connect(self.license_dialog)
        # Deliver the result only once QThread has actually finished. The review
        # screen can no longer expose a Build button while import is still running.
        job.finished.connect(lambda:self.finish_job(job,success))
        self.log(self.t('הפעולה התקבלה. מכין את המשימה…','Request accepted. Preparing the worker…'))
        job.start()
    def finish_job(self,job,success):
        if job is not self.job:return
        self.clock.stop();self.job_done()
        try:
            if job.error:self.failed(job.error)
            else:success(job.result)
        except Exception:self.failed(traceback.format_exc())
    def invoke(self,fn):
        try:fn()
        except Exception:
            self.clock.stop();self.failed(traceback.format_exc());self.stack.setCurrentIndex(2)
    def mark_step(self,index):
        for i,label in enumerate(self.steps):
            label.setProperty('active',i==index);label.style().unpolish(label);label.style().polish(label)
    def tick(self):
        seconds=int(time.monotonic()-self.started_at)
        idle=int(time.monotonic()-self.last_event)
        text=self.t(f'זמן שחלף: {seconds//60:02d}:{seconds%60:02d}',f'Elapsed: {seconds//60:02d}:{seconds%60:02d}')
        if idle>=15:text+=self.t(f'  ·  ממתין לתגובה מהכלי או מהרשת ({idle} שניות). אפשר לבטל.',f'  ·  Waiting for tool/network output ({idle}s). You can cancel.')
        self.elapsed.setText(text)
    def log(self,text):
        self.last_event=time.monotonic();self.logpanel.append(text)
        if self.logpath:
            with self.logpath.open('a',encoding='utf-8') as f:f.write(text+'\n')
    def stage(self,text):
        self.last_event=time.monotonic()
        names={'Preparing managed Python':'מכין סביבת Python פרטית','Installing Python dependencies':'מתקין תלויות Python','Packaging Windows EXE':'אורז קובץ EXE ל־Windows','Preparing managed .NET SDK':'מכין סביבת .NET פרטית','Restoring and publishing Windows EXE':'מוריד תלויות ובונה EXE','Verifying EXE outputs':'מאמת תוצרי EXE','Preparing secure connection certificates':'מכין תעודות אבטחה בפעולה אחת','Preparing Java':'מכין Java','Preparing Gradle':'מכין Gradle','Preparing Android SDK':'מכין Android SDK','Checking SDK packages':'בודק רכיבי SDK','Resolving dependencies / compiling':'פותר תלויות ומקמפל','Verifying APK outputs':'מאמת קובצי APK','Build completed':'הבנייה הושלמה','Aligning and signing APK':'מיישר וחותם APK','Creating signing key — keep a backup':'יוצר מפתח חתימה — חשוב לשמור גיבוי','Repairing missing SDK packages; one retry':'משלים רכיבי SDK חסרים ומנסה שוב'}
        text=names.get(text,text) if self.he else text
        self.current.setText(text);self.activity.appendPlainText('• '+text)
    def job_done(self):self.lang.setEnabled(True);self.cancelbutton.setEnabled(False)
    def start_build(self):
        if not self.project:
            QMessageBox.information(self,'AndroidCompiler',self.t('יש לבחור תיקיית פרויקט או ZIP לפני קימפול.','Choose a project folder or ZIP first.'));return
        if self.job and self.job.isRunning():
            self.stack.setCurrentIndex(2);self.stage(self.t('הפעולה הקודמת עדיין פעילה. המתן או בטל אותה.','Another operation is running. Wait or cancel it.'));return
        if not self.trust.isChecked():
            answer=QMessageBox.question(self,self.t('אישור קימפול','Confirm Build'),self.t('הקימפול יריץ את קוד ה־Build של הפרויקט בהרשאות שלך. האם זה פרויקט מהימן ולהתחיל לבנות אותו?','Build scripts run with your user permissions. Do you trust this project and want to start building it?'),QMessageBox.Yes|QMessageBox.No,QMessageBox.No)
            if answer!=QMessageBox.Yes:
                self.review_notice.setText(self.t('הקימפול לא התחיל: נדרש אישור להרצת הפרויקט.','Build not started: project trust confirmation is required.'));return
            self.trust.setChecked(True)
        if not 0<=self.modules.currentIndex()<len(self.project.modules):
            QMessageBox.warning(self,'AndroidCompiler',self.t('בחר מודול אפליקציה תקין.','Select a valid application module.'));return
        self.output_root.mkdir(parents=True,exist_ok=True)
        if self.output_root.resolve().is_relative_to(self.workspace.path.resolve()):raise ValueError('Choose a destination outside the temporary workspace')
        probe=self.output_root/('.write-check-'+uuid.uuid4().hex)
        try:probe.write_bytes(b'')
        finally:probe.unlink(missing_ok=True)
        cloud=None
        if getattr(self.project,'cloud_target',None):
            cloud=self.cloud_dialog()
            if cloud is None:return
        signing=None
        if self.kind.currentText()=='Release' and self.sign.isChecked():
            signing=self.sign_dialog()
            if signing is None:return
        kind=self.kind.currentText();module=self.project.modules[self.modules.currentIndex()];output=self.output_root;windowed=self.windowed.isChecked();arch=['arm64','x64'][self.macarch.currentIndex()]
        self.busy(self.t('מכין סביבת Build','Preparing build environment'))
        def work(job):
            runner=Runner(job.line.emit,job.stage.emit,job.cancel)
            if cloud:return CloudBuilder(self.base,runner,*cloud).build(self.project,module,kind,output,arch)
            if hasattr(self.project,'engine'):return DesktopBuilder(self.base,runner).build(self.project,module,kind,output,windowed)
            return BuildManager(self.base,runner,job.consent).build(self.project,module,kind,signing,output_root=output)
        self.launch(work,self.completed)
    def cloud_dialog(self):
        dlg=QDialog(self);dlg.setWindowTitle(self.t('אישור העלאה ובנייה בענן','Approve upload and cloud build'));dlg.resize(700,540);form=QFormLayout(dlg)
        form.addRow(self.label(self.t('כל קבצי עותק הפרויקט יועלו למאגר GitHub פרטי בחשבון שלך. הקוד נשאר בהיסטוריית GitHub גם לאחר הבנייה, עד למחיקת המאגר. בדוק שאין בפרויקט סיסמאות או קבצים פרטיים שאינך רוצה להעלות.','All files in the working copy will be uploaded to a private repository in your account. Source remains in GitHub history until you delete the repository. Check for secrets or files you do not want uploaded.')))
        form.addRow(self.label(self.t('נדרש Personal Access Token מסוג classic עם הרשאות repo ו־workflow. יש להזין רק כאן, לא בצ׳אט. הוא נשמר בזיכרון למשימה בלבד. נדרש חשבון GitHub עם Actions פעיל ומכסת דקות זמינה; שימוש מעבר למכסה עשוי לעלות כסף לפי הגדרות החשבון.','Enter a classic Personal Access Token with repo and workflow scopes here, never in chat. It stays in memory for this job only. GitHub Actions must be enabled with available quota; usage may incur charges under your account settings.')))
        form.addRow(self.button(self.t('פתח יצירת אסימון ב־GitHub','Open GitHub token settings'),lambda:QDesktopServices.openUrl(QUrl('https://github.com/settings/tokens/new'))))
        repo=QLineEdit('androidcompiler-cloud-builds');token=QLineEdit();token.setEchoMode(QLineEdit.Password);form.addRow(self.t('שם מאגר פרטי (ייווצר אם חסר)','Private repository name (created if missing)'),repo);form.addRow('GitHub token',token)
        sdk=QCheckBox(self.t('קראתי ואני מסכים לתנאי Android SDK','I have read and accept the Android SDK terms'));sdk.setVisible(getattr(self.project,'cloud_target',None)=='apk');form.addRow(sdk)
        if getattr(self.project,'cloud_target',None)=='apk':form.addRow(self.button(self.t('קרא תנאי Android SDK','Read Android SDK terms'),lambda:QDesktopServices.openUrl(QUrl('https://developer.android.com/studio/terms'))))
        consent=QCheckBox(self.t('אני מאשר העלאת הקוד והרצת הבנייה בחשבון GitHub שלי','I approve uploading the source and running the build in my GitHub account'));form.addRow(consent)
        buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel);buttons.button(QDialogButtonBox.Ok).setEnabled(False)
        def validate():buttons.button(QDialogButtonBox.Ok).setEnabled(consent.isChecked() and (getattr(self.project,'cloud_target',None)!='apk' or sdk.isChecked()) and bool(token.text().strip()) and bool(repo.text().strip()))
        token.textChanged.connect(validate);repo.textChanged.connect(validate);consent.toggled.connect(validate);sdk.toggled.connect(validate);buttons.accepted.connect(dlg.accept);buttons.rejected.connect(dlg.reject);form.addRow(buttons)
        if dlg.exec()!=QDialog.Accepted:return None
        credentials=(token.text().strip(),repo.text().strip());token.clear();return credentials
    def license_dialog(self,text):
        dlg=QDialog(self);dlg.setWindowTitle(self.t('תנאי שימוש ב־Android SDK','Android SDK license terms'));dlg.resize(850,640)
        box=QVBoxLayout(dlg);box.addWidget(self.label(self.t('יש לקרוא ולאשר את תנאי הספק כדי להתקין את הכלים.','Read and accept the supplier terms to install the tools.')))
        editor=QPlainTextEdit();editor.setPlainText(text);editor.setReadOnly(True);editor.setLayoutDirection(Qt.LeftToRight);box.addWidget(editor)
        buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel);buttons.accepted.connect(dlg.accept);buttons.rejected.connect(dlg.reject);box.addWidget(buttons)
        self.job.accepted=dlg.exec()==QDialog.Accepted;self.job.answer.set()
    def sign_dialog(self):
        dlg=QDialog(self);dlg.setWindowTitle(self.t('חתימת Release','Release signing'));dlg.resize(650,370);form=QFormLayout(dlg)
        mode=QComboBox();mode.addItems([self.t('מפתח קיים','Existing keystore'),self.t('צור מפתח חדש','Create new keystore')]);form.addRow(self.t('מצב','Mode'),mode)
        path=QLineEdit();pick=self.button(self.t('בחר קובץ','Choose file'),lambda:None)
        def choose():
            fn=QFileDialog.getSaveFileName if mode.currentIndex()==1 else QFileDialog.getOpenFileName
            p,_=fn(dlg,'Keystore',str(Path.home()/'release.jks'),'Keystore (*.jks *.keystore *.p12)')
            if p:path.setText(p)
        pick.clicked.connect(choose);form.addRow(path,pick)
        alias=QLineEdit('release');sp=QLineEdit();kp=QLineEdit();sp.setEchoMode(QLineEdit.Password);kp.setEchoMode(QLineEdit.Password)
        form.addRow('Alias',alias);form.addRow(self.t('סיסמת Keystore','Store password'),sp);form.addRow(self.t('סיסמת מפתח','Key password'),kp)
        form.addRow(self.label(self.t('שמור גיבוי של המפתח והסיסמאות. הם נדרשים לעדכוני האפליקציה. הסיסמאות אינן נשמרות בהגדרות.','Back up the key and passwords: app updates need the same key. Passwords are not saved in preferences.')))
        buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel);buttons.accepted.connect(dlg.accept);buttons.rejected.connect(dlg.reject);form.addRow(buttons)
        if dlg.exec()!=QDialog.Accepted:return None
        if not path.text() or not alias.text() or not sp.text() or not kp.text():
            QMessageBox.warning(self,'Keystore',self.t('יש למלא את כל השדות.','All fields are required.'));return None
        return Signing(Path(path.text()).resolve(),alias.text(),sp.text(),kp.text(),mode.currentIndex()==1)
    def completed(self,results):
        self.results=results;self.progress.setRange(0,1);self.progress.setValue(1)
        self.resultselect.clear();self.resultselect.addItems([Path(r['path']).name for r in results]);self.result_changed(0);self.stack.setCurrentIndex(3)
    def result_changed(self,index):
        if index<0 or index>=len(self.results):return
        r=self.results[index]
        if r['type']=='Cloud':
            self.resulttext.setText(f"{r['name']}\n{r['variant']}\n{r['bytes']/1024**2:.2f} MiB\n\n{r['path']}\n\n{r['run_url']}");return
        if r['type']=='Mac':
            self.resulttext.setText(f"{r['name']}\n\nmacOS · {r['engine']} · {r['variant']}\n{r['bytes']/1024**2:.2f} MiB\n\n{r['path']}\n\n"+self.t('פתח את ה־DMG במחשב Mac. התוצר אינו חתום ב־Developer ID ואינו מאומת ב־Apple. יישום Windows אינו ניתן להרצה אוטומטית ב־Mac.','Open the DMG on a Mac. No Developer ID signing or Apple notarization. Windows-only applications are not automatically portable.'));return
        if r['type']=='EXE':
            self.resulttext.setText(f"{r['name']}\n\nWindows x64 · {r['engine']} · {r['variant']}\n{r['bytes']/1024**2:.2f} MiB\n\n{r['path']}\n\n"+self.t('EXE ללא חתימת מפרסם. אם נוצרו קבצים נלווים, יש לשמור את תיקיית התוצרים בשלמותה.','EXE has no publisher signature. Keep all companion output files together.'));return
        signature=self.t('חתום','Signed') if r['signed'] else self.t('לא חתום — נדרשת חתימה לפני התקנה','UNSIGNED — sign before installing')
        self.resulttext.setText(f"{r['name']}\n\nApplication ID: {r['applicationId']}\nVersion: {r['version']}\n{r['type']} / {r['variant']}\n{signature}\n{r['bytes']/1024**2:.2f} MiB\n\n{r['path']}")
    def failed(self,error):
        self.clock.stop();self.cancelbutton.setEnabled(False);self.lang.setEnabled(True);self.progress.setRange(0,1);self.progress.setValue(0);self.log(error)
        title,helptext=(self.t('הפעולה בוטלה','Cancelled'),'') if error=='CANCELLED' else explain(error)
        self.current.setText(title);self.activity.appendPlainText(helptext);self.retry.setVisible(self.project is not None);self.backbutton.show();self.logpanel.show()
    def cancel_build(self):
        if self.job:self.job.cancel.set();self.cancelbutton.setEnabled(False);self.stage(self.t('מבטל ומסיים תהליכים…','Cancelling processes…'))
    def review(self):
        if self.job and self.job.isRunning():return
        self.stack.setCurrentIndex(1 if self.project else 0)
    def go_home(self):
        if self.job and self.job.isRunning():return
        if self.workspace:self.workspace.close()
        self.workspace=None;self.project=None;self.stack.setCurrentIndex(0)
    def open_path(self,path):
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(path))):QMessageBox.warning(self,'Open',self.t('לא נמצאה תוכנה לפתיחת הקובץ.','No application could open this file.'))
    def open_log(self):
        if self.logpath and self.logpath.exists():self.open_path(self.logpath)
    def selected(self):return self.results[max(0,self.resultselect.currentIndex())]
    def open_output(self):
        if self.results:self.open_path(Path(self.selected().get('outputDirectory',str(Path(self.selected()['path']).parent))))
    def open_apk(self):
        if self.results:self.open_path(self.selected()['path'])
    def closeEvent(self,event):
        if self.job and self.job.isRunning():
            QMessageBox.information(self,self.t('פעולה פעילה','Operation running'),self.t('יש לבטל את הפעולה ולהמתין לסיום לפני הסגירה.','Cancel and wait for the operation to stop before closing.'));event.ignore();return
        if self.workspace:self.workspace.close()
        event.accept()

def main():
    if os.name=='nt':
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('AndroidCompiler.Desktop')
    app=QApplication(sys.argv);app.setWindowIcon(QIcon(str(ASSETS/'app.ico')));app.setApplicationName('AndroidCompiler');app.setOrganizationName('AndroidCompiler');app.setStyleSheet(STYLE)
    base=Path(QStandardPaths.writableLocation(QStandardPaths.AppLocalDataLocation));base.mkdir(parents=True,exist_ok=True)
    lock=QLockFile(str(base/'app.lock'));lock.setStaleLockTime(0)
    if not lock.tryLock(100):
        QMessageBox.information(None,'AndroidCompiler','AndroidCompiler is already running.');return 1
    window=Window(base)
    def report_exception(kind,value,tb):
        message=''.join(traceback.format_exception(kind,value,tb))
        try:
            (base/'ui-error.log').write_text(message,encoding='utf-8')
            window.failed(message);window.stack.setCurrentIndex(2)
        except Exception:QMessageBox.critical(window,'AndroidCompiler',message[-3000:])
    sys.excepthook=report_exception
    window.show();return app.exec()
