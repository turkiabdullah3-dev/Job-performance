# 📊 نظام تحليل الموارد البشرية - HR Analytics

نظام متقدم لتحليل بيانات الموارد البشرية باستخدام الذكاء الاصطناعي والتعلم الآلي.

## 🚀 الميزات الرئيسية

- ✅ **تسجيل دخول آمن** - مصادقة قوية مع bcrypt
- ✅ **رفع ملفات Excel** - معالجة سريعة للبيانات الضخمة
- ✅ **تحليل ذكي بـ AI** - توقعات وتصنيفات باستخدام scikit-learn
- ✅ **رسوم بيانية تفاعلية** - عرض النتائج بشكل مرئي
- ✅ **توصيات ذكية** - اقتراحات قابلة للتنفيذ

## 🛠️ التشغيل المحلي

```bash
# 1. تثبيت المتطلبات
pip3 install -r requirements.txt

# 2. التشغيل
python3 app.py

# 3. افتح المتصفح
http://127.0.0.1:8002
```

## 📝 بيانات تسجيل الدخول

```
اسم المستخدم: admin
كلمة المرور: admin123456
```

## 🧠 نماذج الذكاء الاصطناعي المستخدمة

| النموذج | الوصف |
|---------|-------|
| **Gradient Boosting** | التنبؤ بالأداء المستقبلي |
| **K-Means Clustering** | تصنيف الموظفين |
| **Statistical Analysis** | التحليل الإحصائي المتقدم |
| **Anomaly Detection** | كشف الحالات الشاذة |

## 📁 هيكل الملفات

```
hr/
├── app.py           # الـ backend الرئيسي
├── script.js        # الـ frontend
├── index.html       # صفحة المرة الأولى
├── styles.css       # التصميم
└── requirements.txt # المكتبات
```

## 🔐 الأمان

- كلمات مرور مشفرة بـ bcrypt
- جلسات آمنة مع timeout 2 ساعة
- التحقق من IP والتوكن
- حد أقصى لعدد محاولات تسجيل الدخول

## 📊 API Endpoints

| الـ Endpoint | الوصف |
|------------|-------|
| `POST /login` | تسجيل الدخول |
| `POST /upload` | رفع الملف |
| `POST /ai-analyze` | التحليل الذكي |
| `POST /analyze-custom` | تحليل مخصص |
| `GET /auth-check` | التحقق من الجلسة |

## 🔧 التطوير

```bash
# تحديث المكتبات
pip3 install -r requirements.txt

# مسح الـ cache
find . -type d -name __pycache__ -exec rm -r {} +

# اختبار الكود
python3 -m py_compile app.py
node --check script.js
```

---

**تم التطوير بواسطة:** turkiabdullah3
**آخر تحديث:** 6 فبراير 2026

### 5. Create Systemd Service
```bash
sudo cp hr-analytics.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable hr-analytics
sudo systemctl start hr-analytics
```

### 6. Setup SSL
```bash
sudo certbot --nginx -d analysis.turki20.sa -d www.analysis.turki20.sa
```

---

## Service Management

```bash
# View status
sudo systemctl status hr-analytics

# Restart service
sudo systemctl restart hr-analytics

# View logs
sudo journalctl -u hr-analytics -f

# Stop service
sudo systemctl stop hr-analytics
```

---

## File Structure

```
/var/www/hr-analytics/
├── app.py                    # Original Flask app (development)
├── production_server.py      # Production Flask app (use this)
├── index.html               # Main HTML page
├── styles.css               # Styling
├── script.js                # Frontend JavaScript
├── nginx.conf               # Nginx configuration
├── deploy.sh                # Deployment script
└── README.md               # This file

/var/log/hr-analytics/
├── app.log                  # Application logs
└── error.log               # Error logs
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main page |
| `/init-session` | GET | Initialize session |
| `/upload` | POST | Upload Excel file |
| `/progress` | GET | Get processing progress |
| `/analytics` | POST | Get analytics results |
| `/get-columns` | POST | Get file columns |
| `/analyze-custom` | POST | Custom analysis |
| `/clear` | POST | Clear data |
| `/status` | GET | Health check |
| `/health` | GET | Load balancer health |

---

## Troubleshooting

### App not starting
```bash
# Check logs
sudo journalctl -u hr-analytics -e

# Check port
sudo lsof -i :8080
```

### Nginx errors
```bash
# Test config
sudo nginx -t

# Check nginx logs
sudo tail -f /var/log/nginx/error.log
```

### SSL certificate issues
```bash
# Renew certificate
sudo certbot renew

# Test renewal
sudo certbot renew --dry-run
```

### Domain not resolving
- Wait 24-48 hours for DNS propagation
- Check domain DNS settings
- Verify A record points to server IP

---

## Security Notes

1. **Keep SSL certificates renewed** - Auto-renewal is set up
2. **Firewall** - UFW is configured to allow only needed ports
3. **Sessions** - Automatically expire after 2 hours
4. **Rate limiting** - Built into the application

---

## Support

For issues:
1. Check application logs: `sudo journalctl -u hr-analytics -f`
2. Check nginx logs: `sudo tail -f /var/log/nginx/error.log`
3. Verify service status: `sudo systemctl status hr-analytics`

---

## Ministry of Education - KSA

This system is configured for the Ministry of Education's Performance Management department.
All data processing is done locally on the server.

