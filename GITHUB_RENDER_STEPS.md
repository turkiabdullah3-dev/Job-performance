# 🔗 ربط مع GitHub وNayload على Render

## ✅ Git جاهز محلياً

```bash
cd /Users/turki/Desktop/hr
git init ✅ 
git add . ✅
git commit ✅
git branch -M main ✅
```

---

## 📋 الخطوات الثلاث التالية:

### 1️⃣ أنشئ Repository جديد على GitHub

1. اذهب إلى [github.com/new](https://github.com/new)
2. **Repository Name:** `hr-analytics-backend`
3. **Description:** `HR Analytics Backend - Python Flask - turki20.sa`
4. **Private:** اختر ما تفضل
5. **لا تختر** "Initialize this repository with..."
6. اضغط **Create repository**

### 2️⃣ ربط مع GitHub

بعد إنشاء الـ Repository، GitHub سيعطيك الأوامر. شغّل هذه الأوامر:

```bash
cd /Users/turki/Desktop/hr

git remote add origin https://github.com/YOUR_USERNAME/hr-analytics-backend.git
git push -u origin main
```

**مثال:**
```bash
git remote add origin https://github.com/turki20/hr-analytics-backend.git
git push -u origin main
```

### 3️⃣ نشر على Render

1. اذهب إلى [render.com](https://render.com)
2. سجل دخول بـ GitHub (اضغط Sign Up with GitHub)
3. اسمح للتطبيق بالوصول إلى حسابك
4. اضغط **New +** → **Web Service**
5. اختر Repository: `hr-analytics-backend`
6. الإعدادات:
   - **Name:** `turki20-hr-api`
   - **Environment:** `Python 3`
   - **Region:** `Frankfurt` أو الأقرب
   - **Branch:** `main`

7. **Build & Start Commands** (سيكتشفها من render.yaml):
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`

8. اضغط **Advanced** وأضف Environment Variables:
   ```
   ALLOWED_ORIGINS = https://turki20.sa,https://www.turki20.sa,http://localhost:8080
   FLASK_ENV = production
   PYTHON_VERSION = 3.11
   ```

9. اضغط **Create Web Service**

10. **انتظر 3-5 دقائق** حتى ينتهي النشر

11. **انسخ الرابط** من الصفحة (مثل: `https://turki20-hr-api.onrender.com`)

---

## ✨ بعد النشر

### تحديث script.js

افتح `/Users/turki/Desktop/hr/script.js` السطر 13 وحدّث:

```javascript
// من هذا:
const API_BASE = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost' 
    ? 'http://127.0.0.1:8080' 
    : 'https://YOUR-RENDER-APP-NAME.onrender.com';

// إلى هذا (ضع رابط Render الفعلي):
const API_BASE = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost' 
    ? 'http://127.0.0.1:8080' 
    : 'https://turki20-hr-api.onrender.com';
```

### رفع على Cloudflare Pages

```bash
cd /Users/turki/Desktop/hr

# إذا كان لديك repo منفصل للـ Frontend
git add script.js
git commit -m "Update API endpoint to Render"
git push
```

**أو رفع يدوي على Cloudflare Pages Dashboard**

---

## 🧪 الاختبار

### اختبار Backend
```
https://turki20-hr-api.onrender.com/init-session
```
يجب أن يعطي JSON

### اختبار Frontend
```
https://turki20.sa
```
ارفع ملف Excel وتأكد من الاتصال

### اختبار مفصّل
افتح `test_backend.html` واختبر:
1. الاتصال
2. Session
3. CORS

---

## 📞 مساعدة إضافية

إذا واجهت مشكلة:

### خطأ في Push إلى GitHub
```bash
# إذا قال: "git push failed"
# تأكد من:
1. اسم الـ Repository صحيح
2. لديك إذن الوصول (Personal Token)
3. SSH Key مضبوط (أو استخدم HTTPS)
```

### خطأ في Render
اذهب إلى Render Dashboard → Logs وابحث عن الخطأ

### خطأ CORS
أضف `https://turki20.sa` في `ALLOWED_ORIGINS` على Render

---

**✨ بعد اتمام كل هذه الخطوات = موقعك يعمل على turki20.sa!**
