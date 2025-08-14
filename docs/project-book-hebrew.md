# ספר פרויקט: Website AI Assistance (WAS) & Agentic Chatbot

הערה על דגש: ספר זה מתמקד בעיקר ב־Website AI Assistant (≈75%) ומשתמש ב־Agentic Chatbot כעוזר תומך (≤25%). התוכן מבוסס על קוד הבסיס הנוכחי, לא על מסמכי legacy.

## תוכן עניינים

1. מבוא
2. רקע תיאורטי / מושגי יסוד
3. מצב קיים נוכחי / State of the Art
4. מפרט ועיצוב (כולל כלי פיתוח)
5. תרחישים (Use Cases / User Stories, תהליכי מערכת)
6. מימוש ותוצאות והערכה
7. פרטים טכניים (מודלים, נתונים, שיטות)
8. סיכום והרחבות עתידיות
9. ביבליוגרפיה / מקורות
10. נספחים

## 1. מבוא

מטרה ומוטיבציה
- אנו בונים עוזר אתר כולל כדי שאנשים יוכלו לתקשר עם כל אתר בשפה אנושית רגילה - טקסט או קול - בשפה שלהם.
- המוטיבציה היא מעשית ואנושית: משתמשים רבים נאבקים עם חסמי חינוך, שפה, אוריינות טכנית או נגישות, במיוחד בשירותים חיוניים (ממשלה, בריאות, כספים). ראינו את המאבקים הללו במו עינינו ועיצבנו את המערכת כדי להסיר אותם.

מה זה עושה
- משתמשים מדברים עם האתר באמצעות widget של chatbot (טקסט או קול). הם שואלים שאלות בשפתם; העוזר עונה באותה שפה.
- התשובות מבוססות על תוכן האתר עצמו באמצעות Retrieval‑Augmented Generation (RAG), מקטין הזיות ושומר על תגובות מדויקות ועדכניות.
- מצב קולי תומך בדיבור נכנס/יוצא לאלה שלא יכולים (או מעדיפים לא) להקליד.
- סיכום: משתמשים יכולים להדביק URL או טקסט גולמי כדי לקבל סיכום תמציתי בשפה שלהם.
- ניתוח צילום מסך: משתמשים יכולים להעלות צילום מסך של דף כדי לחלץ ולהסביר תוכן על המסך.

למי זה עוזר
- משתמשים לא-טכניים ואנשים עם רקע חינוכי נמוך יותר שצריכים תשובות ברורות וישירות.
- משתמשים שמתמודדים עם חסמי שפה; העוזר משקף את שפת המשתמש ללא קשר ל-locale של האתר.
- אנשים עם צרכי נגישות (למשל, ליקויים מוטוריים) שמרוויחים מאינטראקציה קול-ראשון.
- משתמשי כוח ומפתחים באתרי תיעוד עתירי-נתונים: העוזר מצביע על קטעים רלוונטיים, מסביר מושגים ומזרז הכשרה ופתרון בעיות.

למה זה עוזר לבעלי אתרים
- הגעה לאנשים נוספים על ידי פגישה איתם היכן שהם נמצאים - שפה, קול ורמת מומחיות.
- הפחתת עומס תמיכה עם תשובות מדויקות לשירות עצמי הקשורות לתוכן שלך.
- מתן חוויה עקבית ואמינה; תשובות RAG מבוססות על האתר שלך, לא על ידע כללי מהאינטרנט.

שני יישומים קשורים ב-repo הזה
- ראשי: Website AI Assistance (WAS), רב-שוכר, chatbot RAG מבוסס-קוד ו-widget הניתן להטמעה.
- משני (demo): עוזר קניות agentic קול-ראשון שמשתמש ב-tool/function calling לחיפוש מוצרים, הוספה לעגלה והשלמת checkout. הוא עדיין לא משולב ב-WAS; זרימת ה-demo הנוכחית היא באנגלית בלבד עם מפת דרכים לקול רב-לשוני.

תמונות מוצעות לסעיף הזה:
- Widget עונה על שאלה באתר לדוגמה (UI של טקסט).
- קטע מצב קולי (מיקרופון פועל, transcript זורם, תגובה מדוברת).
- לוח בקרה של admin: יצירת chatbot + הוספת מקורות.

## 2. רקע תיאורטי

סעיף זה מתאר את המושגים הבסיסיים שעליהם מתבססות שתי המערכות, מיושרים עם איך שהן מיושמות בקוד.

### 2.1 Retrieval-Augmented Generation (RAG)

- Ingestion & Indexing: תוכן מקור (דפי אינטרנט, PDFים, DOCX, טקסט) נותח, מנוקה, מחולק לחתיכות ונשמר. כל חתיכה מומרת לוקטור צפוף באמצעות Google's Generative AI embeddings (google.genai, למשל, מודל "gemini-embedding-001"). טקסטים גולמיים של חתיכות נשמרים ב-Google Cloud Storage (GCS), והוקטורים מועלים ל-Vertex AI Matching Engine. מזהי וקטור מקודדים chatbot_id וזהות מקור כדי לאפשר בידוד קפדני לכל chatbot בזמן שאילתה.
- Retrieval: בזמן שאילתה, השאלה של המשתמש מוטמעת באמצעות google.genai EmbedContent API ומחפשים אותה מול אינדקס Matching Engine באמצעות מסנן namespace על chatbot_id (באמצעות aiplatform.matching_engine.Namespace). מזהי החתיכות המובילים מוחזרים והטקסטים הגולמיים שלהם נאספים מ-GCS.
- Reranking: החתיכות שנאספו מדורגות מחדש באופן אופציונלי על ידי RankingService כדי לשפר סדר ההקשר ל-LLM.
- Generation: נבנה prompt שכולל הוראות (דבקות בידע וקפדני "תענה בשפת המשתמש"), היסטוריית הצ'אט מתוקצבת למגבלת תווים, וחלקי ההקשר הנבחרים. Vertex AI GenerativeModel (משפחת Gemini) יוצר את התשובה הסופית עם הגדרות בטיחות (קטגוריות נזק וספים). הקשר קולי/תמונה יכול להיכלל כשזה מופעל.

למה זה חשוב: RAG שומר על תשובות מבוססות על תוכן האתר, מקטין הזיות ומאפשר עדכונים מבלי לאמן מחדש LLM.

### 2.2 Agentic AI ו-Tool Use

העוזר הסוכנני משתמש בדפוס "LLM + כלים". ה-LLM מתכנן איזה כלי להשתמש, מחלץ פרמטרים מהשיחה, קורא לכלי (HTTP/API או פונקציית Python), צופה בתוצאה ומסנתז תגובה סופית.

Retail demo (נפרד מ-WAS, עדיין לא משולב):
- קטלוג מוצרים נוצר על ידי בעל האתר ומועלה ל-Google Cloud Retail API; וקטורי מוצרים מוגשים באמצעות Google's Matching Engine.
- המשתמש יכול לתפעל את כל זרימת הקניות בקול: חיפוש מוצרים, בדיקת פרטים, הוספה לעגלה והמשך ל-checkout.
- מצב נוכחי: demo באנגלית בלבד; קול רב-לשוני במפת הדרכים כדי שקונים יוכלו לגלוש ולקנות בשפה שלהם מבלי להקליד או לדעת את ה-locale של האתר.
- הסוכן קורא לכלים מוגדרים היטב: list_products, get_product, add_to_cart, remove_from_cart, view_cart, checkout, וזיהוי תמונה אופציונלי.

### 2.3 יסודות ארכיטקטורת המערכת

