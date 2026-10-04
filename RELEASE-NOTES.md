## AndroidCompiler 0.2 Preview

Download **AndroidCompiler.exe** below — no manual ZIP extraction required.

### עברית

- ממשק חדש עם סרגל שלבים, כרטיסים וגווני כחול־סגול.
- כפתור קימפול מגיב גם כשטרם אושר הפרויקט: מוצג חלון אישור ברור.
- תיקון תזמון: מסך האישור מוצג רק לאחר שמשימת הייבוא הסתיימה.
- זמן שחלף והודעת המתנה לרשת/כלי, ללא אחוזי קימפול מומצאים.
- שגיאות בממשק ובתחילת העבודה מוצגות ונשמרות ביומן.

The release workflow runs regression tests on Windows and starts the actual frozen
EXE in Qt offscreen mode before publishing it. This is not a full interactive
Windows acceptance test or proof that every Android project builds successfully.
Android toolchain downloads need internet access and SDK license consent.
Only build trusted projects: Gradle scripts are not sandboxed.
The EXE is not Authenticode signed. This remains a Preview.
