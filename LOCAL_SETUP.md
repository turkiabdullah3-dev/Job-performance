# تشغيل محلي مع الوصول عبر الدومين

## طريقة التشغيل

### الطريقة الأولى: تشغيل محلي (localhost فقط)
```bash
cd /Users/turki/Desktop/hr
chmod +x run-local.sh
./run-local.sh start
```
ثم افتح: http://localhost:8080

---

### الطريقة الثانية: تشغيل مع ngrok (وصول عام)
```bash
cd /Users/turki/Desktop/hr
./run-local.sh tunnel
```

هذا سيُنشئ رابط عام مثل:
- https://abc123.ngrok.io

**للوصول عبر الدومين:** يجب أن يكون لديك حساب ngrok مدفوع.

---

## الأوامر المتاحة

| الأمر | الوصف |
|-------|-------|
| `./run-local.sh start` | تشغيل الخادم محلياً فقط |
| `./run-local.sh tunnel` | تشغيل + إنشاء tunnel عام |
| `./run-local.sh stop` | إيقاف جميع الخدمات |
| `./run-local.sh restart` | إعادة تشغيل |
| `./run-local.sh status` | فحص الحالة |
| `./run-local.sh logs` | عرض السجلات |

---

## المتطلبات

### تثبيت Homebrew (إن لم يكن مثبتاً)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### تثبيت ngrok
```bash
brew install ngrok
```

أو عبر الموقع: https://ngrok.com/download

---

## للوصول عبر الدومين الخاص

### الخيار 1: ngrok (مدفوع)
```bash
ngrok http 8080 --domain=analysis.turki20.sa
```
متطلب: اشتراك ngrok مدفوع

### الخيار 2: Cloudflare Tunnel (مجاني)
```bash
# تثبيت cloudflared
brew install cloudflare/cloudflare/cloudflared

# تشغيل
cloudflared tunnel --url http://localhost:8080
```

### الخيار 3: localtunnel
```bash
npm install -g localtunnel
lt --port 8080 --subdomain analysis
```

---

## للتحكم بالخدمة

```bash
# إيقاف
pkill -f "python3 production_server.py"

# أو
lsof -ti:8080 | xargs kill

# فحص المنافذ
lsof -i :8080
```

---

## للتطوير

```bash
# تشغيل مع live reload
cd /Users/turki/Desktop/hr
python3 -m flask --app production_server run --host 0.0.0.0 --port 8080 --debug
```

---

## ملاحظات

- الخادم يعمل على المنفذ 8080
- مجلد المشروع: `/Users/turki/Desktop/hr`
- السجلات: `/tmp/ngrok.log`
- PID: `/tmp/hr-analytics.pid`