- Client-Server: frontend מנותק (React admin ו-widget JS הניתן להטמעה) מתקשר עם backend של Flask באמצעות HTTP APIs מאובטחים לכל chatbot עם מפתח API (Bearer).
- Data & Infra: מודלי SQLAlchemy גובים DB יחסי (SQLite ב-dev), טקסטים של חתיכות חיים ב-GCS, וקטורים חיים ב-Vertex AI Matching Engine, ו-LLM/Embeddings מוגשים באמצעות Vertex AI/Google GenAI SDKs. עבודות ארוכות טווח (ingestion, cleanup) רצות ב-Celery workers. Redis גובה Server-Sent Events (SSE) לזרימת סטטוס.
- Multimodal/Voice: נקודות קצה STT→RAG→TTS אופציונליות מאפשרות חוויות קוליות; קלט תמונה יכול לזרוע או לעדן שאילתה.

דיאגרמות מוצעות לסעיף זה:
- סכמת צינור RAG (Ingestion → Index → Retrieve → Re-rank → Generate).
- מפת מיקום נתונים (DB לעומת GCS לעומת Matching Engine) עם קונבנציות מזהה וקטור/נתיב GCS.

## 3. מצב קיים נוכחי / State of the Art

סעיף זה מסכם את הנוף התחרותי. ההתמקדות היא על איך ה-WAS המוצע מתיישר עם או שונה מפתרונות אחרים ביכולות מפתח.


//////////////////////////////////////////////////////////////////////מקום לתמונה: הכנס את תמונת מטריצת ההשוואה שלך כאן.

### תמונות מצב של מתחרים (2–3 משפטים כל אחד)

1) WebAssistants.ai — עוזרי AI לאפליקציות ולוחות בקרה של אינטרנט
- מה זה: widget JavaScript plug-and-play להוספת עוזרי AI לאפליקציות/לוחות בקרה קיימים של אינטרנט עם "שורת קוד אחת", המציע עוזרים הניתנים להתאמה אישית, קריאות פונקציות, חיפוש אינטרנט אופציונלי ותמיכה רב-לשונית.
- השוואה: מותאם לסיוע באפליקציה ופרשנות נתונים בתוך לוחות בקרה בבעלות. ה-WAS שלנו הוא RAG מבוסס על כל תוכן האתר עם בידוד קפדני לכל שוכר, מצב קולי, סיכום URL/טקסט וניתוח צילום מסך; שימוש agentic tool קיים כ-demo נפרד, לא ברירת המחדל הבסיסית.

2) A‑Eye Web Chat Assistant (הרחבת Chrome)
- מה זה: עוזר נגישות דפדפן שמנתח את הדף/צילום המסך הנוכחי, מסכם תוכן ומאפשר ניווט קולי; רץ עם מודלים מקומיים (Gemini Nano, Ollama, LM Studio, vLLM) או ענן (Gemini, Mistral) לפרטיות/שליטה.
- השוואה: מטרגט משתמשי קצה בדפדפן שלהם, לא בעלי אתרים; הלוגיקה רצה בצד לקוח והיא הקשרית לדף. WAS הוא שירות מוטמע-אתר, רב-שוכר שעונה בקפדנות מהידע המאוכלס של האתר עם RAG בצד השרת, בקרות שוכר וקונסולת admin.

3) Salesloft Drift — צ'אט AI לצנרת ותזמור הכנסות
- מה זה: שיחת שיווק/מכירות לכידת enterprise שמציעה שיחות מותאמות אישית, מכשיר לידים, הופך מבקרים לא-אנונימיים, מנתב לנציגים ומתחבר לפלטפורמת ההכנסות של Salesloft (Rhythm, Deals, Analytics, Forecast).
- השוואה: ממוקד על יצירת דרישה ותזמור מכירות (ניקוד לידים, ניתוב, ייחוס). WAS מתמקד בעזרה מדויקת, רב-לשונית, ידידותית-נגישות מבוססת על תוכן האתר; הוא לא הופך מבקרים לא-אנונימיים או מנהל צינור כברירת מחדל, ומתעדף ביסוס תוכן וכוללות קולית על פני ops מכירות.

## 4. מפרט ועיצוב (אפיון ועיצוב)

### 4.1 מטרות מערכת ודרישות פונקציונליות

WAS (ראשי):
- chatbots רב-שוכר לכל חשבון; כל chatbot יש לו מפתח API ייחודי וקונפיגורציה.
- מקורות: הוסף URLs של אתרים והעלה קבצים (.txt, .pdf, .docx); ingestion הוא אסינכרוני.
- צ'אט RAG: תענה בקפדנות מהתוכן המסופק; אכוף התאמת שפה לשאילתת המשתמש; שאלות ותשובות מותנות-תמונה אופציונליות.
- Widget: תגית script הניתנת להטמעה עם צבעים הניתנים להתאמה אישית, avatar/לוגו, טקסט launcher, אינדיקטור הקלדה, toggle התחלה-פתוח, הודעת הסכמה (Authorization: Bearer <api_key> נשלח על קריאות widget).
- Admin: צור/עדכן/מחק chatbots; נהל מקורות; הצג סטטוס ingestion באמצעות SSE; יצר מחדש מפתח API.
- משוב/היסטוריה: נקודות קצה thumbs ומשוב מפורט (אם מופעל); התמדה של היסטוריה אופציונלית לכל chatbot עם מדיניות retention.
- קול: נקודות קצה STT ו-TTS אופציונליות; toggle VAD.
- סיכום: סכם דף אינטרנט לפי URL או סכם טקסט מודבק; החזר את הסיכום בשפת המשתמש.
- ניתוח צילום מסך: קבל תמונה של דף; חלץ טקסט ואלמנטים כדי לענות או לסכם מה שעל המסך.

- RAG מתקדם: feature flag לכל chatbot; מצב סטנדרטי הוא ברירת המחדל. הערה: צינור RAG ניסיוני מתקדם היה פחות יעיל בבנצ'מרקים שלנו עבור הפריסה הזאת, אז מצב סטנדרטי נשאר מומלץ.

Agentic chatbot (משני):
- השתמש בקריאות כלים כדי לבצע משימות מוצר/עגלה וסימולציית checkout פשוטה.
- כלי זיהוי-תמונה אופציונלי להתאמת מוצרים; חיפוש קמעוני חיצוני אופציונלי.
- שמור על מיקוד מוגבל; אין פעולות אוטונומיות רחבות מעבר לכלים מוגדרים.

Non-functional:
- בידוד: סינון namespace לכל chatbot בחיפוש וקטורי; ראה 4.6 לפרטים על מזהי וקטור ופריסת אחסון.
- ביצועים: ingestion ברקע, fetch GCS בו-זמנית ו-reranking עם תקציבי prompt/היסטוריה/הקשר; ראה 4.7 למטרות והתנהגות.
- בטיחות ואימות: הגדרות בטיחות LLM, דבקות ידע קפדנית, בדיקות קובץ/קלט וגבלת קצב; ראה 4.6 למודל מלא ובקרות.

### 4.2 ארכיטקטורה ברמה גבוהה

רכיבים:
- Clients: אפליקציית React admin; widget JS הניתן להטמעה.
- Backend: Flask API עם Blueprints; RagService (execute_pipeline, multimodal), Ingestion; נתיבי Voice; SSE על Redis לסטטוס.
- Workers: Celery למשימות ingestion, discovery/crawl ו-deletion/cleanup.
- Data & AI: SQLite (dev) באמצעות SQLAlchemy; GCS לטקסט חתיכות; Vertex AI Matching Engine לוקטורים; google.genai ל-embeddings; Vertex AI GenerativeModel ל-LLM.

דיאגרמת ארכיטקטורה מומלצת (הכנס כאן):

הערה: ה-Discovery Engine reranker הוא אופציונלי ויש לו fallback חלק לסדר הretrieval המקורי כשלא זמין או נכשל.

### 4.3 מפרט כלי Agent (עוזר)

טווח: demo בלבד; לא משולב בזרימת WAS RAG עדיין. קריאות כלים מוגבלות לנקודות קצה/כלים מוצהרים; אין גלישה אוטונומית בתוך WAS.

