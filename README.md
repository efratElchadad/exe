# AndroidCompiler 0.6 Preview

Native Android online client, Windows desktop compiler and Mac desktop cloud client. Source projects build into APK, Windows EXE or macOS DMG using the supported Android/Python/.NET engines. Cloud builds require a private GitHub repository and a classic repo/workflow token; Actions quotas and charges apply. No universal source/binary conversion.

See [Hebrew setup and limitations](README-HE.md) and [Android source build instructions](android-client/README.md). Direct installable downloads are attached to Releases.

# AndroidCompiler — Preview 0.2

Windows desktop application for building APK files from supported Android Gradle projects.

**Preview:** actual Debug and signed Release builds were tested on Linux. The Preview release workflow builds on Windows, runs regression tests and checks EXE startup before publishing. The 0.2 workflow passed all 23 tests and the frozen EXE startup check on Windows. Full interactive Windows testing remains outstanding.

[Download Windows EXE / הורדת התוכנה](https://github.com/efratElchadad/exe/releases)

## שימוש

הפעילו את AndroidCompiler.exe. הקובץ פורס בעצמו את סביבת הריצה; אין צורך לחלץ ZIP ידנית. בחרו פרויקט Android, בדקו את מסך הסיכום ואשרו Build. בהפעלה הראשונה נדרשים אינטרנט ואישור רישיונות Android.

- [מדריך מלא ומגבלות](README-HE.md)
- [דוח בדיקות](TEST-REPORT.md)
- [הפוסט למתמחים טופ](FORUM-POST-HE.md)
- [רישיונות צד ג׳](THIRD-PARTY.md)

Build scripts execute with the current user's permissions. Only build projects you trust.

![AndroidCompiler 0.2 interface](docs/ui-v2-home.png)

[Successful Windows validation](https://github.com/efratElchadad/exe/actions/runs/37206504804)
