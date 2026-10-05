# גרסה 0.6 — Windows, Mac ו־Android

**הורדה ישירה — ללא ZIP:** [Android APK](https://github.com/efratElchadad/exe/releases/download/v0.6.0-preview.14/AndroidCompiler-Android.apk) · [Windows EXE](https://github.com/efratElchadad/exe/releases/download/v0.6.0-preview.14/AndroidCompiler.exe) · [Mac Apple Silicon](https://github.com/efratElchadad/exe/releases/download/v0.6.0-preview.14/AndroidCompiler-Mac-arm64.dmg) · [Mac Intel](https://github.com/efratElchadad/exe/releases/download/v0.6.0-preview.14/AndroidCompiler-Mac-x64.dmg)

נוספה אפליקציית Android קלה שבה הבנייה מתבצעת אונליין ב־GitHub Actions. נוספו גם תוכנות Mac מוכנות ל־Apple Silicon ול־Intel. אין צורך להתקין כלי פיתוח במכשיר שעליו מפעילים את התוכנה.

| המכשיר שעליו מפעילים | אופן הבנייה | תוצרים לפי סוג המקור |
| --- | --- | --- |
| Windows | מקומית עם הורדת כלים אוטומטית, או בענן | APK, EXE, Mac DMG (Mac בענן בלבד) |
| Mac | בענן | APK, EXE, Mac DMG |
| Android 8+ | בענן בלבד | APK, EXE, Mac DMG |

**הענן דורש חשבון GitHub פעיל ואסימון classic עם repo ו־workflow.** מזינים אותו באפליקציה בלבד. הוא נשמר בזיכרון למשימה ואינו נשמר בהגדרות או נשלח לשרת הקימפול. הקוד מועלה לאחר אישור למאגר פרטי ונשאר בהיסטורייתו. מכסות ועלויות Actions חלות לפי החשבון.

אין המרה בין APK ו־EXE קיימים ואין תרגום אוטומטי בין שפות. Android Gradle מתאים ל־APK; Python או .NET נתמך מתאימים למסלולי EXE/Mac. התאמת התוכנה למערכת היעד היא באחריות קוד המקור.

**Android:** בוחרים ZIP עד 12 MiB, סוג מקור, קובץ כניסה/מודול ותיקיית יעד; מאשרים העלאה ומתחילים. ניתוח הטלפון הוא בדיקה ראשונית בלבד, והניתוח המלא בענן. ״בדוק בנייה קודמת״ מחדש מעקב/הורדה לאחר סגירה עם הזנת אסימון מחדש. יומן שלבים ניתן להצגה ולהעתקה; פלט הפקודות המלא נפתח ב־GitHub. אין מצב אופליין, ייבוא תיקייה או חתימה אישית בלקוח Android. תוצרים עד 1 GiB.

**Mac:** פותחים את ה־DMG וגוררים את AndroidCompiler לתיקיית Applications. אין עדיין חתימת Developer ID או notarization. התוצרים כוללים את אותו ממשק עברי/אנגלי של Windows, כשכל הבניות בענן.

**בנייה מקוד המקור:** להרצת לקוח שולחני: `python -m pip install -r requirements-dev.txt`, אחר כך `python packaging/prepare_assets.py` ו־`python main.py`. לאריזת Mac: התקנת Pillow ואז `python packaging/package_mac.py` על Mac. הוראות Android ב־[android-client/README.md](android-client/README.md). תהליך Windows המלא ב־[publish.yml](.github/workflows/publish.yml).

זו גרסת Preview. ה־APK של הלקוח חתום במפתח Debug; עדכון עשוי לדרוש הסרת התקנה קודמת. בדיקות מנועים וממשק אינן בדיקת חשבון GitHub פרטי מלאה עם אסימון אישי; המסלול הזה טרם נבדק מקצה לקצה. התוצרים אינם מופצים כ־ZIP.

## Windows — שימוש והגבלות
הורד AndroidCompiler.exe מלשונית Releases והפעל. בחר סוג מקור ואז גרור תיקייה/ZIP או השתמש בבחירה. במסך הבדיקה בחר מודול, סוג Build ותיקיית יעד. בנייה מתחילה רק לאחר אישור אמון בקוד, ובענן גם אישור העלאה. אין צורך לחלץ ZIP של התוכנה עצמה.

בנייה מקומית מורידה אוטומטית כלים פרטיים: JDK, Gradle ו־SDK עבור Android; Python 3.12 עם PyInstaller עבור Python; או .NET SDK נתמך. מטמון מקצר בניות חוזרות, אך אין הבטחת אופליין. נדרש Windows 10/11 x64. קובץ התוכנה אינו חתום בתעודת Authenticode מסחרית.

לוג מקומי כולל חיפוש, סינון, העתקה, שמירה וגלילה אוטומטית. בענן מוצגים שלבי GitHub וקישור ללוג המלא. אין אחוזי התקדמות מומצאים. ״פתח תוצר״ מפעיל את שיוך הקובץ במערכת; Windows אינו מריץ APK או DMG.

## אילו פרויקטים נתמכים?
- Android: פרויקט Gradle עם settings, מודול אפליקציה ו־gradle-wrapper.properties. ערכים דינמיים עשויים להיות לא ידועים לפני Build. Flutter ו־React Native אינם מוכנים אוטומטית ללא הכלים הייחודיים להם.
- Python: קובץ py ראשי או spec של PyInstaller; requirements.txt ותצורת התקנת פרויקט נתמכים בשורש. קובצי משאבים וייבוא דינמי עשויים לדרוש spec. Windows Python הפרטי אינו כולל Tkinter או קומפיילר C. spec ל־Mac צריך להגדיר BUNDLE.
- .NET: פרויקט SDK עם יעד יחיד net8.0/net9.0/net10.0. ב־Windows נתמכת גם סיומת windows; ב־Mac אינה נתמכת. Framework ישן, MAUI, workloads מיוחדים ו־NativeAOT אינם נתמכים אוטומטית. ב־Mac בענן זמינים SDK עדכניים מסדרות 8/9/10; global.json שנועל SDK אחר עלול להכשיל בנייה.

## שמירה, פרטיות ואנרגיה
המקור נשמר במאגר GitHub פרטי. התוצרים בענן נשמרים שבעה ימים; עותק שהורד לתיקייה הנבחרת נשאר במכשיר. מחיקת ענף אינה מבטיחה מחיקת המקור מהיסטוריית Git — יש למחוק את המאגר ב־GitHub כשאין בו צורך.

באנדרואיד יש העלאה, מעקב אחת ל־15 שניות והורדה. אין קומפיילר מקומי ואין נעילת מעבד. בזמן המעקב מוצגת התראה; חסכון סוללה או סגירת האפליקציה יכולים לעצור את המעקב, אך משימת הענן עשויה להמשיך. השימוש עדיין צורך נתונים וסוללה, במיוחד בפרויקטים גדולים. לא נמדדה צריכת אנרגיה על מכשיר פיזי.

## בדיקות וקרדיט
ראוי לקרוא את [דוח הבדיקות](TEST-REPORT.md) ואת [מגבלות הגרסה](RELEASE-NOTES.md). הקוד המקורי לא שונה במהלך בנייה רגילה; סביבת עבודה זמנית אינה Sandbox להרצת קוד לא מהימן.

קרדיט ל[מוקד המערכות מפורום מתמחים טופ](https://mitmachim.top/user/%D7%9E%D7%95%D7%A7%D7%93-%D7%94%D7%9E%D7%A2%D7%A8%D7%9B%D7%95%D7%AA).