דוגמאות מבוססות על נקודות קצה וכלים של demo הסוכן:
- list_products(): מחזיר סיכומי מוצרים. קלטים: none | מסננים.
- get_product(product_id): מחזיר פרטי מוצר. קלטים: product_id.
- add_to_cart(user_id, product_id, quantity): מוסיף או מעדכן פריט. קלטים: user_id, product_id, quantity.
- remove_from_cart(user_id, product_id): מסיר פריט. קלטים: user_id, product_id.
- view_cart(user_id): מחזיר פריטי עגלה וסכומים. קלטים: user_id.
- checkout(user_id): מדמה יצירת הזמנה; מחזיר אישור. קלטים: user_id.
- identify_image(image): מסווג/מזהה פריטים בתמונה; עשוי להחזיר מוצרים מועמדים. קלטים: תמונת base64 או URL.

עבור כל כלי, ה-LLM אחראי לבחירת הכלי, חילוץ פרמטרים מהשיחה ושילוב פלטי כלים בתגובה שלו.

### 4.4 כלי פיתוח ו-stack

- Backend: Python, Flask, SQLAlchemy, Alembic (migrations), Celery.
- Frontend: React SPA ל-admin; vanilla JS widget להטמעה.
- Infra & AI: Google Cloud (Vertex AI GenerativeModel, Vertex AI Matching Engine), google-genai SDK ל-embeddings, Google Cloud Storage, Redis (SSE), SQLite (dev).
- בדיקות ו-Ops: גבלת קצב, אימות בקשות, auth מפתח-API לכל chatbot; לוגים ומטריקות שימוש באמצעות UsageLog.

הפניה צולבת: עבור נקודות קצה API מלאות וסכמות בקשה/תגובה, ראה נספח B.

///////////////////////////////////////////////////////////////////////////////////////////////////תמונות מוצעות לסעיף זה:
- דיאגרמת ארכיטקטורה (למעלה) מיוצאת כ-PNG לספר.
- דיאגרמת רצף ל-ingestion ו-RAG.

### 4.5 פילוסופיית עיצוב UI/UX

לוח בקרה Admin (React):
- תעדוף בהירות ושליטה: יצירת chatbot בלחיצה אחת; נראות inline לתוך סטטוס ingestion באמצעות SSE; toggles פשוטים לתכונות (קול, ניתוח תמונה, שמירת היסטוריה, משוב).
- ברירות מחדל בטוחות: דבקות ידע קפדנית מופעלת כברירת מחדל; היסטוריה מבוטלת כברירת מחדל כשנדרשת פרטיות; מגבלות קצב שמרניות מיושמות בצד השרת.

- UX של שגיאה: הצג הודעות אימות backend (למשל, שגיאות סוג/גודל קובץ) וסטטוסי משימות; ספק קטע embed העתקה-הדבקה עם chatbot_id ו-placeholder מפתח API מוכנס אוטומטית.

Widget הניתן להטמעה (vanilla JS):
- טביעת רגל מינימלית: נטען באופן עצל, נצמד לפינת דף, לא-חודרני כברירת מחדל; start-open אופציונלי לעיסוק פרואקטיבי.
- בהירות שיחה: בועות הודעה ברורות, timestamps (אופציונליים), אינדיקטור הקלדה והודעת הסכמה כשנדרש.
- בינאומיות: תשובות משקפות בקפדנות את שפת שאילתת המשתמש; UI קולי מציג מצב הקלטה והתנהגות VAD כשמופעל.
- עמידות: מציג הודעת fallback ידידותית אם השרת מחזיר שגיאה או מערכת הבטיחות חוסמת תגובה.

נגישות (כוללת כברירת מחדל):
- ניווט מקלדת לכל האלמנטים האינטראקטיביים; מצבי פוקוס נראים.
- תוויות קורא-מסך לבקרות (פתח/סגור, התחל/עצור מיקרופון, שלח) ואזורי ARIA live לתגובות זורמות.
- תאימות עם ערכת נושא בניגודיות גבוהה וגדלי גופן הניתנים להקשה; טקסט alt לתמונות ו-avatars.
- נתיב קול-בלבד למשתמשים שלא יכולים להקליד; כתוביות/transcripts מוצגים לצד TTS כשזמין.

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////חזותיים מוצעים: שני wireframes קלים—(1) טופס admin "צור Chatbot" עם קלטי מקור ו-toggles, (2) widget במצבים סגור ופתוח עם מיתוג.

### 4.6 מודל אבטחה ובידוד נתונים

AuthN/AuthZ:
- מפתח API לכל chatbot נדרש לנקודות קצה widget; מפתחות מוצפנים בבטחה במנוחה (check_password_hash) ומתקבלים באמצעות Authorization: Bearer <key>.
- בדיקות בעלות על נקודות קצה ניהול באמצעות client_id; מגבלות קצב מיושמות (למשל, כניסה, יצירה, עדכון, widget-config) באמצעות limiter.
- מפתח API לכל chatbot נשמר מוצפן ומאומת בכל קריאת widget באמצעות כותרת Authorization: Bearer.

בידוד נתונים:
- בידוד קשיח בזמן retrieval באמצעות סינון Vertex AI Matching Engine Namespace לפי chatbot_id.
- מזהי וקטור דטרמיניסטיים מקודדים chatbot ומקור: chatbot_{chatbot_id}_source_{hash}_chunk_{index}. נתיבי blob GCS משקפים את הפריסה הזאת: chatbot_{id}/source_{hash}/{index}.txt.
- נתיב ה-RAG מאמת את הקידומת vector_id's chatbot_{id} לפני ניסיון כל fetch GCS.

אימות קלט:
- העלאות קבצים מוגבלות לפי סיומת וגודל למקורות נתונים; מגבלות קפדניות יותר נפרדות ללוגו/.
- העלאות תמונה מאומתות לסוג; קלטים לא מהימנים אף פעם לא מבוצעים.

תעבורה ו-CORS:
- CORS מופעל לשימוש widget ו-admin; ברירות מחדל מתירניות ב-dev; הדק origins מותרים בייצור (מתירני ב-dev; הגבל ב-prod).

בטיחות:
- הגדרות בטיחות LLM חוסמות הטרדה, שנאה, מפורש ותוכן מסוכן; finish reasons לא-STOP מוצגים כהודעות ידידותיות למשתמש.
- רמות דבקות ידע ניתנות להקשה (strict/moderate/flexible) ונאכפות בבניית prompt.

PII והסכמה:
- פרטיות קולית: אודיו מעובד זמנית ל-STT/TTS כברירת מחדל; אין אודיו גולמי נשמר אלא אם מופעל במפורש בהגדרות admin ומוגלה למשתמשי קצה.

### 4.7 מאפיינים תפעוליים וביצועים

SLOs (מטרות, ניתנות להתאמה):
- תגובת צ'אט P50 < 2.5s, P95 < 6s לשאילתות טקסט-בלבד בגדלי הקשר בינוניים.
- זמן ingestion תלוי בגודל האתר; משוב זורם באמצעות SSE עם מצבים (Queued, Updating, Active, Pending Deletion, Empty) אבל מהיר יחסית.

