#!/usr/bin/env python3
"""
Production-ready Flask server for HR Analytics System
Configured for domain: analysis.turki20.sa
"""

import os
import ssl
import sys
from datetime import datetime, timedelta
from functools import wraps
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/hr-analytics/app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_cors import CORS
import pandas as pd
import numpy as np
import io
import threading
import hashlib
import secrets
import re

app = Flask(__name__, static_folder='.')

# ============= CONFIGURATION =============
DOMAIN_NAME = 'analysis.turki20.sa'
ALLOWED_ORIGINS = [
    'https://analysis.turki20.sa',
    'https://www.analysis.turki20.sa',
    'http://localhost:8080',
    'http://127.0.0.1:8080'
]

# Security settings
SESSION_TIMEOUT = timedelta(hours=2)
MAX_SESSIONS_PER_IP = 10
MAX_SESSIONS_TOTAL = 100
MAX_UPLOADS_PER_SESSION = 20
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MB

app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Session & Storage with enhanced security
sessions = {}
files = {}
analytics_cache = {}
progress = {}
lock = threading.Lock()

# Saudi Regions with coordinates
SAUDI_REGIONS = {
    'الرياض': {'lat': 24.7136, 'lng': 46.6753, 'color': '#00d9ff'},
    'مكة': {'lat': 21.4225, 'lng': 39.8262, 'color': '#7c3aed'},
    'المدينة': {'lat': 24.5247, 'lng': 39.5692, 'color': '#ec4899'},
    'الشرقية': {'lat': 26.2361, 'lng': 50.1971, 'color': '#f59e0b'},
    'القصيم': {'lat': 26.1292, 'lng': 46.7103, 'color': '#06b6d4'},
    'عسير': {'lat': 18.2155, 'lng': 42.5074, 'color': '#10b981'},
    'تبوك': {'lat': 28.3896, 'lng': 36.5624, 'color': '#f97316'},
    'حائل': {'lat': 27.5373, 'lng': 41.6972, 'color': '#8b5cf6'},
    'الجوف': {'lat': 29.7865, 'lng': 40.0836, 'color': '#6366f1'},
    'نجران': {'lat': 17.4904, 'lng': 43.9886, 'color': '#14b8a6'},
    'الباحة': {'lat': 19.9864, 'lng': 41.4695, 'color': '#eab308'},
    'جازان': {'lat': 16.8892, 'lng': 42.5521, 'color': '#22c55e'},
    'الأحساء': {'lat': 25.3860, 'lng': 49.5832, 'color': '#f43f5e'},
}


def set_security_headers(response):
    """Apply security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    
    # HSTS for HTTPS
    if request.is_secure:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    return response


@app.after_request
def after_request(response):
    """Apply security headers and CORS"""
    # CORS headers
    origin = request.headers.get('Origin', '')
    if origin in ALLOWED_ORIGINS:
        response.headers['Access-Control-Allow-Origin'] = origin
    
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Session-Token, X-Requested-With'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Max-Age'] = '3600'
    
    return set_security_headers(response)


def validate_session(f):
    """Session validation decorator"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('X-Session-Token')
        
        with lock:
            if not token or token not in sessions:
                return jsonify({'error': 'جلسة غير صالحة', 'code': 'INVALID_SESSION'}), 401
            
            session_data = sessions[token]
            
            if session_data['expires'] < datetime.now():
                del sessions[token]
                return jsonify({'error': 'انتهت صلاحية الجلسة', 'code': 'SESSION_EXPIRED'}), 401
            
            if session_data['ip'] != request.remote_addr:
                # Allow for proxy setups
                if request.headers.get('X-Forwarded-For', '').split(',')[0].strip() != session_data['ip']:
                    return jsonify({'error': 'جلسة غير صالحة', 'code': 'INVALID_IP'}), 401
        
        return f(*args, **kwargs)
    return decorated


