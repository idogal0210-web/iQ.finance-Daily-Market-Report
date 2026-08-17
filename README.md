# 📊 iQ.finance — Daily Market Report

מערכת אוטומטית שמייצרת ושולחת דוח שוק וסחורות יומי לכתובת מייל, כל יום ב-07:00 שעון ישראל.

---

## 🗂 מבנה הפרויקט

```
daily-market-report/
├── .github/
│   └── workflows/
│       └── daily_report.yml   ← GitHub Actions (cron יומי)
├── src/
│   ├── fetch_data.py          ← yfinance + NewsAPI + Gemini AI
│   ├── build_report.py        ← HTML generator
│   └── send_email.py          ← Gmail SMTP sender
├── main.py                    ← נקודת כניסה
├── requirements.txt
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
| `NEWS_API_KEY` | [newsapi.org](https://newsapi.org/register) — Developer plan חינמי |

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

### 1. צור GitHub Repository חדש
```bash
git init
git remote add origin https://github.com/YOUR_USERNAME/daily-market-report.git
```

### 2. דחוף את הקוד
```bash
git add .
git commit -m "feat: initial daily market report system"
git push -u origin main
```

### 3. הגדר את ה-Secrets (ראה למעלה)

### 4. הרץ ידנית לבדיקה
```
GitHub repo → Actions → Daily Market Report → Run workflow
```

---

## 🕖 תזמון

| עונה | שעה UTC | שעה ישראל |
|------|---------|-----------|
| **קיץ (UTC+3)** | `0 4 * * *` | 07:00 |
| **חורף (UTC+2)** | `0 5 * * *` | 07:00 |

כרגע מוגדר ל-**קיץ** (`0 4 * * *`).  
לשינוי — ערוך את `.github/workflows/daily_report.yml` בשורת `cron:`.

---

## 📦 סחורות שנאספות

| סחורה | מקור |
|--------|------|
| WTI Crude, Brent, Natural Gas | yfinance (futures) |
| Gold, Nickel | yfinance (futures) |
| Wheat | yfinance (futures) |
| ICL Group (Potash proxy) | yfinance (מניה) |

---

## ⚠️ הגבלות חינמיות

| שירות | מגבלה חינמית |
|--------|--------------|
| **yfinance** | ללא מגבלה (נתוני Yahoo Finance) |
| **NewsAPI** | 100 בקשות/יום, חדשות עד 30 יום אחורה |
| **Gemini AI** | 60 req/min, 1,500 req/day |
| **GitHub Actions** | 2,000 דקות/חודש (Ubuntu) |
| **Gmail SMTP** | 500 מיילים/יום |

---

## ⚖️ כתב ויתור

הדוח מיועד למטרות לימוד ומידע בלבד ואינו מהווה ייעוץ השקעות.
