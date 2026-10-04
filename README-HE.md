# עדכון לגרסת 0.2

מומלץ להוריד את AndroidCompiler.exe היחיד מלשונית Releases. אין צורך בחילוץ ZIP.
בעדכון זה חודש הממשק ותוקנו מסלולים שבהם כפתור קימפול לא נתן תגובה ברורה.
23 בדיקות אוטומטיות ובדיקת פתיחת ה־EXE עברו על Windows ב־GitHub Actions.
בדיקות שימוש ידניות ובניית APK מלאה על Windows עדיין לא הושלמו.
ההוראות להלן כוללות גם את מסלול ZIP הישן מגרסת 0.1.

# AndroidCompiler — גרסת Preview 0.1

תוכנת Desktop לייבוא פרויקט Android, הכנת סביבת Build פרטית והפקת APK.
**זו גרסת Preview, לא גרסה מסחרית מאושרת.** מנוע הבנייה נבדק בפועל ב־Linux;
חבילת Windows נוצרה בקימפול צולב, אך לא הורצה על מחשב Windows בסביבה זו.

## שימוש בחבילת Windows

1. חלצו את **כל** קובץ AndroidCompiler-Windows-x64.zip לתיקייה מקומית.
2. פתחו `AndroidCompiler.exe`. השאירו לצדו את התיקיות `runtime` ו־`app`.
3. בחרו/גררו תיקיית Android או ZIP. אפשר להתחיל מתיקיית `sample` המצורפת.
4. במסך „מה הבנתי” בדקו מודול, SDK, מזהה אפליקציה וסוג Build.
5. אשרו שאתם סומכים על הפרויקט ולחצו „התחל Build”.
6. בהפעלה הראשונה אשרו את רישיונות Android לאחר קריאתם. הכלים יורדים אוטומטית.
7. בסיום בחרו „פתח תיקיית Output”. נשמרים APK ודוח JSON.

לא נדרשת התקנת Python, Qt, Android Studio, Java, Gradle או SDK אצל משתמש
חבילת Windows. נדרש Windows 10/11 x64; אין תמיכה ב־Windows 7 או ARM64 native.
זהו EXE נייד עם קובצי ריצה נלווים, לא EXE יחיד ולא Installer.
ה־EXE אינו חתום בתעודת Authenticode מסחרית; אין לעקוף חסימה ארגונית כדי להפעילו.

## מה קיים

- ממשק Qt כהה, עברית/RTL, החלפה לאנגלית, בחירת תיקייה/ZIP ו־Drag & Drop.
- ניתוח ראשוני ללא הרצת Gradle, זיהוי מודולים והצגת ערכים שאינם ידועים.
- העתקת הפרויקט לסביבת עבודה; הפרויקט המקורי אינו נכתב במהלך הפעולות הרגילות.
- ניהול JDK 17/21, הורדת גרסת Gradle מתוך wrapper properties,
  Android command-line tools, SDK Platforms ו־Build Tools.
- אימות Hash בהורדות הכלים, Cache קבוע ושימוש ב־Proxy/תעודות מערכת עבור Java.
- אישור מפורש לפני Build, Logs חיים, שלבי Gradle אמיתיים וביטול תהליך.
- Debug חתום בחתימת פיתוח; Release יכול להשתמש בחתימת הפרויקט או ב־Keystore
  שנוצר/נבחר בממשק. Release ללא חתימה מוצג במפורש כלא חתום.
- zipalign, apksigner sign/verify, אימות מבנה APK וקריאת metadata באמצעות aapt.
- העתקת כל תוצרי הווריאנטים שנוצרו, כולל APK מפוצלים, לתיקיית Output נפרדת.
- ניסיון תיקון אחד כאשר מזוהה במדויק חבילת SDK חסרה; אין שינוי אוטומטי בקוד.

## נתונים, ביצועים ובטיחות

הנתונים נשמרים תחת תיקיית AppLocalData של Windows בשם AndroidCompiler
(לרוב `%LOCALAPPDATA%\AndroidCompiler\AndroidCompiler`). אין צורך ב־PATH גלובלי.
תיקיית `tools` מכילה את הכלים וה־Cache, `Output` את התוצרים ו־`Logs` את היומנים.
הכלים והתלויות עשויים לצרוך כמה GB. הורדה ראשונה עשויה לקחת דקות רבות.

תיקיית העבודה הזמנית נשארת זמינה לבנייה חוזרת ונמחקת בעת מעבר לפרויקט חדש או
סגירה תקינה. סגירה בכוח עלולה להשאיר תיקיות עבודה; ניתן להסירן כשהתוכנה סגורה.
ה־Cache נשמר בכוונה. Gradle מופעל עם `--no-daemon`, עד שני workers ו־2 GB JVM;
קומפיילר Kotlin מוגדר לעבוד בתוך תהליך Gradle. בפרויקט גדול ייתכן שצריך יותר RAM.

ZIP נבדק לנתיבי traversal, נתיבי Windows מיוחדים, קישורים, כפילויות,
מספר קבצים וגודל לא דחוס. קבצי `local.properties` מועתקים בלי נתיבי SDK/NDK/CMake
מקומיים, והנתיב הפרטי ל־SDK נוסף בעותק. ערכים אחרים נשמרים.

