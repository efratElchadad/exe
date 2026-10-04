from __future__ import annotations
import os, signal, subprocess, threading, time, queue
from pathlib import Path

class Cancelled(Exception): pass
class CommandFailed(Exception):
    def __init__(self, code, tail):
        self.code,self.tail=code,tail
        super().__init__(f'Process exited with code {code}\n{tail}')

class Runner:
    def __init__(self, log, stage, cancel=None):
        self.log,self.stage=log,stage
        self.cancel=cancel or threading.Event()
        self.last_stage=''
    def check(self):
        if self.cancel.is_set(): raise Cancelled('Cancelled')
    def run(self, args, cwd, env, stdin=None, timeout=3600):
        self.check()
        flags=subprocess.CREATE_NO_WINDOW|subprocess.CREATE_NEW_PROCESS_GROUP if os.name=='nt' else 0
        p=subprocess.Popen([str(x) for x in args],cwd=str(cwd),env=env,stdin=subprocess.PIPE if stdin is not None else subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,creationflags=flags,start_new_session=os.name!='nt',text=True,encoding='utf-8',errors='replace',bufsize=1)
        q=queue.Queue(maxsize=2048)
        def pump():
            try:
                for line in p.stdout: q.put(line)
            finally: q.put(None)
        threading.Thread(target=pump,daemon=True).start()
        if stdin is not None:
            try: p.stdin.write(stdin);p.stdin.close()
            except (BrokenPipeError,OSError): pass
        tail=[]; head=[]; start=time.monotonic()
        try:
            while True:
                self.check()
                if time.monotonic()-start>timeout: raise TimeoutError('Build process timed out')
                try: line=q.get(timeout=.15)
                except queue.Empty: continue
                if line is None: break
                line=line.rstrip(); self.log(line)
                if len(head)<120:head.append(line)
                tail.append(line);tail=tail[-120:]
                if line.startswith('> Task '):
                    task=line[7:].split()[0]
                    self.last_stage=task;self.stage(task)
            code=p.wait(timeout=10)
            self.check()
            if code: raise CommandFailed(code,'\n'.join(head+tail))
            return '\n'.join(head+tail)
        finally:
            if p.poll() is None:
                if os.name=='nt':
                    subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    try: os.killpg(p.pid,signal.SIGKILL)
                    except ProcessLookupError: pass
                p.wait()
            p.stdout.close()

def explain(error):
    s=str(error)
    rules=[(['PKIX','SSL','CERTIFICATE_VERIFY_FAILED'],'חיבור מאובטח נכשל','בדקו סינון רשת ותעודות מערכת. אימות TLS נשאר פעיל.'),(['Could not resolve','UnknownHost','timed out','HTTP Error'],'הורדה או תלות לא זמינה','בדקו חיבור וגישה לשרתי Google, Maven, Gradle ו-Adoptium ואז נסו שוב.'),(['SDK location','Failed to find Platform SDK','failed to find target'],'רכיב SDK חסר','הכנת SDK נכשלה או שנדרשת גרסה מיוחדת. הפרטים מופיעים ביומן.'),(['license','licenses'],'נדרש אישור רישיון','יש לאשר את תנאי כלי Android לפני התקנתם.'),(['requires Java','Unsupported class file'],'אי התאמה של Java','הפרויקט דורש שילוב Java/Gradle שאינו נתמך בזיהוי הנוכחי.'),(['Compilation error','Compilation failed','error:'],'שגיאת קוד בפרויקט','יש לתקן את קובץ המקור המצוין ביומן. התוכנה אינה משנה קוד כדי להסתיר שגיאות.'),(['keystore','password','signing'],'שגיאת חתימה','בדקו קובץ מפתח, כינוי וסיסמאות.')]
    for needles,title,helptext in rules:
        if any(n.lower() in s.lower() for n in needles): return title,helptext
    return 'הפעולה לא הושלמה','פתחו את היומן המלא לקבלת פרטי השגיאה.'
