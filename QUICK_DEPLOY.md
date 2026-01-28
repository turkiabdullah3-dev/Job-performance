# نشر سريع - TL;DR

## 🚀 خطوات سريعة للنشر

### 1️⃣ رفع على GitHub
```bash
git init
git add .
git commit -m "Backend ready for deployment"
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

### 2️⃣ نشر على Render
1. [render.com](https://render.com) → New Web Service
2. اختر Repository → `hr-analytics-backend`
3. Settings:
   - **Name:** `hr-analytics-api`
   - **Environment:** Python 3
   - **Build:** `pip install -r requirements.txt`
   - **Start:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
4. Environment Variables:
   ```
   ALLOWED_ORIGINS=https://your-cloudflare-pages.pages.dev
   FLASK_ENV=production
   ```
5. Create Web Service

### 3️⃣ تحديث Frontend
في `script.js` السطر 12:
```javascript
const API_BASE = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost' 
    ? 'http://127.0.0.1:8080' 
    : 'https://YOUR-APP-NAME.onrender.com'; // ضع الرابط من Render
```

### 4️⃣ رفع على Cloudflare
```bash
git add script.js
git commit -m "Update API endpoint"
git push
```

---

## ✅ اختبار
- Backend: `https://your-app.onrender.com/init-session`
- Frontend: افتح موقعك وارفع ملف Excel

---

## ⚠️ مهم
- **Free Plan على Render:** يتوقف بعد 15 دقيقة من عدم الاستخدام
- **Cold Start:** أول طلب يأخذ 30-60 ثانية
- **CORS:** تأكد من إضافة رابط Cloudflare في `ALLOWED_ORIGINS`

---

للتفاصيل الكاملة: راجع `DEPLOYMENT_GUIDE.md`
