# 📊 HR Analytics System - نظام تحليل الموارد البشرية

نظام تحليل متقدم للموارد البشرية يعمل على **turki20.sa** مع معالجة ذكية لملفات Excel وعرض تحليلات تفاعلية.

---

## 🏗️ المعمارية

```
Frontend (HTML/CSS/JS)
    ↓
Cloudflare Pages (turki20.sa)
    ↓
Backend API (Python/Flask)
    ↓
Render.com Hosting
```

---

## ✨ المميزات

### Frontend
- 🎨 واجهة عربية احترافية
- 📱 متجاوبة مع جميع الأجهزة
- 📊 رسوم بيانية تفاعلية (Chart.js)
- 🔍 فلاتر متقدمة للبيانات
- 🗺️ تحليل جغرافي للمناطق السعودية

### Backend
- 🐍 Python Flask
- 📁 معالجة ملفات Excel (pandas)
- 🔒 نظام Session آمن
- 🌐 CORS مضبوط للإنتاج
- ⚡ معالجة سريعة للبيانات

---

## 📁 هيكل المشروع

```
hr/
├── Frontend Files (Cloudflare Pages)
│   ├── index.html          # الواجهة الرئيسية
│   ├── script.js           # منطق التطبيق
│   └── styles.css          # التصميم
│
├── Backend Files (Render)
│   ├── app.py              # Flask API
│   ├── requirements.txt    # مكتبات Python
│   └── render.yaml         # إعدادات Render
│
├── Deployment Guides
│   ├── DEPLOYMENT_TURKI20.md  # دليل شامل
│   ├── QUICK_START.md         # خطوات سريعة
│   └── test_backend.html      # أداة اختبار
│
└── Configuration
    ├── .gitignore          # ملفات مستبعدة
    └── README.md           # هذا الملف
```

---

## 🚀 التثبيت والنشر

### المتطلبات
- Python 3.11+
- Git
- حساب على [Render.com](https://render.com)
- حساب على [Cloudflare Pages](https://pages.cloudflare.com)
- نطاق turki20.sa (مضبوط على Cloudflare)

### التطوير المحلي

1. **تشغيل Backend:**
```bash
cd /Users/turki/Desktop/hr
python3 app.py
```
السيرفر يعمل على `http://127.0.0.1:8080`

2. **فتح Frontend:**
افتح `index.html` في المتصفح مباشرة

3. **الاختبار:**
- ارفع ملف Excel
- راقب Console للتأكد من عدم وجود أخطاء

### النشر على الإنتاج

اتبع الخطوات في `QUICK_START.md` أو `DEPLOYMENT_TURKI20.md`

**باختصار:**
1. رفع Backend على Render
2. تحديث `script.js` برابط Render
3. رفع Frontend على Cloudflare Pages
4. اختبار من `https://turki20.sa`

---

## 🔧 الإعدادات

### Environment Variables (Render)
```env
ALLOWED_ORIGINS=https://turki20.sa,https://www.turki20.sa,http://localhost:8080
FLASK_ENV=production
PYTHON_VERSION=3.11
```

### API Endpoint (script.js)
```javascript
const API_BASE = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost' 
    ? 'http://127.0.0.1:8080' 
    : 'https://YOUR-RENDER-APP.onrender.com';
```

---

## 📊 API Endpoints

### `GET /init-session`
إنشاء جلسة جديدة
```json
Response: {
  "session_token": "abc123...",
  "file_id": "xyz789...",
  "expires_in": 7200
}
```

### `POST /upload`
رفع ملف Excel
```
Headers: X-Session-Token
Body: FormData with 'file'
```

### `POST /analytics`
تحليل البيانات
```json
Body: {
  "file_id": "...",
  "sheet": "Sheet1"
}
```

### `POST /analyze-custom`
تحليل مخصص بأعمدة محددة
```json
Body: {
  "file_id": "...",
  "sheet": "Sheet1",
  "dept_column": "الإدارة",
  "rating_columns": ["التقييم1", "التقييم2"]
}
```

### `GET /status`
حالة السيرفر
```json
Response: {
  "status": "running",
  "fast": true
}
```

---

## 🧪 الاختبار

### اختبار Backend
```bash
# اختبار محلي
curl http://127.0.0.1:8080/init-session

# اختبار على Render
curl https://your-app.onrender.com/init-session
```

### اختبار Frontend
افتح `test_backend.html` في المتصفح لاختبار شامل:
- الاتصال
- Session
- CORS
- معلومات البيئة

---

## 🔒 الأمان

- ✅ نظام Session مؤقت (2 ساعات)
- ✅ CORS محدد بنطاقات معينة
- ✅ Rate limiting على الـ uploads
- ✅ تحقق من IP
- ✅ SSL/TLS تلقائي
- ✅ لا يتم حفظ البيانات بشكل دائم

---

## 📈 الأداء

### Render Free Plan
- ✅ مجاني بالكامل
- ⚠️ Cold Start: 30-60 ثانية بعد عدم الاستخدام
- 💾 512 MB RAM
- 🔄 Sleep بعد 15 دقيقة من عدم النشاط

### تحسينات مقترحة
- Render Paid Plan ($7/شهر) → لا Cold Start
- Cron Job → يبقي السيرفر نشط
- Caching → تسريع الاستجابة

---

## 🐛 المشاكل الشائعة

### "الخادم غير متاح"
**السبب:** رابط API خاطئ أو Backend متوقف  
**الحل:** تحقق من `script.js` وتأكد Backend شغال

### CORS Error
**السبب:** النطاق غير مسموح  
**الحل:** أضف النطاق في `ALLOWED_ORIGINS` على Render

### 503 Service Unavailable
**السبب:** Cold Start (Free Plan)  
**الحل:** انتظر 30-60 ثانية

### معالجة بطيئة
**السبب:** ملف Excel كبير جداً  
**الحل:** Render Paid Plan أو تقليل حجم الملف

---

## 📚 المكتبات المستخدمة

### Backend
- Flask 3.0.0
- flask-cors 4.0.0
- pandas 2.1.4
- numpy 1.26.2
- openpyxl 3.1.2
- gunicorn 21.2.0

### Frontend
- Chart.js 4.x
- Font Awesome 6.x
- Google Fonts (Cairo)

---

## 🤝 المساهمة

لتحسين المشروع:
1. Fork المشروع
2. أنشئ Branch جديد
3. قم بالتعديلات
4. Submit Pull Request

---

## 📄 الترخيص

هذا المشروع خاص بـ turki20.sa

---

## 📞 الدعم

للمساعدة:
1. راجع `DEPLOYMENT_TURKI20.md`
2. استخدم `test_backend.html`
3. افحص Logs في Render
4. افحص Console في المتصفح

---

## 🎯 خارطة الطريق

- [ ] إضافة تحليلات إضافية
- [ ] دعم ملفات CSV
- [ ] تصدير التقارير PDF
- [ ] لوحة تحكم متقدمة
- [ ] نظام مستخدمين
- [ ] حفظ التقارير

---

**✨ تم التطوير بواسطة GitHub Copilot**

**🌐 يعمل على: https://turki20.sa**
