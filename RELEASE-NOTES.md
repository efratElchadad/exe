# AndroidCompiler 0.2.1 Preview — certificate setup fix

Fixed the repeated “Certificate was added to keystore” messages during first setup.
System roots are now prepared by one Java process, with actual certificate counts,
a 120-second timeout and a verified cache. Partial files from interrupted work are
not reused. TLS certificate verification and Java security policies stay enabled.

תוקנה הכנת תעודות האבטחה האיטית: פעולה אחת במקום הפעלת Java לכל תעודה.
כעת מוצגים מספרי תעודות אמיתיים, התוצאה נשמרת לשימוש חוזר וקובץ חלקי אינו משמש
לבנייה. אין צורך למחוק את כלי Java/SDK או את הפרויקט כדי להתקין עדכון זה.

Windows regression tests include actual Java trust-store creation, cache reuse,
corruption recovery and cancellation. The frozen EXE startup is tested before
publishing. Full manual Windows and project-specific Android tests remain outstanding.
