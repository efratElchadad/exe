CREDIT_URL='https://mitmachim.top/user/%D7%9E%D7%95%D7%A7%D7%93-%D7%94%D7%9E%D7%A2%D7%A8%D7%9B%D7%95%D7%AA'
GUIDE_HE='''# המדריך ל־AndroidCompiler
## האם צריך אינטרנט?
כן, בהכנה הראשונה: להורדת Java, Gradle, Android SDK ותלויות הפרויקט. הכלים נשמרים במחשב. בנייה חוזרת עשויה להסתפק במטמון, אבל אין הבטחה לפעולה ללא אינטרנט: גרסאות חדשות, תלויות חסרות, תלויות דינמיות וסקריפטים של הפרויקט יכולים לדרוש רשת. אין כרגע מתג Offline שמונע גישה לרשת. אין צורך ב־Android Studio.

הקימפול מתבצע במחשב שלך. התוכנה אינה מעלה את הפרויקט לשירות קימפול. סקריפטים ותוספים של הפרויקט עצמם יכולים לגשת לרשת. ברשת מסוננת ייתכן שתידרש פתיחת אתרי ההורדות; האפליקציה אינה עוקפת חסימות.
## 1. בחירת פרויקט
**בחר תיקייה** — בחר את תיקיית פרויקט Android. התוכנה מעתיקה אותה לסביבת עבודה זמנית.

**בחר ZIP** — בחר ארכיון פרויקט; הוא מחולץ עם בדיקת נתיבים כדי למנוע כתיבה מחוץ לתיקייה. אפשר גם לגרור תיקייה או ZIP לאזור המסומן.

הניתוח מוצא קובצי settings.gradle ו־build.gradle, גם בפורמט Kotlin. הוא אינו מריץ קוד בשלב זה; ערכים שמחושבים בזמן Build עשויים להופיע כלא ידועים.
## 2. מה הבנתי — בדיקה ואישור
**מודול** — חלק בפרויקט שמייצר אפליקציה. אם נמצאו כמה, בחר את הרצוי.

**Application ID** — מזהה האפליקציה באנדרואיד. **Compile SDK** — גרסת ממשקי Android שבאמצעותה בונים. **Min SDK** — גרסת Android המינימלית להתקנה. **Build Tools** — כלי האריזה, היישור והחתימה. **Java / Gradle** — סביבת ההרצה ומנהל תהליך הבנייה. **גרסה** — גרסת האפליקציה, כשהיא זמינה בניתוח הראשוני.

**Debug** — מתאים לבדיקה ומקבל בדרך כלל חתימת פיתוח אוטומטית. **Release** — בנייה להפצה לפי הגדרות הפרויקט; ללא הגדרת חתימה ייתכן APK לא חתום שלא ניתן להתקנה.

**אני סומך על הפרויקט** — אישור להריץ את סקריפטי הבנייה בהרשאות המשתמש. סביבת עבודה זמנית אינה ארגז חול אבטחתי.

**חתום Release** — פותח בחירה בין Keystore קיים ליצירת חדש. בחר נתיב, Alias (שם המפתח בתוך הקובץ), סיסמת המאגר וסיסמת המפתח. גבה את הקובץ והסיסמאות: עדכון אפליקציה מחייב את אותו מפתח. הסיסמאות אינן נשמרות בהעדפות.

**התחל Build** — מתחיל רק אחרי אישור. **חזרה** — חוזר לבחירת פרויקט ומנקה את העותק הזמני.
## 3. איך עובד הקימפול?
1. מכינים Java, מחברים תעודות אבטחה מהמערכת ומכינים Gradle.
2. מכינים SDK ומתקינים רכיבי פלטפורמה ו־Build Tools חסרים. תנאי הספק מוצגים לאישור כשנדרש.
3. Gradle קורא את הגדרות הפרויקט ומוריד תלויות חסרות. הוא מעבד משאבים, מקמפל Java/Kotlin וממיר לקובצי DEX שאנדרואיד מריץ.
4. Gradle אורז קוד, משאבים ו־Manifest ל־APK לפי Debug או Release והווריאנטים של הפרויקט.
5. התוכנה חותמת אם התבקש, בודקת חתימה ומבנה APK ומעתיקה את התוצרים לתיקיית Output עם דוח.

השלב והזמן שחלף אמיתיים. הפס הנע מציין עבודה, ולא אחוזי השלמה. שקט בלוג יכול להיות הורדה או חישוב; אינו מוכיח תקיעה. הודעת Single-use Daemon של Gradle תקינה: תהליך Java זמני שנסגר בסוף הבנייה.
## 4. לוגים וביטול
**הצג / הסתר Logs** — שינוי תצוגה בלבד; כתיבת הלוג ממשיכה.

**חיפוש** — חיפוש ללא הבחנה בין אותיות גדולות לקטנות. **הכול / שגיאות / אזהרות** — מסנן לפי מילות מפתח; משפט שמכיל error אינו בהכרח כשל בבנייה.

**גלילה אוטומטית** — עוקבת אחרי השורה האחרונה; בטל כדי לקרוא בנחת. התצוגה מחזיקה עד 5,000 שורות, והקובץ שומר את כל הפלט.

**העתק תצוגה / שמור תצוגה** — מעתיק או שומר את השורות המסוננות עם זמן קבלתן. **פתח קובץ Logs** — פותח את הלוג המלא. לפני שיתוף בדוק שאין בו מידע פרטי מהפרויקט.

**בטל** — מפסיק את המשימה ואת תהליכי הבנייה; המתן לסיום הביטול. **נסה שוב / חזרה לפרויקט** — חוזר למסך האישור, ושם מתחילים ניסיון נוסף. תיקון SDK אוטומטי מתבצע רק לשגיאה מזוהה ובניסיון חוזר אחד; קוד מקור שגוי אינו מתוקן אוטומטית.
## 5. התוצר
אפשר לבחור בין APKs אם נוצרו כמה. מוצגים שם, מזהה, גרסה, וריאנט, סוג בנייה, מצב חתימה, גודל ונתיב בפועל.

**פתח APK** — מפעיל את היישום המשויך לקובץ במחשב. Windows אינו מתקין APK בעצמו. **פתח תיקיית Output** — פותח את מיקום התוצרים ודוח הבנייה. **Build נוסף** — חוזר לאישור אותו פרויקט. **פרויקט אחר** — מאפשר לבחור קלט חדש. התוצרים שכבר נוצרו נשמרים.

**English / עברית** — מחליף שפה כשהתוכנה אינה באמצע עבודה. **מדריך ועזרה** — פותח את ההסברים הללו. **קרדיט** — פותח את הפרופיל בדפדפן.
## קרדיט
קרדיט למוקד המערכות מפורום מתמחים טופ.
'''+f'\n[לפרופיל מוקד המערכות]({CREDIT_URL})\n'
GUIDE_EN='''# AndroidCompiler guide
## Internet and privacy
First setup needs internet to download Java, Gradle, Android SDK and project dependencies. Cached builds may work without a connection, but new versions, missing or dynamic dependencies and project scripts can still need the network. There is no enforced Offline switch. Android Studio is not required. Builds run locally; this app does not upload projects to a build service. Project scripts can access the network. Filtering services may require download domains to be allowed.
## Import and review
Choose folder or Choose ZIP, or drag either into the drop area. The app creates a temporary working copy and checks ZIP extraction paths. Static analysis finds Gradle settings, application modules and known configuration values. Dynamic values are resolved during Build.

Module selects the application to build. Application ID identifies the installed app. Compile SDK is the Android API used to compile; Min SDK is the minimum device API. Build Tools package and sign APKs. Java runs the tools; Gradle coordinates the build. Version refers to your app.

Debug is for testing, usually with an automatic development signature. Release uses project distribution settings and may remain unsigned. Trust approval allows project scripts to run with your user permissions: a temporary directory is not a security sandbox. Start Build requests approval if needed; Back returns to import and clears the working copy.
## Signing
Enable Sign Release to use an existing keystore or create one. Choose a path, alias (key name), store password and key password. Back up the key and passwords; app updates require the same key. Passwords are not saved in preferences.
## Build process
Java, system trust certificates, Gradle and Android SDK are prepared. Missing SDK packages and dependencies are downloaded; supplier terms require consent when needed. Gradle processes resources, compiles Java/Kotlin, converts code to DEX and packages code, resources and the manifest into APKs. The app optionally signs, verifies outputs and copies them into Output with a report.

Stages and elapsed time reflect actual work. The moving bar is indeterminate, not a percentage. A quiet log can mean computation or networking. The single-use Gradle daemon message is normal; that temporary Java process exits after the build.
## Log controls
Show/hide changes visibility only. Search filters the last 5,000 lines; Errors/Warnings use keyword matching, not the actual build result. Disable Auto-scroll to read earlier output. Copy view and Save view export the filtered text with receipt timestamps; Open log file opens the full raw log. Inspect logs for project secrets before sharing.

Cancel stops the job and its processes; wait until it finishes. Try again and Back to project return to review before starting another attempt. A recognized missing SDK error is repaired once automatically; source code errors are not rewritten.
## Output and navigation
Select an APK when multiple outputs exist. Name, ID, version, variant, build type, signature status, size and path come from actual outputs. Open APK launches the associated application; Windows itself cannot install APKs. Open Output folder shows APKs and the report. Another build returns to review; New project clears the temporary copy while preserving outputs. Language switching is available when idle. Guide & help opens this guide. Credit opens the credited profile in your browser.
## Credit
Credit to Moked Hama’arachot (מוקד המערכות), Mitmachim Top forum.
'''+f'\n[Profile]({CREDIT_URL})\n'
