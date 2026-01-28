#!/bin/bash

# ✅ Pre-Deployment Checklist للتحقق قبل النشر

echo "======================================"
echo "🔍 فحص ما قبل النشر - turki20.sa"
echo "======================================"
echo ""

# التحقق من الملفات الأساسية
echo "📁 التحقق من الملفات الأساسية..."

files=("app.py" "requirements.txt" "render.yaml" "index.html" "script.js" "styles.css")
all_files_exist=true

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file موجود"
    else
        echo "  ❌ $file مفقود!"
        all_files_exist=false
    fi
done

echo ""

# التحقق من محتوى requirements.txt
echo "📦 التحقق من requirements.txt..."
if grep -q "Flask" requirements.txt && grep -q "flask-cors" requirements.txt && grep -q "gunicorn" requirements.txt; then
    echo "  ✅ requirements.txt يحتوي على المكتبات الأساسية"
else
    echo "  ⚠️  تحقق من requirements.txt"
fi

echo ""

# التحقق من CORS في app.py
echo "🌐 التحقق من CORS..."
if grep -q "ALLOWED_ORIGINS" app.py; then
    echo "  ✅ CORS مضبوط في app.py"
else
    echo "  ⚠️  CORS قد يحتاج ضبط"
fi

echo ""

# التحقق من API_BASE في script.js
echo "🔗 التحقق من API endpoint..."
if grep -q "API_BASE" script.js; then
    echo "  ✅ API_BASE موجود في script.js"
    echo "  💡 تذكر: حدّث الرابط بعد النشر على Render"
else
    echo "  ❌ API_BASE مفقود في script.js"
fi

echo ""

# التحقق من Python
echo "🐍 التحقق من Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "  ✅ $PYTHON_VERSION"
else
    echo "  ❌ Python غير مثبت"
fi

echo ""

# التحقق من Git
echo "📝 التحقق من Git..."
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version)
    echo "  ✅ $GIT_VERSION"
    
    if [ -d ".git" ]; then
        echo "  ✅ Git repository مهيأ"
    else
        echo "  ⚠️  Git repository غير مهيأ - شغّل: git init"
    fi
else
    echo "  ❌ Git غير مثبت"
fi

echo ""

# اختبار Backend محلياً (اختياري)
echo "🧪 اختبار Backend المحلي..."
if curl -s http://127.0.0.1:8080/status &> /dev/null; then
    echo "  ✅ Backend يعمل محلياً"
else
    echo "  ⚠️  Backend غير شغال محلياً (طبيعي إذا لم تشغله)"
fi

echo ""
echo "======================================"
echo "📋 الخطوات التالية:"
echo "======================================"
echo ""
echo "1️⃣  إذا كانت كل الملفات ✅، جاهز للنشر!"
echo ""
echo "2️⃣  رفع على GitHub:"
echo "    git add ."
echo "    git commit -m 'Ready for deployment'"
echo "    git push"
echo ""
echo "3️⃣  نشر على Render:"
echo "    https://render.com → New Web Service"
echo ""
echo "4️⃣  بعد النشر:"
echo "    - انسخ رابط Render"
echo "    - حدّث script.js (السطر 13)"
echo "    - ارفع على Cloudflare Pages"
echo ""
echo "📖 للتفاصيل: راجع QUICK_START.md"
echo ""
echo "✨ بالتوفيق!"
echo "======================================"