**אין כאן Sandbox לקוד Gradle.** Build הוא הרצת קוד בעל הרשאות המשתמש:
סקריפטים ותוספים עלולים לגשת לקבצים ולרשת מחוץ לתיקיית העבודה. יש לבנות רק
פרויקטים מהימנים. הגנת ZIP אינה מבטיחה שפרויקט זדוני בטוח להרצה.

## מגבלות ממשיות

- לא נבדקה הפעלת EXE על Windows, פתיחת Explorer או association לקובצי APK.
- ניתוח Groovy/Kotlin הוא סטטי ושמרני. Gradle הוא שפה ניתנת לתכנות, ולכן לא
  ניתן להבטיח לפני הרצה זיהוי מלא של משתנים, custom plugins או כל התלויות.
- נתמכים פרויקטים רגילים עם settings.gradle(.kts), הצהרות include מילוליות,
  מודול com.android.application וגרסת Gradle ב־gradle-wrapper.properties.
  יש תמיכה בכינוי plugin מקטלוג `gradle/libs.versions.toml` ובמיפויי projectDir פשוטים.
- נדרשת Gradle 7.3 ומעלה; זיהוי Java מעבר ל־21 אינו נתמך. גרסאות וכלים חריגים
  עשויים להיכשל. אין יצירת קובצי Build חסרים ואין המרה של קוד שאינו פרויקט Android.
- Flutter, React Native/Node, KMP מורכב, NDK/CMake, מאגרים פרטיים, credentials,
  custom build types וקונבנציות מורכבות אינם נתמכים אוטומטית באופן מלא.
- נתמכים Debug ו־Release; פרויקטים עם flavors עשויים להפיק כמה APK.
- Build ראשוני ותלויות שלא נשמרו דורשים אינטרנט. NetFree/Proxy יכול לחסום שרתי
  הורדה; התוכנה אינה עוקפת סינון. Proxy עם שם משתמש וסיסמה לא נתמך אוטומטית.
- רישיונות חדשים שלא אושרו, תנאי ספק משתנים או הגדרות פרויקט חריגות עלולים לעצור Build.
- אין הבטחה שכל פרויקט תקין ייבנה, ואין תיקון אוטומטי של שגיאות Java/Kotlin.
- „פתח APK” משתמש בשיוך הקבצים של Windows; הוא אינו מתקין APK על Android.
- רכיבי הממשק מתורגמים; פלט Gradle, שמות משימות וחלק מהאבחונים נשארים באנגלית.

## בנייה מהמקור — למפתח בלבד

דרוש Python 3.12 x64 במחשב הבנייה; אין צורך בו אצל משתמש ה־EXE.

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
python main.py
.\packaging\build-windows.ps1
```

פקודת האריזה מפיקה `dist\AndroidCompiler\AndroidCompiler.exe` ו־ZIP נייד.
ניתן גם להריץ את workflow המצורף ב־GitHub Actions דרך `workflow_dispatch`.
הוא לא הופעל בחשבון GitHub כחלק ממשימה זו. בחירת integration ב־workflow מורידה
כלי Android ומאשרת את רישיונותיהם; יש לקרוא את התנאים לפני בחירה זו.

### שחזור החבילה שנוצרה בקימפול צולב

ה־launcher מקומפל ב־Zig 0.13.0 ל־Windows GUI x64. `packaging/portable.py`
מצרף CPython embeddable ו־wheels של Windows; ההורדות מתועדות ב־runtime-manifest.json.

```text
python -m ziglang cc -target x86_64-windows-gnu -Os -municode -Wl,--subsystem,windows packaging/launcher.c -o packaging/AndroidCompiler.exe -luser32
python packaging/portable.py --downloads downloads --launcher packaging/AndroidCompiler.exe
```

בתיקיית downloads נדרשים Python 3.12.10 embeddable amd64 ושני wheels בגרסת
6.8.3: PySide6-Essentials ו־shiboken6, בפורמט cp39-abi3-win_amd64.

## ארכיטקטורה

- `androidcompiler/ui.py` — חלון Qt, Drag & Drop, אישור, חתימה ופעולות תוצאה.
- `project.py` — Workspace, חילוץ בטוח וניתוח Gradle סטטי.
- `toolchain.py` — הורדות מאומתות, SDK, רישיונות ו־Cache.
- `network.py` — Proxy ו־trust store פרטי המבוסס על תעודות מערכת.
- `runtime.py` — הרצת תהליכים, פלט חי, ביטול ואבחון שגיאות.
- `build.py` — תזמור Build, תיקון SDK מוגבל, חתימה ואימות APK.
- `tests/` — בדיקות ממוקדות ובדיקות אינטגרציה אמיתיות לפי בחירה.
- `packaging/` — launcher C, bootstrap ודרכי אריזה.

לפירוט בדיקות: TEST-REPORT.md. רישיונות רכיבי צד ג': THIRD-PARTY.md.
הפוסט לגרסת הניסיון נמצא בקובץ FORUM-POST-HE.md.
