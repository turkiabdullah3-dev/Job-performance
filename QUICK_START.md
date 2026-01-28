# ⚡ خطوات النشر السريعة - turki20.sa

## 🎯 الهدف
نشر Backend على Render + ربطه مع Frontend على Cloudflare Pages

---

## 📝 الخطوات

### 1. رفع على GitHub
```bash
cd /Users/turki/Desktop/hr
git init
git add .
git commit -m "Ready for deployment"
git remote add origin https://github.com/YOUR_USERNAME/hr-backend.git
git push -u origin main
```

### 2. نشر على Render
1. [render.com](https://render.com) → New Web Service
2. اختر Repository
3. Settings:
   - **Name:** `turki20-hr-api`
   - **Build:** `pip install -r requirements.txt`
   - **Start:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
4. Environment Variables:
   ```
   ALLOWED_ORIGINS=https://turki20.sa,https://www.turki20.sa,http://localhost:8080
   FLASK_ENV=production
   ```
5. Create Web Service
6. **انسخ الرابط**: `https://turki20-hr-api.onrender.com`

### 3. تحديث script.js
السطر 13:
```javascript
const API_BASE = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost' 
    ? 'http://127.0.0.1:8080' 
    : 'https://turki20-hr-api.onrender.com'; // ضع رابط Render
```

### 4. رفع على Cloudflare Pages
```bash
git add script.js
git commit -m "Update API endpoint"
git push
```
أو: ارفع يدوياً في Cloudflare Dashboard

### 5. الاختبار
- افتح: `test_backend.html` في المتصفح
- أو: افتح `https://turki20.sa` وارفع ملف Excel

---

## ✅ التحقق السريع

**Backend شغال؟**
```
https://turki20-hr-api.onrender.com/init-session
```
يجب أن يعطي JSON

**Frontend شغال؟**
```
https://turki20.sa
```
يجب أن يفتح الموقع

**CORS شغال؟**
افتح Console في turki20.sa ولا يوجد أخطاء CORS

---

## 🐛 حل سريع للمشاكل

### خطأ CORS
→ أضف `https://turki20.sa` في `ALLOWED_ORIGINS` على Render

### خطأ 503
→ انتظر 30 ثانية (Cold Start)

### "الخادم غير متاح"
→ تأكد رابط API في `script.js` صحيح

---

**✨ انتهى!**

للتفاصيل الكاملة: `DEPLOYMENT_TURKI20.md`