תפוקה ובו-זמניות:
- Celery workers מטפלים במשימות ingestion/discovery/deletion; בו-זמניות מוגדרת ל-CPU ו-I/O; נתיב retrieval תומך ב-fetches GCS בו-זמניים וחיפושי שכנים ניתנים להקבלה. במצב סטנדרטי נעשה שימוש בוריאציית שאילתה יחידה; מצבים מתקדמים עשויים להוסיף וריאציות (ניסיוני בפריסה זו ונמצא פחות יעיל בבנצ'מרקים).

נסיונות חוזרים וbackoff:
- משימות רקע משתמשות בנסיונות חוזרים עם backoff/jitter; שגיאות GCP/HTTP זמניות לא חוסמות את ה-API; תוצאות חלקיות מתדרדרות בחן.

תקציבי Prompt/הקשר:
- מקסימום תווי היסטוריה ואורך הקשר חסומים; reranking מקטין tokens מבוזבזים; שימוש בtoken מתועד ב-metadata כשזמין.

### 4.8 מחזור חיי נתונים ומחיקה

Ingestion:
- מקורות (URLs/קבצים) נותחים, מחולקים לחתיכות, מוטמעים ו-upserted; VectorIdMapping מקשר כל וקטור למקור שלו.

עדכון:
- משימות re-ingestion רצות כשמקורות משתנים; וקטורים מיושנים מזוהים ומוסרים; סטטוס chatbot משקף התקדמות באמצעות SSE.

מחיקה:
- מחיקה לכל מקור מסירה וקטורים מ-Matching Engine ומיפויים מ-DB; ניקוי chatbot מלא מנקה וקטורים/מיפויים, הודעות צ'אט ולוגים של שימוש; מאפס סטטוס chatbot ל-Empty.
- מחיקה לכל מקור במפורש ממפה vector_ids באמצעות VectorIdMapping, מסירה את נקודות הנתונים האלה ב-Matching Engine, ואז מנקה מיפויי DB מתאימים.

פריסת אחסון:
- GCS: chatbot_{id}/source_{hash}/{index}.txt; DB: Chatbot, User, ChatMessage, DetailedFeedback, UsageLog, VectorIdMapping.

### 4.9 קונפיגורציה וסביבה

קונפיגורציה בסיסית (env/app config):
- PROJECT_ID, REGION, BUCKET_NAME, INDEX_ENDPOINT_ID, DEPLOYED_INDEX_ID.
- EMBEDDING_MODEL_NAME (למשל, gemini‑embedding‑001), GENERATION_MODEL_NAME (למשל, gemini‑2.5‑flash‑preview‑04‑17), טמפרטורת יצירה ומקסימום tokens.
- RAG_TOP_K, M_FUSED_CHUNKS, MAX_CONTEXT_CHARS, MAX_HISTORY_CHARS.
- GOOGLE_CLOUD_PROJECT ו-GOOGLE_CLOUD_LOCATION מוגדרים פרוגרמטית כדי ליישר SDKs ב-workers; workers גם דורשים GOOGLE_GENAI_USE_VERTEXAI=True כדי ש-google.genai יכוון ל-Vertex AI.

סודות:
- מפתחות API מוצפנים במנוחה; אישורי GCP מסופקים באמצעות מנגנוני סביבה סטנדרטיים; לעולם לא לבצע commit סודות.

סביבות:
- Dev: SQLite; CORS מתירני; מגבלות קצב רפויות.
- Prod: העדף Postgres מנוהל (או Cloud SQL), CORS מוגבל, מגבלות קפדניות יותר, מספר Celery workers ו-health probes.

### 4.10 ניתור וטלמטריה

לוגים מובנים:
- כל בקשה מקבלת request_id; זמנים מתועדים לכל שלב (embeddings, retrieval, fetch, rerank, generation).

לוגי שימוש:
- UsageLog שומר פרטי פעולה (שאילתה, קטעי תגובה, מקורות, duration_ms, status_code, ספירות token כשזמין, שגיאות, request_id) לביקורות וניתוח איכות.

מטה-נתוני LLM:
- Finish reason ו-safety_ratings כלולים במטה-נתוני התגובה כשזמין מ-API המודל.

### 4.11 סיכונים והתמתנות

- סירובי מודל/חסימות בטיחות: הצג fallbacks מועילים; אפשר thumbs/משוב מפורט כדי ללמוד מצבי כישלון.
- הזיות: דבקות ידע קפדנית עם הוראה מפורשת "תגיד שאני לא יודע"; הקשר שנאסף בלבד.
- זיקי latency: fetch GCS בו-זמני, תקציב reranking, בידוד משימות רקע; חימומי cache כשיפור אופציונלי.
- מגבלות קוטה: backoff אקספוננציאלי; הידרדר לפחות שכנים או הקשר קטן יותר כשצריך.
- דליפת נתונים: סינון namespace ואימות מזהה וקטור מבטיחים בידוד בין chatbots; לעולם לא לערבב הקשרים בין שוכרים.
- טיפול שגוי באישורים: שמור רק מפתחות API מוצפנים; סובב באמצעות נקודת קצה regenerate-key.
- כישלונות reranker: אם ה-reranker נכשל או לא זמין, המערכת משמרת את סדר ה-retrieval המקורי כ-fallback.

## 5. תרחישים (Use Cases, User Stories, תהליכי מערכת)

### 5.1 User Stories — WAS (ראשי)

- כלקוח פוטנציאלי, אני רוצה לשאול שאלות ספציפיות ל-chatbot על תכונות של מוצר כדי שאוכל לקבל החלטה מבלי לקרוא דפים ארוכים.
- כמשתמש חדש, אני רוצה לשאול "איך אני מאפס את הסיסמה שלי?" ולקבל תשובה מיידית ומדויקת מבוססת על המסמכים של האתר.
- כבעל עסק, אני רוצה להוסיף דפי אינטרנט ומסמכים כדי שה-chatbot יוכל לענות על שאלות נפוצות ולהקטין את עומס התמיכה שלי.
- כמנהל תמיכה, אני רוצה נראות לתוך שאלות שנשאלות כדי שאוכל לשפר את תוכן האתר.
- כדובר לא-אנגלי, אני רוצה תשובות בשפה שלי כדי שאוכל להבין מבלי לעבור locales (הבוט משקף את שפת השאילתה).
- כadmin, אני רוצה לייצר מחדש את מפתח ה-API ולהעתיק את קטע embed ה-widget כדי לפרוס במהירות את ה-chatbot.
- כשוכר רגיש-פרטיות, אני רוצה לבטל היסטוריה ולהפעיל שער הסכמה ב-widget.
- כadmin, אני רוצה למחוק מקור ספציפי או את כל ה-chatbot ולראות עדכוני סטטוס באמצעות SSE.
- כמשתמש נייד, אני רוצה להעלות תמונה עם השאלה שלי כדי שהבוט יוכל להשתמש בה כדי לזרוע או לעדן retrieval.
- כמשתמש, אני רוצה להדביק URL ולקבל סיכום תמציתי של הדף הזה בשפה שלי.
- כמשתמש, אני רוצה להדביק טקסט גולמי ולקבל סיכום תמציתי בשפה שלי.
- כמשתמש, אני רוצה להעלות צילום מסך של דף ושהעוזר ינתח ויסביר את התוכן.
- כמשתמש עם ליקויים מוטוריים, אני רוצה להשתמש במצב קולי מקצה לקצה מבלי להקליד כדי שאוכל לנווט ולקבל תשובות ידיים-חופשיות.
- כמפתח בפלטפורמה עתירת-תיעוד, אני רוצה שהעוזר יפרש מסמכים מורכבים וינחה אותי לצעדים או APIs מדויקים.

### 5.2 User Stories — עוזר Agentic (משני)

- כלקוח שמנסה לקנות, אני רוצה שהסוכן יעזור עם פעולות עגלה ו-checkout.
- כמשתמש שמפתר בעיות, אני רוצה הוראות מונחות רב-שלביות מבוססות על התגובות שלי.
- כקונה, אני רוצה לגלוש ולהשלים checkout באמצעות אינטראקציה קול-בלבד.

### 5.3 תהליך מערכת — מענה על שאלה עם WAS

1) Widget שולח POST ל-backend עם chatbot_id ומפתח API (Bearer) בתוספת השאלה של המשתמש והיסטוריה.
2) Backend (RagService.execute_pipeline):
    - מטמיע את השאילתה באמצעות google.genai models.embed_content (task_type=RETRIEVAL_QUERY).
    - מחפש ב-Vertex AI Matching Engine שכנים הכי קרובים, מסונן לפי Namespace chatbot_id כדי לבודד נתונים.
    - אוסף את הטקסטים הגולמיים של החתיכות מ-GCS באמצעות קונבנציית מזהה וקטור → נתיב GCS.
    - עבור מתקדם מדרג מחדש את הטקסטים באמצעות RankingService וממפה מזהי וקטור חזרה למזהי המקור שלהם. אם ה-reranker מבוטל או לא זמין, המערכת משמרת את סדר ה-retrieval המקורי.
    - בונה prompt עם דבקות ידע וכלל קפדני "תענה בשפת השאילתה", מתקצב היסטוריית צ'אט וכולל חלקי הקשר.
    - קורא ל-Gemini (Vertex AI GenerativeModel) עם הגדרות בטיחות כדי לייצר את התשובה.
