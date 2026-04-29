# 🚀 JobTrack AI — Resume Matcher

AI-powered job application tracker jo batata hai ki tera resume kitna match karta hai kisi bhi job ke saath.

---

## ✅ Features
- Resume PDF upload karke AI se match % nikalo
- Matched & missing skills dekho
- AI suggestions pao resume improve karne ke liye
- Sare applications ek jagah track karo
- Status update karo (Applied → Interview → Offered)
- Dashboard with live stats

---

## 🛠️ Setup — Step by Step

### Step 1 — Python install hai? Check karo
```
python --version
```

### Step 2 — Project folder mein jao
```
cd job_tracker
```

### Step 3 — Virtual environment banao (recommended)
```
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```

### Step 4 — Dependencies install karo
```
pip install -r requirements.txt
```

### Step 5 — Gemini API Key lo (FREE hai)
1. https://aistudio.google.com/app/apikey pe jao
2. "Create API Key" click karo
3. Key copy karo

### Step 6 — .env file banao (same folder mein)
```
GEMINI_API_KEY=yahan_apni_key_paste_karo
```

### Step 7 — App run karo
```
python app.py
```

### Step 8 — Browser mein kholo
```
http://127.0.0.1:5000
```

---

## 📁 Project Structure
```
job_tracker/
│
├── app.py              ← Main Flask backend
├── requirements.txt    ← Python dependencies
├── .env                ← Apni API key (khud banao)
├── job_tracker.db      ← SQLite database (auto banta hai)
│
├── templates/
│   └── index.html      ← Frontend UI
│
└── uploads/            ← Uploaded resumes store hote hain yahan
```

---

## 🔑 Gemini API Key kahan se milegi?
- https://aistudio.google.com/app/apikey
- Bilkul FREE hai — koi credit card nahi chahiye

---

## 🏆 Resume Pe Kaise Likhna Hai?

```
AI Job Application Tracker — Python, Flask, SQLite, Gemini API
- Built full-stack web app to track job applications with AI resume matching
- Integrated Google Gemini API to analyze resume vs job description (match %)
- Implemented PDF parsing, REST APIs, and SQLite database
- Tech Stack: Python, Flask, SQLite, HTML/CSS/JS, Gemini API
```

---

## 👨‍💻 Made by Satyam Mishra
BSc AI & ML — Mumbai University
