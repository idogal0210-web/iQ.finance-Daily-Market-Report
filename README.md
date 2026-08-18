# 📊 iQ.finance — Daily Market Report

מערכת אוטומטית שמייצרת ושולחת דוח שוק, מט״ח וסחורות יומי לכתובת מייל, כל יום ב-07:00 שעון ישראל.

---

## 🗂 מבנה הפרויקט

```
daily-market-report/
├── .github/
│   └── workflows/
│       └── daily_report.yml   ← GitHub Actions (cron יומי)
├── src/
│   ├── fetch_data.py          ← FMP API + yfinance (עם חישוב 52wk/MA50/מט"ח) + FMP News
│   ├── generate_analysis.py   ← Gemini AI (עם מנגנון Safety Settings ו-Fallbacks)
│   ├── build_report.py        ← HTML generator
│   └── send_email.py          ← Gmail SMTP sender
├── main.py                    ← נקודת כניסה
├── requirements.txt
├── .gitignore
└── README.md
```

---

## ⚙️ הגדרת GitHub Secrets

עבור אל: `GitHub repo → Settings → Secrets and variables → Actions → New repository secret`

| Secret | איך להשיג |
|--------|-----------|
| `GMAIL_USER` | כתובת ה-Gmail שממנה נשלח (לדוגמה: `yourname@gmail.com`) |
| `GMAIL_APP_PASSWORD` | ראה הוראות למטה |
| `RECIPIENT_EMAIL` | המייל שיקבל את הדוח |
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/app/apikey) — חינמי |
| `FMP_API_KEY` | [Financial Modeling Prep](https://site.financialmodelingprep.com/developer/docs/) — מפתח חינמי לנתוני שוק וחדשות |
| `NEWS_API_KEY` | (אופציונלי) למעקב כותרות חלופי |

---

## 🔑 איך ליצור Gmail App Password

> **חובה**: חשבון Gmail עם **2-Step Verification** מופעל.

1. היכנס ל-[myaccount.google.com/security](https://myaccount.google.com/security)
2. חפש **"App passwords"** (סיסמאות אפליקציה)
3. לחץ **"Create app password"**
4. שם: `iQ Market Report`
5. העתק את הסיסמה בת 16 התווים → הדבק ב-Secret `GMAIL_APP_PASSWORD`

---

## 🚀 הפעלה ראשונה

### 1. דחוף את הקוד
```bash
git add .
git commit -m "feat: updated daily market report system"
git push origin main
```

### 2. הגדר את ה-Secrets (ראה למעלה)

### 3. הרץ ידנית לבדיקה
```
GitHub repo → Actions → Daily Market Report → Run workflow
```

---

## 🕖 תזמון

| עונה | שעה UTC | שעה ישראל |
|------|---------|-----------|
| **קיץ (UTC+3)** | `0 4 * * *` | 07:00 |
| **חורף (UTC+2)** | `0 5 * * *` | 07:00 |

לשינוי — ערוך את `.github/workflows/daily_report.yml` בשורת `cron:`.

---

## 📦 נתונים ונכסים שנאספים

| קטגוריה | מקור | פרטים |
|--------|------|-------|
| **מדדים ומט״ח** | yfinance / FMP | S&P 500, נאסד"ק, דאו ג'ונס, ת"א-125, דולר/שקל (`USDILS=X`) |
| **סחורות** | yfinance | WTI Crude, Brent, Natural Gas, Gold, Copper, Wheat, ICL |
| **חברות בפוקוס** | FMP / yfinance | Nvidia, Lockheed Martin, Delta Air Lines, Vistra, Frontline, Diamondback, Freeport, Southern Copper, אלביט מערכות, ICL |
| **חדשות שוק** | FMP Stock News | כותרות וניתוח אקטואלי בזמן אמת |

---

## ⚠️ הגבלות חינמיות

| שירות | מגבלה חינמית |
|--------|--------------|
| **yfinance** | ללא מגבלה (נתוני Yahoo Finance + חישוב היסטורי) |
| **FMP API** | 250 בקשות/יום במנגנון החינמי |
| **Gemini AI** | 60 req/min, 1,500 req/day |
| **GitHub Actions** | 2,000 דקות/חודש (Ubuntu) |
| **Gmail SMTP** | 500 מיילים/יום |

---

## ⚖️ כתב ויתור

הדו״ח מיועד למטרות לימוד ומידע בלבד ואינו מהווה ייעוץ השקעות.