3) API מחזיר את התשובה, המקורות והמטה-נתונים; ה-widget מרנדר את התגובה.

הערות:
- אם ניתוח תמונה מופעל ותמונה סופקה, המערכת קודם חולצת טקסט/תיאור מהתמונה כדי לזרוע את השאילתה.
- שגיאות/אזהרות ושימוש בtoken מתועדים לטבלת UsageLog לטלמטריה; finish_reason ו-safety_ratings כלולים במטה-נתונים כשמסופק על ידי המודל.
- אם לא נמצא הקשר רלוונטי (או דבקות ידע קפדנית ושום דבר לא מתאים), העוזר עונה שהוא לא יודע במקום לנחש.
- RAG מתקדם יכול להיות מופעל/מבוטל לכל chatbot או לכל בקשה (use_advanced_rag), אבל מצב סטנדרטי הוא ברירת המחדל. בפריסה זו, הצינור הניסיוני המתקדם ביצע נמוך יותר לעומת סטנדרטי בבנצ'מרקים.

### 5.4 תהליך מערכת — אינטראקציה קולית (אופציונלית)

1) Frontend שולח אודיו לנקודת הקצה קולית; backend מבצע STT.
2) הטקסט המזוהה זורם דרך אותו צינור RAG כמו למעלה.
3) התשובה הטקסטואלית הסופית מומרת ל-TTS ומוחזרת לצד הטקסט.

/////////////////////////////////////////////////////////////////////////////////////////////////תמונות/דיאגרמות מוצעות לסעיף זה:
- דיאגרמת רצף של נתיב שאילתת RAG (Widget → API → Embeddings → Matching Engine → GCS → Rerank → Gemini → Widget).
- קליפ קצר או צילום מסך של בקשה/תגובה קולית.

## 6. מימוש ותוצאות והערכה (מימוש; תוצאות והערכה)

### 6.1 פריסת Backend (נבחר)

- Flask API: נתיבים, decorators של auth וחיווט שירותים חיים תחת אפליקציית ה-backend. יחידות בולטות:
    - נתיבי REST (כניסה, CRUD של chatbot, widget-config, triggers של ingestion/crawl, משוב, זרימת סטטוס SSE).
    - שומר מפתח API לנקודות קצה widget באמצעות decorator שקורא Authorization: Bearer <key> ובודק את המפתח המוצפן.
    - גישה singleton לשירות RAG כדי לעשות שימוש חוזר ב-clients מאותחלים (Vertex AI, google.genai, GCS, Redis, DB session).
    - כלי SSE מפרסמים עדכוני סטטוס ל-Redis על ערוץ כמו "chatbot-status-updates", כולל chatbot_id ו-client_id לסינון צד-לקוח.
- שירות RAG: מתזמר embed → retrieve → fetch → //rerank → prompt → generate, בתוספת עוזרי multimodal וניקוי.
- Celery workers: מבצעים משימות ingestion, discovery/crawl ו-deletion; מדווחים התקדמות שה-API חושף באמצעות SSE.
- אחסון: טקסטים של חתיכות ב-GCS; וקטורים ב-Vertex AI Matching Engine; נתונים יחסיים באמצעות SQLAlchemy (SQLite ב-dev).

### 6.2 פנימיות צינור RAG

- נקודת כניסה: RagService.execute_pipeline(request). אחריויות:
    - ייצר embeddings עבור שאילתת המשתמש (google.genai EmbedContent, task_type=RETRIEVAL_QUERY).
    - אחזר שכנים מ-Matching Engine באמצעות סינון Namespace על chatbot_id לבידוד קפדני.
    - אסוף טקסטים גולמיים של חתיכות מ-GCS באמצעות קונבנציית vector_id → נתיב blob, אחרי אימות שהקידומת vector_id מתאימה ל-namespace chatbot_{id}.
    - //דרג מחדש עם RankingService (Discovery Engine semantic-ranker-default-004) כדי לדחוס את חלון ההקשר ולשפר סדר; בשגיאה/חוסר זמינות, שמור את סדר ה-retrieval המקורי.
    - בנה את ה-prompt: כלול רמת דבקות ידע, קפדני "תענה בשפת המשתמש," היסטוריה גזומה (לפי תקציב תווים), והקשר נבחר.
    - קרא ל-Vertex AI GenerativeModel (Gemini) עם הגדרות בטיחות; תפוס finish reason וחסימות בטיחות.
    - החזר טקסט תשובה, מקורות ומטה-נתוני זמניים/שימוש.
- שיטות תומכות (אינדיקטיביות): generate_multiple_embeddings, retrieve_chunks_multi_query, fetch_chunk_texts, construct_prompt, generate_response, multimodal_query.

הערות מימוש:
- מזהי וקטור מקודדים זהות chatbot ומקור (chatbot_{chatbot_id}_source_{hash}_chunk_{index}); נתיבי GCS משקפים את זה, מאפשרים fetch ישיר מבלי חיפושי DB נוספים.
- היסטוריה והקשר חסומים על ידי MAX_HISTORY_CHARS ו-MAX_CONTEXT_CHARS כדי לשלוט בזמן phlatency ועלות.
- שורות UsageLog תופסות זמניים, שימוש בtoken (כשזמין), קודי סטטוס ושגיאות מקודדות על ידי request_id.
- נתיב Multimodal: טקסט נגזר-תמונה עשוי לזרוע/לעדן את השאילתה; התמונה המקורית נשלחת למודל רק אם לא נמצא הקשר טקסטואלי מתאים.

### 6.2.1 פונקציות מפתח ואלגוריתמים (pseudocode תמציתי)

- RagService.execute_pipeline(req):
    0. lang ← detect_language(req.query or stt(req.audio))
    1. q_emb ← embed(req.query, task=RETRIEVAL_QUERY)
    2. nbrs ← retrieve(match_engine, q_emb, namespace=chatbot_id, top_k=RAG_TOP_K)
    3. docs ← fetch_texts_gcs(validate_and_map_ids(nbrs.ids, chatbot_id))
    4. ranked ← try_rerank(docs) or docs
    5. prompt ← build_prompt(lang_rule=mirror_user_language(lang), history_budget, ranked[:M_FUSED_CHUNKS])
    6. out ← generate(llm, prompt, safety, temp, max_tokens)
    7. return compose_response(out, sources=ranked.sources, timings, safety, lang)

- RankingService.try_rerank(docs):
    - return discovery_engine.rerank(docs) on success; else return docs (שמור סדר מקורי)

- IngestionTask.run(sources):
    1. chunks ← parse_and_chunk(sources, size≈800, overlap≈80)
    2. embs ← embed_all(chunks, task=RETRIEVAL_DOCUMENT)
    3. ids ← make_vector_ids(chatbot_id, source_hash, index)
    4. upsert(match_engine, ids, embs)
    5. write_texts_gcs(chunks, ids)
    6. persist_vector_mapping(ids ↔ source_identifier)

- validate_and_map_ids(ids, chatbot_id):
    - וודא שכל id מתחיל עם f"chatbot_{chatbot_id}_"; מפה לנתיבי gcs באמצעות קונבנציה

- צינור קולי (אופציונלי):
    - stt(audio, lang_hint?) → text; pipeline(text); if tts_enabled → tts(answer_text, lang) → audio

- סכם URL/טקסט:
    - if req.mode == "summarize_url": page_text ← fetch_and_clean(req.url); return summarize(page_text, lang)
    - if req.mode == "summarize_text": return summarize(req.text, lang)