def normalize_text(text):
    """Normalize text for fuzzy matching"""
    if not text:
        return ''
    
    text = str(text).strip()
    arabic_diacritics = re.compile('[\u064B-\u065F\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED]')
    text = arabic_diacritics.sub('', text)
    
    replacements = {
        'ة': 'ه', 'ہ': 'ه', 'ھ': 'ه', 'ە': 'ه',
        'ي': 'ي', 'ى': 'ي', 'ئ': 'ي', 'ؤ': 'و',
        'أ': 'ا', 'إ': 'ا', 'آ': 'ا',
        'ك': 'ك', 'گ': 'ك', 'پ': 'ب', 'چ': 'ج', 'ژ': 'ز', 'ف': 'ف',
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text.lower()


def match_region(region_name):
    """Enhanced fuzzy match for region names"""
    if not region_name or region_name == 'nan':
        return None
    
    region_str = str(region_name).strip()
    region_normalized = normalize_text(region_str)
    
    REGION_NAME_MAPPINGS = {
        'الرياض': ['الرياض', 'Riyadh', 'riyadh', 'RIYADH', 'منطقة الرياض', 'Central', 'KSA_Riyadh', 'رياض', 'الرياض Region', 'الرياضregion'],
        'مكة': ['مكة', 'Makkah', 'makkah', 'MAKKAH', ' Mecca', 'منطقة مكة', 'مكة المكرمة', 'Makkah Al-Mukerramah', 'Western', 'مكه', 'جدة', 'Jeddah', 'jeddah', 'Western Region'],
        'المدينة': ['المدينة', 'Medina', 'medina', 'MEDINA', ' Medina', 'المدينة المنورة', 'Medina Munawarah', 'Al-Madinah', 'Madinah', 'Madina', 'المنورة', 'المدينه'],
        'الشرقية': ['الشرقية', 'Eastern', 'eastern', 'EASTERN', 'المنطقة الشرقية', 'Eastern Province', 'Dammam', 'damman', 'الدمام', 'الظهران', 'الخبر', 'القطيف', 'الجبيل', 'Ras Tanura', 'Dahran', 'Dhahran', 'الشرقيه'],
        'القصيم': ['القصيم', 'Qassim', 'qassim', 'QASSIM', 'Al-Qassim', 'Alqassim', 'بريده', 'Buraydah', 'buraydah', 'الرس', 'عنيزة', 'بريدة', 'القصييم'],
        'عسير': ['عسير', 'Asir', 'asir', 'ASIR', 'Aseer', 'Abha', 'abha', '南部地区', 'Khamis Mushait', 'خميس مشيط', 'ابها', 'محايل', 'النماص', 'تنومة', 'عسير Region', 'ابها Region'],
        'تبوك': ['تبوك', 'Tabuk', 'tabuk', 'TABUK', 'Tabook', 'تبوك Region', 'تبوكregion', 'طبرجل', 'البدع', 'حقل', 'طبرجل Region'],
        'حائل': ['حائل', 'Hail', 'hail', 'HAIL', 'Hael', "Ha'il", ' Hail', 'حائل Region', 'حائلregion', 'الشنان', 'الغزالة'],
        'الجوف': ['الجوف', 'Jawf', 'jawf', 'JAWF', 'Al-Jawf', 'Aljawf', 'Sakaka', 'sakaka', 'سكاكا', 'القريات', 'رفحا', 'دومة الجندل', 'الجوف Region', 'الجوفregion'],
        'نجران': ['نجران', 'Najran', 'najran', 'NAJRAN', 'Najrān', ' Najran', 'نجران Region', 'نجرانregion', 'ابها', 'hubuna', 'حبونا'],
        'الباحة': ['الباحة', 'Baha', 'baha', 'BAHA', 'Al-Baha', 'Albahah', 'Bahah', 'الباحة Region', 'الباحةregion', 'بلجرشي', 'المخواة', 'قلوة'],
        'جازان': ['جازان', 'Jazan', 'jazan', 'JAZAN', 'Gizan', 'gizan', 'Jizan', 'جيزان', 'جازان Region', 'جازانregion', 'صبيا', 'أحد المسارحة', 'الفرصة', 'الدرب'],
        'الأحساء': ['الأحساء', 'Ahsa', 'ahsa', 'AHSA', 'Al-Ahsa', 'Alahsa', 'Hofuf', 'hofuf', 'Hasa', 'الهفوف', 'الأحساء Region', 'الأحساءregion', 'الدمام', 'ommel'],
    }
    
    for saudi_region, variations in REGION_NAME_MAPPINGS.items():
        for variation in variations:
            variation_normalized = normalize_text(variation)
            if variation_normalized in region_normalized or region_normalized in variation_normalized:
                return saudi_region
    
    if len(region_normalized) >= 3:
        for saudi_region in SAUDI_REGIONS.keys():
            saudi_normalized = normalize_text(saudi_region)
            if saudi_normalized[:4] in region_normalized:
                return saudi_region
    
    return None


def convert_rating(val):
    """Convert rating value to numeric"""
    try:
        if pd.isna(val):
            return None
        
        if isinstance(val, (int, float, np.integer, np.floating)):
            num = float(val)
        else:
            val_str = str(val).replace('%', '').replace(',', '.').strip()
            try:
                num = float(val_str)
            except:
                text = val_str.lower()
                if 'ممتاز' in text or 'excellent' in text:
                    return 5.0
                elif 'جيد جداً' in text or 'very good' in text:
                    return 4.5
                elif 'جيد' in text or 'good' in text:
                    return 4.0
                elif 'متوسط' in text or 'fair' in text or 'average' in text:
                    return 3.0
                elif 'ضعيف' in text or 'poor' in text:
                    return 2.0
                return None
        
        if 1 <= num <= 5:
            return num
        elif 0 <= num <= 1:
            return num * 4 + 1
        elif 1 < num <= 10:
            return (num / 10) * 4 + 1
        elif 10 < num <= 100:
            return (num / 100) * 4 + 1
        elif num > 100:
            return min((num / 100) * 4 + 1, 5.0)
        
        return None
    except:
        return None


# ============= ROUTES =============

@app.route('/')
def index():
    """Serve main page"""
    return send_from_directory('.', 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    if os.path.exists(path):
        return send_from_directory('.', path)
    return jsonify({'error': 'Not found'}), 404


@app.route('/init-session', methods=['GET', 'OPTIONS'])
def init_session():
    """Initialize secure session"""
    if request.method == 'OPTIONS':
        return make_response('', 200)
    
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
    
    with lock:
        now = datetime.now()
        
        # Clean expired sessions
        expired = [t for t, data in sessions.items() 
                  if isinstance(data, dict) and data.get('expires', now) < now]
        for t in expired:
            del sessions[t]
        
        # Check limits
        if len(sessions) >= MAX_SESSIONS_TOTAL:
            return jsonify({'error': 'عدد الجلسات الكامل', 'code': 'MAX_SESSIONS'}), 429
        
        ip_sessions = sum(1 for data in sessions.values() 
                         if isinstance(data, dict) and data.get('ip') == client_ip)
        
        if ip_sessions >= MAX_SESSIONS_PER_IP:
            return jsonify({'error': 'عدد الجلسات لهذا IP Full', 'code': 'MAX_IP_SESSIONS'}), 429
        
        token = secrets.token_urlsafe(32)
        sessions[token] = {
            'created': now,
            'expires': now + SESSION_TIMEOUT,
            'ip': client_ip,
            'uploads': 0
        }
    
    logger.info(f"Session created for IP: {client_ip}")
    return jsonify({'session_token': token})


@app.route('/upload', methods=['POST'])
@validate_session
def upload():
    """Handle file upload"""
    token = request.headers.get('X-Session-Token')
    
    with lock:
        session_data = sessions[token]
        if session_data['uploads'] >= MAX_UPLOADS_PER_SESSION:
            return jsonify({'error': 'تجاوز حد الرفع', 'code': 'MAX_UPLOADS'}), 429
        session_data['uploads'] += 1
    
    if 'file' not in request.files:
        return jsonify({'error': 'لا يوجد ملف', 'code': 'NO_FILE'}), 400
    
    file = request.files['file']
    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({'error': 'ملفات Excel فقط', 'code': 'INVALID_TYPE'}), 400
    
    file_bytes = file.read()
    if not file_bytes:
        return jsonify({'error': 'ملف فارغ', 'code': 'EMPTY_FILE'}), 400
    
    file_id = hashlib.sha256(file_bytes).hexdigest()[:16]
    
    with lock:
        files[file_id] = file_bytes
        progress[file_id] = {'status': '✓ تم التحميل', 'progress': 0}
    
    logger.info(f"File uploaded: {file.filename} ({len(file_bytes)} bytes)")
    
    try:
        excel = pd.ExcelFile(io.BytesIO(file_bytes))
        sheets = excel.sheet_names
    except Exception as e:
        return jsonify({'error': str(e), 'code': 'READ_ERROR'}), 400
    
    for sheet in sheets:
        thread = threading.Thread(
            target=analyze_background,
            args=(file_id, sheet, file_bytes),
            daemon=True
        )
        thread.start()
    
    return jsonify({'success': True, 'sheets': sheets, 'file_id': file_id})


@app.route('/progress', methods=['GET'])
@validate_session
def get_progress():
    """Get file processing progress"""
    file_id = request.args.get('file_id')
    if not file_id:
        return jsonify({'progress': 0, 'status': 'لا يوجد ملف'}), 200
    
    with lock:
        if file_id in progress:
            return jsonify(progress[file_id].copy()), 200
    
    return jsonify({'progress': 0, 'status': 'جاري المعالجة...'}), 200


@app.route('/analytics', methods=['POST'])
@validate_session
def analytics():
    """Get analytics results"""
    data = request.get_json()
    file_id = data.get('file_id')
    sheet = data.get('sheet')
    
    if not file_id or not sheet:
        return jsonify({'error': 'معلومات ناقصة', 'code': 'MISSING_PARAMS'}), 400
    
    cache_key = f"{file_id}_{sheet}"
    
    for i in range(300):  # 30 seconds max wait
        if cache_key in analytics_cache:
            with lock:
                result = analytics_cache[cache_key].copy()
            return jsonify(result), 200
        
        import time
        time.sleep(0.1)
    
    return jsonify({'error': 'انتهت المهلة', 'code': 'TIMEOUT'}), 202


@app.route('/get-columns', methods=['POST'])
@validate_session
def get_columns():
    """Get columns from uploaded file"""
    data = request.get_json()
    file_id = data.get('file_id')
    sheet = data.get('sheet', 'Sheet1')
    
    if not file_id or file_id not in files:
        return jsonify({'error': 'الملف غير موجود', 'code': 'FILE_NOT_FOUND'}), 404
    
    try:
        excel = pd.ExcelFile(io.BytesIO(files[file_id]))
        df = pd.read_excel(excel, sheet_name=sheet)
        columns = [col for col in df.columns.tolist()]
        return jsonify({'columns': columns}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'code': 'READ_ERROR'}), 400


@app.route('/analyze-custom', methods=['POST'])
@validate_session
def analyze_custom():
    """Custom analysis with selected columns"""
    data = request.get_json()
    file_id = data.get('file_id')
    sheet = data.get('sheet', 'Sheet1')
    dept_col = data.get('dept_column')
    rating_cols = data.get('rating_columns', [])
    
    if not file_id or not dept_col or not rating_cols:
        return jsonify({'error': 'أعمدة ناقصة', 'code': 'MISSING_COLUMNS'}), 400
    
    if file_id not in files:
        return jsonify({'error': 'الملف غير موجود', 'code': 'FILE_NOT_FOUND'}), 404
    
    if isinstance(rating_cols, str):
        rating_cols = [rating_cols]
    
    try:
        excel = pd.ExcelFile(io.BytesIO(files[file_id]))
        df = pd.read_excel(excel, sheet_name=sheet)
        df = df.dropna(how='all')
        
        all_ratings = []
        column_results = {}
        
        for rating_col in rating_cols:
            ratings = []
            for val in df[rating_col]:
                r = convert_rating(val)
                if r:
                    ratings.append(r)
                    all_ratings.append({'col': rating_col, 'rating': r})
            
            depts = {}
            for dept, group in df.groupby(dept_col, observed=True):
                dept_ratings = []
                for val in group[rating_col]:
                    r = convert_rating(val)
                    if r:
                        dept_ratings.append(r)
                
                if dept_ratings:
                    depts[str(dept)] = {
                        'count': len(group),
                        'avg': round(np.mean(dept_ratings), 2)
                    }
            
            top_depts = sorted(depts.items(), key=lambda x: x[1]['avg'], reverse=True)[:10]
            
            column_results[rating_col] = {
                'valid_ratings': len(ratings),
                'avg': round(np.mean(ratings), 2) if ratings else 0,
                'top_departments': [{'name': d[0], 'rating': d[1]['avg'], 'employees': d[1]['count']} for d in top_depts]
            }
        
        combined_top_depts = {}
        for rating_col in rating_cols:
            if rating_col in column_results:
                for dept in column_results[rating_col]['top_departments']:
                    if dept['name'] not in combined_top_depts:
                        combined_top_depts[dept['name']] = {'ratings': [], 'employees': set()}
                    combined_top_depts[dept['name']]['ratings'].append(dept['rating'])
                    combined_top_depts[dept['name']]['employees'].add(dept['employees'])
        
        final_top_depts = []
        for name, data_dict in combined_top_depts.items():
            avg_rating = round(sum(data_dict['ratings']) / len(data_dict['ratings']), 2)
            final_top_depts.append({
                'name': name,
                'rating': avg_rating,
                'employees': max(data_dict['employees']) if data_dict['employees'] else 0
            })
        
        final_top_depts.sort(key=lambda x: x['rating'], reverse=True)
        
        result = {
            'total_records': len(df),
            'valid_ratings': len(all_ratings),
            'avg_rating': round(np.mean([r['rating'] for r in all_ratings]), 2) if all_ratings else 0,
            'top_departments': final_top_depts[:10],
            'column_details': column_results,
            'columns_used': {'dept': dept_col, 'ratings': rating_cols}
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Custom analysis error: {e}")
        return jsonify({'error': str(e), 'code': 'ANALYSIS_ERROR'}), 400


@app.route('/clear', methods=['POST'])
@validate_session
def clear():
    """Clear all data for session"""
    with lock:
        files.clear()
        analytics_cache.clear()
        progress.clear()
    
    logger.info(f'Data cleared for IP: {request.remote_addr}')
    return jsonify({'success': True}), 200


@app.route('/status', methods=['GET'])
def status():
    """Health check endpoint"""
    return jsonify({
        'status': 'running',
        'domain': DOMAIN_NAME,
        'time': datetime.now().isoformat()
    }), 200


@app.route('/health', methods=['GET'])
def health():
    """Detailed health check for load balancers"""
    return jsonify({
        'healthy': True,
        'active_sessions': len(sessions),
        'cached_files': len(files),
        'memory': 'ok'
    }), 200


def analyze_background(file_id, sheet_name, file_bytes):
    """Background analysis worker"""
    try:
        with lock:
            if file_id not in progress:
                progress[file_id] = {'status': '📥 جاري قراءة...', 'progress': 1}
        
        logger.info(f"Processing sheet: {sheet_name}")
        df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet_name)
        df = df.dropna(how='all')
        
        logger.info(f"Loaded {len(df)} records")
        
        analyzer = FastAnalyzer(df, file_id)
        result = analyzer.analyze()
        
        with lock:
            analytics_cache[f"{file_id}_{sheet_name}"] = result
        
        logger.info("Analysis complete")
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        with lock:
            progress[file_id] = {'status': f'❌ خطأ: {str(e)}', 'progress': 0}


class FastAnalyzer:
    def __init__(self, df, file_id):
        self.df = df
        self.file_id = file_id
    
    def update_progress(self, status, pct):
        with lock:
            progress[self.file_id] = {'status': status, 'progress': pct}
    
    def analyze(self):
        self.update_progress('🔍 كشف الأعمدة...', 10)
        
        dept_col = None
        rating_col = None
        region_col = None
        
        # Find department column
        dept_keywords = ['قسم', 'department', 'dept', 'إدارة', 'ادارة', 'جهة', 'وحدة', 'فرع', 'branch', 'section']
        name_keywords = ['اسم', 'name', 'موظف', 'employee', 'سجل', 'id']
        
        for col in self.df.columns:
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in name_keywords):
                logger.info(f"Skipping name/ID column: {col}")
                continue
            if any(keyword in col_lower for keyword in dept_keywords):
                dept_col = col
                logger.info(f"Department column: {col}")
                break
        
        # Find rating column
        rating_keywords = ['أداء الحالية', 'أداء الحالي', 'درجة الاداء الحالية', 'تقييم', 'rating', 'score', 'نسبة', 'إنجاز', 'أداء', 'درجة', 'معدل', 'average', 'avg']
        
        for col in self.df.columns:
            col_lower = str(col).lower()
            if 'حالية' in col_lower or 'حالي' in col_lower:
                if any(keyword in col_lower for keyword in ['أداء', 'درجة', 'تقييم']):
                    try:
                        sample = pd.to_numeric(self.df[col], errors='coerce')
                        if sample.notna().sum() > 0:
                            rating_col = col
                            logger.info(f"Rating column (current): {col}")
                            break
                    except:
                        continue
        
        if not rating_col:
            for col in self.df.columns:
                col_lower = str(col).lower()
                if any(keyword in col_lower for keyword in rating_keywords):
                    try:
                        sample = pd.to_numeric(self.df[col], errors='coerce')
                        if sample.notna().sum() > 0:
                            rating_col = col
                            logger.info(f"Rating column: {col}")
                            break
                    except:
                        continue
        
        # Fallbacks
        if not dept_col:
            for col in self.df.columns:
                if self.df[col].dtype == 'object' or self.df[col].dtype.name == 'string':
                    dept_col = col
                    break
            if not dept_col:
                dept_col = self.df.columns[0]
        
        if not rating_col:
            for col in self.df.columns:
                try:
                    sample = pd.to_numeric(self.df[col], errors='coerce')
                    if sample.notna().sum() > len(self.df) * 0.5:
                        rating_col = col
                        break
                except:
                    continue
            if not rating_col:
                rating_col = self.df.columns[-1]
        
        # Detect region column
        region_keywords = ['منطقة', 'region', 'location', 'مكان', 'الموقع', 'city', 'مدينة', 'province']
        for col in self.df.columns:
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in region_keywords):
                region_col = col
                logger.info(f"Region column: {col}")
                break
        
        self.update_progress('⚡ معالجة التقييمات...', 30)
        
        ratings = []
        for val in self.df[rating_col]:
            r = convert_rating(val)
            if r:
                ratings.append(r)
        
        self.update_progress('📊 تحليل الأقسام...', 60)
        
        depts = {}
        for dept, group in self.df.groupby(dept_col, observed=True):
            dept_ratings = []
            for val in group[rating_col]:
                r = convert_rating(val)
                if r:
                    dept_ratings.append(r)
            
            if dept_ratings:
                depts[str(dept)] = {
                    'count': len(group),
                    'avg': round(np.mean(dept_ratings), 2)
                }
        
        top_depts = sorted(depts.items(), key=lambda x: x[1]['avg'], reverse=True)[:10]
        
        self.update_progress('🗺️ تحليل المناطق...', 80)
        
        # Regional analysis
        regions = {}
        
        if region_col:
            for region, group in self.df.groupby(region_col, observed=True):
                region_name = str(region).strip()
                if region_name == 'nan' or not region_name:
                    continue
                    
                matched_region = match_region(region_name)
                
                if not matched_region:
                    continue
                
                region_ratings = []
                region_depts = {}
                
                for idx, row in group.iterrows():
                    dept_name = str(row.get(dept_col, 'غير محدد'))
                    r = convert_rating(row[rating_col])
                    if r:
                        region_ratings.append(r)
                        if dept_name not in region_depts:
                            region_depts[dept_name] = []
                        region_depts[dept_name].append(r)
                
                if region_ratings:
                    dept_details = []
                    for dept, dratings in region_depts.items():
                        dept_details.append({
                            'name': dept,
                            'avg_rating': round(np.mean(dratings), 2),
                            'employees': len(dratings)
                        })
                    dept_details.sort(key=lambda x: x['avg_rating'], reverse=True)
                    
                    avg_rating = round(np.mean(region_ratings), 2)
                    if matched_region in SAUDI_REGIONS:
                        regions[matched_region] = {
                            'lat': SAUDI_REGIONS[matched_region]['lat'],
                            'lng': SAUDI_REGIONS[matched_region]['lng'],
                            'color': SAUDI_REGIONS[matched_region]['color'],
                            'employees': len(group),
                            'avg_rating': avg_rating,
                            'departments': len(region_depts),
                            'dept_details': dept_details,
                            'top_dept': dept_details[0] if dept_details else None,
                            'low_dept': dept_details[-1] if dept_details else None
                        }
        else:
            # Extract from department names
            dept_regions = {}
            for dept_name in depts.keys():
                matched_region = match_region(dept_name)
                if matched_region:
                    if matched_region not in dept_regions:
                        dept_regions[matched_region] = []
                    dept_regions[matched_region].append(dept_name)
            
            if dept_regions:
                for region_name, region_depts in dept_regions.items():
                    region_ratings = []
                    region_depts_data = {}
                    
                    for dept in region_depts:
                        if dept in depts:
                            for i in range(depts[dept]['count']):
                                region_ratings.append(depts[dept]['avg'])
                            region_depts_data[dept] = {
                                'avg_rating': depts[dept]['avg'],
                                'employees': depts[dept]['count']
                            }
                    
                    if region_ratings and region_name in SAUDI_REGIONS:
                        dept_details = [{'name': k, 'avg_rating': v['avg_rating'], 'employees': v['employees']} 
                                       for k, v in region_depts_data.items()]
                        dept_details.sort(key=lambda x: x['avg_rating'], reverse=True)
                        avg_rating = round(np.mean(region_ratings), 2)
                        
                        regions[region_name] = {
                            'lat': SAUDI_REGIONS[region_name]['lat'],
                            'lng': SAUDI_REGIONS[region_name]['lng'],
                            'color': SAUDI_REGIONS[region_name]['color'],
                            'employees': sum(d['employees'] for d in region_depts_data.values()),
                            'avg_rating': avg_rating,
                            'departments': len(region_depts),
                            'dept_details': dept_details,
                            'top_dept': dept_details[0] if dept_details else None,
                            'low_dept': dept_details[-1] if dept_details else None
                        }
        
        self.update_progress('✅ اكتمل!', 100)
        
        return {
            'total_records': len(self.df),
            'valid_ratings': len(ratings),
            'avg_rating': round(np.mean(ratings), 2) if ratings else 0,
            'top_departments': [{'name': d[0], 'rating': d[1]['avg'], 'employees': d[1]['count']} for d in top_depts],
            'regional_data': regions
        }


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='HR Analytics Production Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to listen on')
    parser.add_argument('--workers', type=int, default=1, help='Number of worker processes')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--ssl', action='store_true', help='Enable HTTPS')
    
    args = parser.parse_args()
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║     منظومة إدارة الأداء الوظيفي - Ministry of Education      ║
║                                                              ║
║  🌐 Domain: {DOMAIN_NAME:<42}║
║  📡 Server: http://{args.host}:{args.port:<40}║
║  🔒 SSL: {'Enabled' if args.ssl else 'Disabled':<49}║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    if args.ssl:
        # SSL context
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(
            '/etc/letsencrypt/live/analysis.turki20.sa/fullchain.pem',
            '/etc/letsencrypt/live/analysis.turki20.sa/privkey.pem'
        )
        
        if args.workers > 1:
            print("Running with multiple workers. SSL handled by nginx.")
            app.run(
                host=args.host,
                port=args.port,
                debug=args.debug,
                threaded=True
            )
        else:
            app.run(
                host=args.host,
                port=args.port,
                debug=args.debug,
                ssl_context=ssl_context,
                threaded=True
            )
    else:
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug,
            threaded=True
        )

