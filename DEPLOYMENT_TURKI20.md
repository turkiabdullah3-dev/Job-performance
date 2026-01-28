# 🚀 دليل النشر النهائي - turki20.sa
## Backend Python على Render + Frontend على Cloudflare Pages

---

## 📌 المعمارية المستخدمة

```
المستخدم
    ↓
turki20.sa (Cloudflare Pages)
    ↓ [HTTP API Calls]
Backend على Render (Python Flask)
```

**لماذا هذا الحل؟**
- ✅ Cloudflare Pages لا يدعم Python (ملفات ثابتة فقط)
- ✅ Render يدعم Python/Flask بشكل كامل
- ✅ CORS يسمح بالتواصل بين النطاقين
- ✅ SSL تلقائي على الطرفين
- ✅ النطاق turki20.sa لا يتغير

---

## ⚡ الخطوات السريعة

### **1️⃣ نشر Backend على Render**

#### أ. رفع على GitHub (إذا لم يتم بعد)
```bash
cd /Users/turki/Desktop/hr

git init
git add app.py requirements.txt render.yaml .gitignore
git commit -m "Backend ready for Render"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/hr-backend.git
git push -u origin main
```

#### ب. إنشاء Web Service على Render
1. اذهب إلى [render.com](https://render.com)
2. سجل دخول بـ GitHub
3. **New +** → **Web Service**
4. اختر الـ Repository: `hr-backend`
5. الإعدادات:
   - **Name:** `turki20-hr-api` (أو أي اسم)
   - **Environment:** `Python 3`
   - **Region:** `Frankfurt` (الأقرب)
   - **Branch:** `main`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`

6. **Environment Variables** (Advanced):
   ```
   ALLOWED_ORIGINS=https://turki20.sa,https://www.turki20.sa,http://localhost:8080,http://127.0.0.1:8080
   FLASK_ENV=production
   PYTHON_VERSION=3.11
   ```

7. اضغط **Create Web Service**

8. انتظر 3-5 دقائق حتى ينتهي النشر

9. **انسخ الرابط** الناتج، مثل:
   ```
   https://turki20-hr-api.onrender.com
   ```

---

### **2️⃣ تحديث Frontend**

#### أ. تعديل script.js
افتح `/Users/turki/Desktop/hr/script.js` السطر 13:

```javascript
const API_BASE = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost' 
    ? 'http://127.0.0.1:8080' 
    : 'https://turki20-hr-api.onrender.com'; // ضع الرابط من Render
```

**مثال بعد التعديل:**
```javascript
const API_BASE = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost' 
    ? 'http://127.0.0.1:8080' 
    : 'https://turki20-hr-api.onrender.com';
```

#### ب. رفع على Cloudflare Pages

**الطريقة 1: Git Deployment (الموصى بها)**
```bash
cd /Users/turki/Desktop/hr

# إذا كان عندك repo منفصل للـ Frontend
git add script.js
git commit -m "Update API endpoint to Render"
git push
```
Cloudflare Pages سيكتشف التحديث ويعيد النشر تلقائياً.

**الطريقة 2: الرفع اليدوي**
1. اذهب إلى Cloudflare Pages Dashboard
2. افتح مشروع `turki20.sa`
3. اضغط على **Create a new deployment**
4. ارفع الملفات:
   - `index.html`
   - `script.js` (المحدث)
   - `styles.css`
   - أي ملفات أخرى

---

### **3️⃣ الاختبار**

#### أ. اختبر Backend مباشرة
افتح المتصفح:
```
https://turki20-hr-api.onrender.com/init-session
```

**النتيجة المتوقعة:**
```json
{
  "session_token": "abc123...",
  "file_id": "xyz789...",
  "expires_in": 7200
}
```

#### ب. اختبر الموقع الكامل
1. افتح `https://turki20.sa`
2. ارفع ملف Excel
3. افتح **Console** (F12 → Console)
4. تأكد من عدم وجود أخطاء CORS
5. تأكد من ظهور البيانات والرسوم البيانية

---

## 🔧 ضبط CORS (مهم جداً)

إذا ظهرت أخطاء CORS:

### في Render Dashboard:
1. اذهب إلى **Environment**
2. عدّل `ALLOWED_ORIGINS`:
   ```
   https://turki20.sa,https://www.turki20.sa
   ```
3. **Save Changes**
4. اضغط **Manual Deploy** → **Deploy latest commit**

### اختبار CORS:
افتح Console في المتصفح وجرب:
```javascript
fetch('https://turki20-hr-api.onrender.com/init-session')
  .then(r => r.json())
  .then(d => console.log(d))
  .catch(e => console.error(e))
```

إذا نجح = CORS شغال ✅

---

## 🌐 Custom Domain (اختياري)

### لاستخدام api.turki20.sa بدلاً من onrender.com:

#### في Cloudflare DNS:
أضف CNAME Record:
```
Type: CNAME
Name: api
Target: turki20-hr-api.onrender.com
Proxy: ✅ (On)
```

#### في Render:
1. اذهب إلى **Settings** → **Custom Domains**
2. أضف: `api.turki20.sa`
3. انتظر التحقق (5-10 دقائق)

#### في script.js:
```javascript
const API_BASE = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost' 
    ? 'http://127.0.0.1:8080' 
    : 'https://api.turki20.sa';
```

---

## ⚠️ ملاحظات مهمة

### 1. **Render Free Plan**
- ✅ مجاني بالكامل
- ⚠️ يتوقف بعد 15 دقيقة من عدم الاستخدام
- ⚠️ أول طلب بعد التوقف يأخذ 30-60 ثانية (Cold Start)
- 💡 الحل: Paid Plan ($7/شهر) أو استخدام Cron Job للإبقاء على السيرفر نشط

### 2. **حدود الموارد**
- Free: 512 MB RAM
- إذا كانت ملفات Excel كبيرة (>10 MB)، قد تحتاج Paid Plan

### 3. **التطوير المحلي**
للعمل على الجهاز:
```bash
cd /Users/turki/Desktop/hr
python3 app.py
# السيرفر يعمل على http://127.0.0.1:8080
```
افتح `index.html` في المتصفح → سيتصل تلقائياً بـ localhost

---

## 🐛 حل المشاكل

### مشكلة: CORS Error في Console
```
Access to fetch at 'https://...' from origin 'https://turki20.sa' has been blocked by CORS
```
**الحل:**
1. تأكد من إضافة `https://turki20.sa` في `ALLOWED_ORIGINS` على Render
2. أعد نشر Backend
3. امسح الـ Cache في المتصفح (Ctrl+Shift+R)

### مشكلة: Backend يعرض 503 Service Unavailable
**السبب:** Cold Start (Free Plan)
**الحل:** انتظر 30-60 ثانية وأعد المحاولة

### مشكلة: الموقع يقول "الخادم غير متاح"
**الحل:**
1. تأكد من أن رابط API في `script.js` صحيح
2. افتح رابط Backend مباشرة للتأكد أنه يعمل
3. تحقق من Console للأخطاء

### مشكلة: Backend Crashed
**الحل:**
1. اذهب إلى Render Dashboard → **Logs**
2. ابحث عن أخطاء Python
3. تأكد من وجود كل المكتبات في `requirements.txt`

---

## ✅ Checklist النهائي

قبل الإطلاق الفعلي، تأكد من:

- [ ] Backend منشور على Render ويعمل
- [ ] `/init-session` يستجيب بنجاح
- [ ] CORS يسمح بطلبات من `turki20.sa`
- [ ] `script.js` يحتوي على رابط API الصحيح
- [ ] Frontend محدّث على Cloudflare Pages
- [ ] اختبار رفع ملف Excel بنجاح
- [ ] الرسوم البيانية تظهر بشكل صحيح
- [ ] لا توجد أخطاء في Console
- [ ] SSL شغال على الطرفين (قفل أخضر 🔒)

---

## 📊 النتيجة النهائية

```
✅ المستخدم يفتح: https://turki20.sa
✅ Cloudflare Pages يعرض الواجهة
✅ JavaScript يرسل طلبات إلى: https://turki20-hr-api.onrender.com
✅ Flask Backend يعالج البيانات
✅ النتائج ترجع للواجهة
✅ الرسوم البيانية تظهر
✅ كل شيء يعمل على نطاق turki20.sa
```

---

## 📞 دعم إضافي

**إذا واجهت أي مشكلة:**
1. افحص Logs في Render Dashboard
2. افحص Console في المتصفح (F12)
3. تأكد من CORS Settings
4. جرّب من متصفح آخر أو نافذة خفية

---

**✨ تم الإعداد بنجاح!**

نطاقك turki20.sa جاهز مع Backend قوي على Render