- ניתוח צילום מסך:
    - ocr ← extract_text(req.image); seed ← ocr or caption(req.image); route seed through pipeline; if needed, answer with extracted elements summary

### 6.3 Ingestion, עדכון ומחיקה

- משימות Ingestion (Celery):
    - קבל URLs/קבצים, נתח וחלק לחתיכות תוכן, הטמע חתיכות, upsert וקטורים ל-Matching Engine והתמד רשומות VectorIdMapping.
    - פלוט מצבי התקדמות (Queued → Updating → Active) שה-UI קורא באמצעות SSE.
- עדכון: בשינוי תוכן, re-ingest והסר וקטורים/מיפויים מיושנים.
- מחיקה:
    - לכל מקור: הסר וקטורים מ-Matching Engine ומחק שורות VectorIdMapping מתאימות.
    - ניקוי chatbot מלא: הסר וקטורים/מיפויים, הודעות צ'אט, משוב מפורט ולוגי שימוש; אפס סטטוס chatbot ל-Empty.

### 6.4 משטח API (רמה גבוהה)

- Auth/session: כניסה ל-admins; מפתח API לכל chatbot לקריאות widget. לסכמות בקשה/תגובה מלאות, ראה נספח B.
- ניהול Chatbot: צור/עדכן/מחק chatbot, נהל מקורות, ייצר מחדש מפתח API. פרטי נקודת קצה מקוטלגים בנספח B.
- קונפיגורציית Widget: מחזיר מיתוג ו-toggles תכונות מורשים על ידי מפתח API של chatbot (נספח B).
- משוב: נקודות קצה thumbs ומשוב מפורט אופציונלי (נספח B לpayloads).
- triggers של Crawl/ingestion: התחל עבודות discovery ו-ingestion (async). ראה נספח B לדוגמאות.
- סטטוס: נקודת קצה SSE זורמת עדכוני סטטוס chatbot (נספח B יש לו סכמת אירוע SSE).
- קול: נקודות קצה STT/TTS (ראה נספח B לפורמטי אודיו, payloads וקודי שפה).
- סיכום: נקודות קצה ל-summarize-by-URL ו-summarize-by-text (נספח B לבקשה/תגובה ומגבלות גודל).
- ניתוח צילום מסך: נקודת קצה להעלאת תמונה וניתוח (נספח B לסוגי תמונה, מגבלות גודל והערות OCR).

### 6.5 אימות, הרשאה וגבלת קצב

