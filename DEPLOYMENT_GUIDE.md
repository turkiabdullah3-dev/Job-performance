# دليل النشر - HR Analytics System
## نشر Backend على Render + Frontend على Cloudflare Pages

---

## ✅ الملفات الجاهزة

تم إعداد الملفات التالية:
- ✓ `requirements.txt` - مكتبات Python
- ✓ `render.yaml` - إعدادات Render
- ✓ `app.py` - Backend معدّل للإنتاج
- ✓ `script.js` - Frontend معدّل

---

## 📋 خطوات النشر

### **الخطوة 1: رفع الكود على GitHub**

```bash
# في مجلد المشروع
git init
git add .
git commit -m "Initial commit - HR Analytics Backend"
git branch -M main

# أنشئ repository جديد على GitHub ثم:
git remote add origin https://github.com/YOUR_USERNAME/hr-analytics-backend.git
git push -u origin main
```

**مهم:** تأكد من رفع كل الملفات خصوصًا:
- `app.py`
- `requirements.txt`
- `render.yaml`

---

### **الخطوة 2: نشر Backend على Render**

#### أ. إنشاء حساب وربط GitHub
1. اذهب إلى [render.com](https://render.com)
2. سجل دخول بحساب GitHub
3. اضغط **"New +"** → **"Web Service"**

#### ب. إعدادات الـ Web Service
- **Repository:** اختر `hr-analytics-backend`
- **Name:** `hr-analytics-api` (أو أي اسم تريد)
- **Environment:** `Python 3`
- **Region:** اختر الأقرب (مثل Frankfurt)
- **Branch:** `main`

#### ج. Build & Start Settings
سيتم اكتشافها تلقائيًا من `render.yaml`، لكن تأكد:
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`

#### د. إعدادات Environment Variables
اضغط **"Advanced"** ثم أضف:
- `ALLOWED_ORIGINS` = `https://YOUR-CLOUDFLARE-PAGES-URL.pages.dev,https://yourdomain.com`
- `PYTHON_VERSION` = `3.11`
- `FLASK_ENV` = `production`

#### هـ. اختر الخطة
- **Free Plan** (كافية للاختبار والاستخدام المحدود)
- اضغط **"Create Web Service"**

#### و. انتظر النشر
- سيأخذ 2-5 دقائق
- بعد النجاح، ستحصل على رابط مثل:
  `https://hr-analytics-api.onrender.com`

---

### **الخطوة 3: تحديث Frontend**

#### أ. تعديل script.js
افتح `script.js` وعدّل السطر 12:

```javascript
const API_BASE = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost' 
    ? 'http://127.0.0.1:8080' 
    : 'https://hr-analytics-api.onrender.com'; // ضع رابط Render هنا
```

#### ب. رفع التحديث على Cloudflare Pages
```bash
# في مجلد المشروع
git add script.js
git commit -m "Update API endpoint to Render"
git push
```

إذا كنت تستخدم Cloudflare Pages مع GitHub:
- سيتم النشر تلقائيًا بعد Push
- راقب التقدم في Cloudflare Dashboard

إذا كنت تستخدم الرفع اليدوي:
- اذهب إلى Cloudflare Pages Dashboard
- اسحب الملفات الجديدة أو ارفعها

---

### **الخطوة 4: تحديث CORS على Render**

بعد نشر Frontend على Cloudflare:

1. اذهب إلى Render Dashboard
2. افتح الـ Web Service
3. اذهب إلى **"Environment"**
4. عدّل `ALLOWED_ORIGINS`:
   ```
   https://your-app.pages.dev,https://yourdomain.com
   ```
5. احفظ وأعد النشر (Deploy)

---

## 🧪 اختبار النظام

### أ. اختبر Backend مباشرة
افتح المتصفح واذهب إلى:
```
https://hr-analytics-api.onrender.com/init-session
```
يجب أن ترى:
```json
{
  "session_token": "...",
  "file_id": "...",
  "expires_in": 7200
}
```

### ب. اختبر Frontend
1. افتح موقعك على Cloudflare Pages
2. ارفع ملف Excel
3. راقب Console في Developer Tools (F12)
4. تأكد من عدم وجود أخطاء CORS

---

## 🔧 إعدادات إضافية (اختياري)

### تفعيل Custom Domain على Render
1. في Render Dashboard → **"Settings"**
2. أضف Custom Domain مثل `api.yourdomain.com`
3. أضف CNAME Record في DNS:
   ```
   Type: CNAME
   Name: api
   Value: hr-analytics-api.onrender.com
   ```

### تحسين الأداء
في `render.yaml` يمكنك زيادة الـ Workers:
```yaml
startCommand: gunicorn app:app --bind 0.0.0.0:$PORT --workers 4 --timeout 180
```

---

## ⚠️ ملاحظات مهمة

### 1. **Render Free Plan**
- يتم إيقاف السيرفر بعد 15 دقيقة من عدم الاستخدام
- أول طلب بعد الإيقاف يأخذ 30-60 ثانية (Cold Start)
- **الحل:** استخدم Paid Plan ($7/شهر) أو استخدم Uptime Monitor

### 2. **حدود الذاكرة**
- Free: 512 MB RAM
- إذا كانت ملفات Excel كبيرة جدًا، قد تحتاج Paid Plan

### 3. **الأمان**
- لا تشارك رابط API الخاص بك علنًا
- استخدم Environment Variables للبيانات الحساسة

---

## 🐛 حل المشاكل الشائعة

### مشكلة: CORS Error
**الحل:**
- تأكد من إضافة رابط Cloudflare في `ALLOWED_ORIGINS`
- أعد نشر Backend بعد التعديل

### مشكلة: Backend Crashed
**الحل:**
- افتح Logs في Render Dashboard
- ابحث عن أخطاء Python
- تأكد من وجود كل المكتبات في `requirements.txt`

### مشكلة: Timeout
**الحل:**
- زد قيمة `--timeout` في gunicorn
- أو استخدم Workers أكثر

---

## 📞 الدعم

إذا واجهت مشاكل:
1. افحص Logs في Render Dashboard → **"Logs"**
2. افحص Console في المتصفح (F12)
3. تأكد من صحة جميع الروابط

---

## ✨ النتيجة النهائية

بعد اتباع الخطوات:
- ✅ Frontend يعمل على Cloudflare Pages
- ✅ Backend يعمل على Render
- ✅ الاتصال بينهما عبر HTTPS
- ✅ CORS مضبوط بشكل صحيح
- ✅ نظام جاهز للاستخدام الفعلي

---

**تم إعداد هذا الدليل بواسطة GitHub Copilot**