- זרימת מפתח API: Authorization: Bearer <key> נדרש לנקודות קצה widget; ה-backend מאמת מול מפתח מוצפן שנשמר עם ה-chatbot.
- בדיקות בעלות: נקודות קצה ניהול מאמתות בעלות client_id.
- מגבלות קצב: מיושמות על נקודות קצה רגישות (למשל, כניסה, צור/עדכן, widget-config, צ'אט) כדי להגן על משאבים.

### 6.6 תמונת מצב של מודל נתונים (תמציתי)

- Chatbot: id, client_id, api_key_hash, name, config (מיתוג/toggles), status.
- VectorIdMapping: id, chatbot_id, vector_id, source_identifier, created_at.
- ChatMessage: id, chatbot_id, role (user/assistant), content, created_at; lang אופציונלי.
- DetailedFeedback: id, chatbot_id, message_id, rating, משוב free-text, created_at.
- UsageLog: id, chatbot_id, action, request_id, duration_ms, status_code, ספירות token (אם זמין), error, source_ids.
- User/Admin: שדות auth בסיסיים ובעלות על chatbots.

הערה: דיאגרמת ER בפרק העיצוב משקפת את הישויות האלה והקשרים שלהן (ראה סעיף 4.2 ונספח E).

### 6.7 טיפול בשגיאות וניתור

- לוגים מובנים כוללים request_id וזמניים לכל שלב (embeddings, retrieval, fetch, rerank, generation).
- מקרי בטיחות וסירוב מחזירים הודעות ידידותיות למשתמש; פרטים מתועדים אבל לא נחשפים למשתמשי קצה.
- טלמטריה מתמידה ל-UsageLog לביקורות וניתוח איכות.

### 6.8 קונפיגורציה ו-clients

- לרשימה מלאה של משתני env וברירות מחדל, ראה סעיף עיצוב 4.9. הערות:
    - יישור Cloud SDK: GOOGLE_CLOUD_PROJECT ו-GOOGLE_CLOUD_LOCATION מוגדרים פרוגרמטית היכן שנדרש (כולל workers).
    - Clients מאותחלים פעם אחת בשירות RAG (Vertex AI, google.genai, GCS) ונעשה בהם שימוש חוזר על פני בקשות כשאפשר.
    - Workers מבטיחים GOOGLE_GENAI_USE_VERTEXAI=True כדי ש-google.genai ינתב דרך Vertex AI.

### 6.9 אינטגרציית Frontend

- Widget: שולח בקשות צ'אט עם chatbot_id ומפתח API Bearer; מרנדר תשובה, מקורות ומטפל בהודעות בטיחות/fallback; מכבד toggles מיתוג.
- Admin SPA: מנהל chatbots/מקורות, מתחיל ingestion, צורך SSE לסטטוס ומציג קטעי embed ושגיאות אימות.

### 6.10 עוזר Agentic (קצר)

- הערה: ה-demo הקמעוני agentic הוא כרגע באנגלית בלבד ונפרד מ-chatbot WAS RAG. מפת דרכים: תמיכה קולית רב-לשונית מלאה ונקודות אינטגרציה אופציונליות ל-WAS.

- דפוס: LLM + כלים. המודל בוחר כלי, מחלץ פרמטרים, קורא לו, צופה בתוצאות ומרכיב תגובה.
- כלים מיושמים (אינדיקטיביים): list_products, get_product, add_to_cart, remove_from_cart, view_cart, checkout, identify_image.
- מגבלות: טווח מוגבל לכלים מוצהרים; אין פעולות אוטונומיות מעבר לזרימות שמתחילות על ידי משתמש.

### 6.11 תוצאות והערכה (תוצאות והערכה)

סעיף זה מסכם את המבחנים המוקדי-תוצאה האחרונים עבור chatbot RAG הראשי. המספרים למטה משקפים את הבנצ'מרקים שסופקו והם נועדו להנחות איטרציה, לא לשרת כטענות שיווקיות.

#### 6.11.1 Retrieval של מחט-בערימת-חציר

- קורפוס: ~150 דפים, עם משפט "מחט" אחד מוטמע פעם אחת.
- שאילתות: 10 וריאציות שפה-טבעית שתוכננו כדי להוציא את המשפט הספציפי הזה.
- תוצאה: 10/10 retrievals מוצלחים (100%).
- מצב: RAG סטנדרטי (מתקדם מבוטל לריצה זו); reranker מופעל.
- למה זה חשוב: זה מלחיץ recall מקצה-לקצה תחת הצינור הנוכחי שלנו (חיתוך ≈800/80, בידוד namespace לכל chatbot, retrieval → rerank). 100% עקבי מצביע שretrieval top-K בתוספת reranking מעלה באופן אמין את הקטע המדויק כשהידע קיים.
- הערות וסיכונים:
    - שמור עין על סחף מילים נרדפות ו-paraphrase; שקול rephrasings יריבותיים תקופתיים.
    - אם גודל הקורפוס גדל משמעותית, בחן מחדש RAG_TOP_K ותקציב reranker כדי לשמר recall מבלי לנפח latency.

#### 6.11.2 שאלות ותשובות סטנדרטיות (תחום מתמחה)

- סט: 50 שאלות מתוקנות, ספציפיות-תחום (תערובת של single-hop ו-multi-hop קל).
- הערכה: ציון דמיון סמנטי אוטומטי על ידי Gemini 2.5 Pro מול תשובות צפויות.
- תוצאה: ≈96% דיוק.
- מצב: RAG סטנדרטי (מתקדם מבוטל לריצה זו); reranker מופעל; דבקות ידע מוגדרת לקפדנית.
- פרשנות: רוב החמצות היו כמעט-החמצות או בעיות גרעיניות-ביטוי במקום עובדות לחלוטין שגויות. הידוק prompt דבקות-ידע והפעלת follow-ups הבהרה קצרים יכולים להקטין את המקרים האלה.

#### 6.11.3 קריאת התוצאות האלה

- מדרגים אוטומטיים הם כיווניים. למקרי קצה (תשובות דו-משמעיות או בסגנון רשימה), כלול בדיקות נקודתיות אנושיות.
- המספרים המדווחים משתמשים ב-RAG סטנדרטי; הצינור הניסיוני המתקדם ביצע נמוך בפריסה זו ולא שימש לתוצאות אלה.
- Reranker היה מופעל; אם לא זמין, המערכת משמרת את סדר ה-retrieval המקורי כ-fallback.
- טיפי רפרודוקטיביות: תקע פרמטרי retrieval (RAG_TOP_K, reranker on/off), שמור תקציבי הקשר/היסטוריה קבועים ועשה שימוש חוזר באותו seed/config כשנתמך; תעד finish_reason ו-safety_ratings לריצות כדי לזהות דפוסי בטיחות/סירוב.

#### 6.11.4 צעדים הבאים (קל משקל)

- הפוך אוטומטי חבילת regression קטנה (תת-קבוצה של 50 השאלות ותשובות + 2–3 prompts ערימת חציר) ותעד דיוק לכל commit.
- עקוב אחר שיעור פגיעה retrieval ודיוק תשובה לאורך זמן ב-UsageLog; שרטט מגמות לצד latency P50/P95.
- הרחב עם prompts רב-לשוניים כדי לאמת "תענה בשפת המשתמש."
- במידה תקופתית re-sweep RAG_TOP_K והגדרות reranker ככל שהקורפוס גדל.
- עקוב אחר התפלגות finish_reason (STOP לעומת non-STOP) ו-safety_ratings כדי לנטר שיעורי סירוב/חסימה.

## 7. פרטים טכניים (פירוט טכני)

מטרה: מקד פרק זה על איך נתונים מטופלים ל-RAG ואיך מודלים מוקשבים. קטלוגים מפורטים של API ופרמטרים חיים בנספחים כדי להימנע מיתור.

### 7.1 טיפול בנתונים והכנה (RAG)

- קלטים: URLs ו-קבצים מועלים (.txt, .pdf, .docx). HTML מנוקה לטקסט; קבצים מנותחים באמצעות pdfminer/docx.
- חיתוך: RecursiveCharacterTextSplitter גודל ≈ 800 תווים עם ≈ 80 חפיפה.
- אחסון ומיפוי: טקסטים גולמיים של חתיכות נשמרים ב-GCS; מזהי וקטור דטרמיניסטיים מקודדים זהות chatbot ומקור (chatbot_{chatbot_id}_source_{hash}_chunk_{index}). שורת VectorIdMapping מקשרת vector_id → source_identifier.

ראה נספח C לפריסת האחסון המלאה וקונבנציות מיפוי.

### 7.2 קונפיגורציית מודל ו-prompting

- Embeddings: google.genai models.embed_content עם מודל EMBEDDING_MODEL_NAME; RETRIEVAL_QUERY לשאילתות, RETRIEVAL_DOCUMENT ל-ingestion.
- Retrieval: Vertex AI Matching Engine עם סינון Namespace לפי chatbot_id; ספירות top-K וחתיכות מאוחדות כמו שמוקשב.
- Reranking: Discovery Engine semantic-ranker-default-004 באמצעות RankingService; משמר סדר מדורג מחדש; נופל חזרה לסדר retrieval מקורי אם לא זמין.
- כללי Prompt: רמת דבקות ידע ו"תענה בשפת המשתמש." היסטוריה והקשר מתוקצבים על ידי מגבלות תווים.
- יצירה: Vertex AI GenerativeModel עם טמפרטורה ומקסימום tokens; הגדרות בטיחות נאכפות.
- Multimodal: חילוץ טקסט תמונה אופציונלי; שלח מחדש של תמונה מקורית רק כשלא נמצא הקשר טקסטואלי מתאים.

קונפיגורציית שפה ודיבור:
- זיהוי שפה: LID קל משקל בשימוש כדי להגדיר את שפת היעד; נופל חזרה לרמז משתמש או ברירת מחדל של אתר.
- שפת תגובה: prompts אוכפים "תענה בשפת המשתמש"; דטרמיניסטי אלא אם מוחלף על ידי מדיניות שוכר.
- הגדרות דיבור: מודל STT/TTS, קצב דגימה וקידוד מוקשבים לכל סביבה; ראה נספח B/C לערכים נוכחיים.

פרטי סיכום וניתוח צילום מסך:
- סיכום: תבנית הוראה תמציתית; תקציב אורך ניתן להקשה; שפה משקפת שפת משתמש מזוהה או מרומזת.
- מצב URL: fetch → ניקוי HTML → חילוץ תוכן-עיקרי → סכם.
- מצב הדבקה: סכם טקסט גולמי ישירות.
- מצב צילום מסך: OCR קודם; captioning תמונה אופציונלי אם OCR דליל; טקסט מחולץ זורע RAG או סיכום ישיר.

ראה נספח C לשמות פרמטרים וברירות מחדל.

### 7.3 הפניות

- נקודות קצה API וסכמות: נספח B.
- פרמטרי RAG, פריסת אחסון, מגבלות קצב ופרטי סביבה: נספח C.
- הקשר ארכיטקטורה: סעיף 4.2. פנימיות מימוש: סעיף 6.

## 8. סיכום והרחבות עתידיות (סיכום והרחבות עתידיות)

### 8.1 סיכום

Website AI Assistance (WAS) מספק chatbot RAG רב-שוכר, מבוסס-קוד עם בידוד קפדני לכל chatbot, ingestion חזק, reranking ובקרות בטיחות. המערכת משתלבת עם Vertex AI (LLMs + Matching Engine), שומרת טקסט חתיכות ב-GCS וחושפת API נקי + widget. הערכות עדכניות מצביעות על איכות חזקה: 100% retrieval במבחן מחט-בערימת-חציר (10/10) ו≈96% דיוק בסט שאלות ותשובות מתמחה של 50 שאלות, עם חסימות בטיחות זניחות ו-STOP finishes טיפוסיים. זה מקים בסיס חזק למעבר מעבר לשאלות ותשובות לסיוע משימות.

הערה תפעולית: הצינור הניסיוני RAG המתקדם ביצע נמוך בפריסה זו; RAG סטנדרטי נשאר ברירת המחדל והמצב המומלץ. ה-Discovery Engine reranker הוא אופציונלי ואם לא זמין, המערכת משמרת את סדר ה-retrieval המקורי כ-fallback.

### 8.2 הרחבות עתידיות (רעיונות בעלי השפעה גבוהה)

מפת דרכים דף אחד (סיכום):
- אינטגרציה Agentic ל-WAS: איחד RAG + כלים בsession יחיד; toggles לכל שוכר, קוטות ולוגי ביקורת של קריאות כלים.
- פעולות בתוך-דף: מילוי טפסים בטוח ו-overlays מודרכים; אוטומציה מוגבלת של דפדפן באמצעות sandbox (allow-lists, מגבלות קצב, redaction, אישורים).
- התאמה אישית (opt-in): פרופילי משתמש מוסכמים; מחברי IdP/CRM קלים; retrieval מודע-סגמנט ו-ABAC על מקורות.
- איכות Retrieval: חיפוש היברידי (dense+BM25), מסנני מטה-נתונים, חיתוך דינמי; rerankers חוצי-לשון; תכנון מרובה-קפיצות ממוקד.
- רעננות ידע: זיהוי שינוי, re-index מצטבר ו-re-ingestion אוטומטי ל-URLs מעודכנים.
- הערכה וממשל: eval רציף (זהב + יריבותי), בדיקות ביסוס/ציטוט, HITL לכלים רגישים; בקרות מדיניות ל-PII, הסכמה ו-retention.
- קול ו-multimodal: STT זורם עם barge-in, TTS מהיר יותר; שאלות ותשובות מבוססות-תמונה/חיפוש חזותי; סיכום מסמכים עם חילוץ טבלה/רשימה.
- פלטפורמה ועלות: מעקב עמוק ו-dashboards של SLO; cache embedding, top-K אדפטיבי ותקציבי reranker; workers אוטו-scaling; מקום מגורים אזורי ו-CMEK.
- אנליטיקה ו-ops תוכן: טקסונומיית שאלות וניתוח פערים; תובנות admin על intents נכשלים, חסימות בטיחות, latency והצלחת כלים.
- שלבים: שלב 1 (toggles סוכן + POC מילוי-טופס + UI אישורים), שלב 2 (אוטומציה בsandbox + retrieval היברידי + dashboards), שלב 3 (ספריית כלים רחבה יותר + התאמה אישית מתקדמת + ממשל בוגר).

## 9. ביבליוגרפיה (ביבליוגרפיה)

סגנון: הפניות מספריות [1], [2], … עם URLs מלאים (ו-DOI היכן שזמין). השתמש ב-[n] לציטוטים בטקסט באזכור ראשון של שיטה/רכיב.

### 9.1 אקדמיה ושיטות
1. Vaswani, A., Shazeer, N., Parmar, N., et al. "Attention Is All You Need." NeurIPS, 2017. https://arxiv.org/abs/1706.03762
2. Lewis, P., Perez, E., Piktus, A., et al. "Retrieval‑Augmented Generation for Knowledge‑Intensive NLP." NeurIPS, 2020. https://arxiv.org/abs/2005.11401
3. Yao, S., Zhao, J., Yu, D., et al. "ReAct: Synergizing Reasoning and Acting in Language Models." 2022. https://arxiv.org/abs/2210.03629
4. Li, M., Ma, X., Shen, D., et al. "SELF‑INSTRUCT: Aligning Language Models with Self‑Generated Instructions." 2023. https://arxiv.org/abs/2212.10560
5. Liu, J., Xu, W., Xie, S., et al. "Reranking for Retrieval‑Augmented Generation: A Survey." 2024. https://arxiv.org/abs/2402.11026

### 9.2 תיעוד ענן ומודל
6. Google Cloud. "Generative AI on Vertex AI — Overview." https://cloud.google.com/vertex-ai/docs/generative-ai/learn/overview (נגיש: 2025‑08‑10)
7. Google Cloud. "Vertex AI Matching Engine — Overview." https://cloud.google.com/vertex-ai/docs/matching-engine/overview (נגיש: 2025‑08‑10)
8. Google for Developers. "Text embeddings API (gemini‑embedding‑001)." https://ai.google.dev/docs/embeddings_api (נגיש: 2025‑08‑10)
9. Google Cloud. "Reranking for Vertex AI Search and Conversation." https://cloud.google.com/generative-ai-app-builder/docs/reranking (נגיש: 2025‑08‑10)

### 9.3 frameworks וספריות
10. Flask Documentation. "Flask." https://flask.palletsprojects.com/ (נגיש: 2025‑08‑10)
11. SQLAlchemy Documentation. "SQLAlchemy." https://docs.sqlalchemy.org/ (נגיש: 2025‑08‑10)
12. Celery Project. "Celery: Distributed Task Queue." https://docs.celeryq.dev/en/stable/ (נגיש: 2025‑08‑10)
13. Redis. "Redis Documentation." https://redis.io/docs/ (נגיש: 2025‑08‑10)
14. Beautiful Soup Documentation. "bs4." https://www.crummy.com/software/BeautifulSoup/bs4/doc/ (נגיש: 2025‑08‑10)
15. MDN Web Docs. "Server‑Sent Events (EventSource)." https://developer.mozilla.org/docs/Web/API/Server-sent_events (נגיש: 2025‑08‑10)

### 9.4 מערכי נתונים ו-benchmarks
16. פנימי. "קורפוס מבחן מחט-בערימת-חציר ותוצאות (10/10)." חפץ פרויקט; ראה שורש repository: combined_haystack.txt (נגיש: 2025‑08‑10)
17. פנימי. "סט שאלות ותשובות מתמחה של 50 ותוצאות מדורגות Gemini (≈96%)." חפץ פרויקט; נשמר עם מתחזקים (נגיש: 2025‑08‑10)

### 9.5 מאמרים איכותיים (אופציונלי)
18. (מקום שמור) דפוסי RAG ייצור ב-GCP/Vertex AI. הוסף קישור סופי אם בשימוש.

הערה: הפניות compliance/נגישות הושמטו במכוון לטווח MVP לפי הנחיות פרויקט.

### 9.6 frameworks וכלים נוספים (בשימוש בקוד)
19. LangChain. "Documentation." https://python.langchain.com/docs/ (נגיש: 2025‑08‑10)
20. pdfminer.six. "Documentation." https://pdfminersix.readthedocs.io/ (נגיש: 2025‑08‑10)
21. python‑docx. "Documentation." https://python-docx.readthedocs.io/ (נגיש: 2025‑08‑10)
22. Pillow. "Pillow (PIL Fork) Documentation." https://pillow.readthedocs.io/ (נגיש: 2025‑08‑10)
23. Alembic. "Alembic Documentation." https://alembic.sqlalchemy.org/ (נגיש: 2025‑08‑10)

### 9.7 מקורות מתחרים
24. WebAssistants.ai — אתר מוצר. https://webassistants.ai (נגיש: 2025‑08‑11)
25. A‑Eye Web Chat Assistant — רישום Chrome Web Store. https://chromewebstore.google.com/detail/a-eye-web-chat-assistant/cdjignhknhdkldbjijipaaamodpfjflp (נגיש: 2025‑08‑11)
26. Salesloft Drift — דף פלטפורמה. https://www.salesloft.com/platform/drift (נגיש: 2025‑08‑11)

## 10. נספחים (נספחים)

מטרה: ספק פרטים ברמת מימוש מבלי לנפח פרקים עיקריים. אין dump של dependency/version לפי בקשה.

### A. Prompting ותבניות
- ראה ./appendix/A-prompts-and-templates.md עבור prompt המערכת הנוכחי, הקדמת היסטוריה, prompts תמונה והערות (תומך ב-4.3, 4.5, 6.2).

### B. חוזי API (סכמות)
- ראה ./appendix/B-api-contracts.md לדוגמאות בקשה/תגובה מינימליות המכסות יצירה, קונפיגורציית widget, אינטראקציה קולית, משוב, מקורות, discovery/crawl וסכמת SSE (תומך ב-4.1–4.2, 6.4).

### C. הפניה לקונפיגורציית RAG
- ראה ./appendix/C-rag-configuration.md לפרמטרי RAG/LLM, מסנני retrieval, reranking, תקציבי היסטוריה וקונבנציות מיפוי (תומך ב-4.4, 4.9, 7.1–7.2, 6.2).

### D. חפצי הערכה (פנימי)
- ראה ./appendix/D-evaluation-artifacts.md למתכון ערימת חציר והערות סט 50-שאלות ותשובות (תומך ב-6.11.1–6.11.4).

### E. דיאגרמות ארכיטקטורה וזרימות נתונים
- ראה ./appendix/E-architecture-diagrams.md לקישורי דיאגרמה וכתוביות (תומך ב-4.2). מקם תמונות מיוצאות תחת ./images.

### F. Runbook ופתרון בעיות
- ראה ./appendix/F-runbook-troubleshooting.md לתיקונים מהירים לבעיות MVP נפוצות (תומך ב-4.7, 4.10, 6.7).
