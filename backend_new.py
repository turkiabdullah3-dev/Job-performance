#!/usr/bin/env python3
"""
Enhanced secure backend with improved region detection and data accuracy.
"""

import os
import secrets
import tempfile
import pathlib
import json
from functools import wraps
from flask import Flask, request, jsonify, make_response, send_from_directory, abort
from flask_cors import CORS
from werkzeug.utils import secure_filename
import pandas as pd
import numpy as np
import io
import threading
import hashlib
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"xls", "xlsx"}
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MB

app = Flask(__name__, static_folder='.')
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

CORS(app, supports_credentials=True)

# Session & Storage with enhanced security
sessions = {}
files = {}
analytics_cache = {}
progress = {}
lock = threading.Lock()

# Security settings
SESSION_TIMEOUT = timedelta(hours=2)
MAX_SESSIONS_PER_IP = 5

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

# Enhanced region mapping with more variations
REGION_NAME_MAPPINGS = {
    'الرياض': ['الرياض', 'Riyadh', 'riyadh', 'RIYADH', 'منطقة الرياض', 'Central', 'KSA_Riyadh', 'رياض', 'المنطقة الرياض', 'الرياض Region'],
    'مكة': ['مكة', 'Makkah', 'makkah', 'MAKKAH', 'منطقة مكة', 'مكة المكرمة', 'Western', 'مكه', 'Western Province', 'Makkah Region'],
    'المدينة': ['المدينة', 'Medina', 'medina', 'MEDINA', 'المدينة المنورة', 'Al-Madinah', 'Madinah', 'المدينه', 'Medina Region'],
    'الشرقية': ['الشرقية', 'Eastern', 'eastern', 'EASTERN', 'المنطقة الشرقية', 'Eastern Province', 'Dammam', 'الشرقيه', 'Eastern Region'],
    'القصيم': ['القصيم', 'Qassim', 'qassim', 'QASSIM', 'Al-Qassim', 'بريده', 'Buraydah', 'القصييم', 'Qassim Region'],
    'عسير': ['عسير', 'Asir', 'asir', 'ASIR', 'Aseer', 'Abha', 'ابها', 'عسير Region', '南部地区'],
    'تبوك': ['تبوك', 'Tabuk', 'tabuk', 'TABUK', 'تبوك Region', 'Tabuk Region'],
    'حائل': ['حائل', 'Hail', 'hail', 'HAIL', 'Hael', "Ha'il", 'حايل', 'Hail Region'],
    'الجوف': ['الجوف', 'Jawf', 'jawf', 'JAWF', 'Al-Jawf', 'Sakaka', 'الجوف Region'],
    'نجران': ['نجران', 'Najran', 'najran', 'NAJRAN', 'Najran', 'نجران Region'],
    'الباحة': ['الباحة', 'Baha', 'baha', 'BAHA', 'Al-Baha', 'الباحه', 'Baha Region'],
    'جازان': ['جازان', 'Jazan', 'jazan', 'JAZAN', 'Gizan', 'Jizan', 'جيزان', 'Jazan Region'],
    'الأحساء': ['الأحساء', 'Ahsa', 'ahsa', 'AHSA', 'Al-Ahsa', 'Hofuf', 'الاحساء', 'الهفوف', 'Ahsa Region'],
}


def match_region(region_name):
    """
    Enhanced fuzzy match for region names with improved accuracy.
    Returns matched region name or None.
    """
    if not region_name or region_name == 'nan' or str(region_name).strip() == '':
        return None
    
    region_str = str(region_name).strip()
    
    # Check direct mappings first with exact matching
    for saudi_region, variations in REGION_NAME_MAPPINGS.items():
        for variation in variations:
            if variation.lower() == region_str.lower():
                return saudi_region
    
    # Check partial matches for short strings
    if len(region_str) >= 3:
        for saudi_region in REGION_NAME_MAPPINGS.keys():
            saudi_parts = saudi_region[:4].lower()
            region_lower = region_str.lower()
            if saudi_parts in region_lower or region_lower[:4] in saudi_parts:
                return saudi_region
    
    # Check for common abbreviations
    abbreviation_map = {
        'R': 'الرياض',
        'M': 'مكة',
        'MD': 'المدينة',
        'E': 'الشرقية',
        'Q': 'القصيم',
        'A': 'عسير',
        'T': 'تبوك',
        'H': 'حائل',
        'J': 'الجوف',
        'N': 'نجران',
        'B': 'الباحة',
        'G': 'جازان',
    }
    
    if region_str.upper() in abbreviation_map:
        return abbreviation_map[region_str.upper()]
    
    return None


def set_security_headers(resp):
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    resp.headers['X-Frame-Options'] = 'DENY'
    resp.headers['Referrer-Policy'] = 'no-referrer'
    resp.headers['Permissions-Policy'] = 'camera=(), microphone=()'
    resp.headers['Strict-Transport-Security'] = 'max-age=63072000; includeSubDomains; preload'
    resp.headers['Content-Security-Policy'] = "default-src 'self'; img-src 'self' data:; object-src 'none'"
    return resp


@app.after_request
def apply_security_headers(response):
    return set_security_headers(response)


class FastAnalyzer:
    def __init__(self, df, file_id):
        self.df = df
        self.file_id = file_id
    
    def update_progress(self, status, pct):
        with lock:
            progress[self.file_id] = {'status': status, 'progress': pct}
    
    def analyze(self):
        self.update_progress('🔍 كشف الأعمدة...', 10)
        
        logger.info(f"Available columns: {list(self.df.columns)}")
        
        dept_col = None
        rating_col = None
        region_col = None
        
        # Find department column
        dept_keywords = ['قسم', 'department', 'dept', 'إدارة', 'ادارة', 'جهة', 'وحدة', 'فرع', 'branch', 'section']
        name_keywords = ['اسم', 'name', 'موظف', 'employee', 'سجل', 'id']
        
        for col in self.df.columns:
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in name_keywords):
                logger.info(f"Skipping name/ID column for privacy: {col}")
                continue
            if any(keyword in col_lower for keyword in dept_keywords):
                dept_col = col
                logger.info(f"Department column found: {col}")
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
                            logger.info(f"Rating column found (current performance): {col}")
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
                            logger.info(f"Rating column found: {col}")
                            break
                    except:
                        continue
        
        # Fallback for department
        if not dept_col:
            for col in self.df.columns:
                if self.df[col].dtype == 'object' or self.df[col].dtype.name == 'string':
                    dept_col = col
                    logger.info(f"Using first text column as department: {col}")
                    break
            if not dept_col:
                dept_col = self.df.columns[0]
        
        # Fallback for rating
        if not rating_col:
            for col in self.df.columns:
                try:
                    sample = pd.to_numeric(self.df[col], errors='coerce')
                    if sample.notna().sum() > len(self.df) * 0.5:
                        rating_col = col
                        logger.info(f"Using first numeric column as rating: {col}")
                        break
                except:
                    continue
            if not rating_col:
                rating_col = self.df.columns[-1]
        
        logger.info(f"Final selection - Department: '{dept_col}', Rating: '{rating_col}'")
        
        # Detect region column
        region_keywords = ['منطقة', 'region', 'location', 'مكان', 'الموقع', 'city', 'مدينة', 'province']
        for col in self.df.columns:
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in region_keywords):
                region_col = col
                logger.info(f"Region column found: {col}")
                break
        
        self.update_progress('⚡ معالجة التقييمات...', 30)
        
        ratings = []
        for val in self.df[rating_col]:
            r = self._convert_rating(val)
            if r:
                ratings.append(r)
        
        self.update_progress('📊 تحليل الأقسام...', 60)
        
        depts = {}
        for dept, group in self.df.groupby(dept_col, observed=True):
            dept_ratings = []
            for val in group[rating_col]:
                r = self._convert_rating(val)
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
                    logger.debug(f"Could not match region: {region_name}")
                    continue
                
                region_ratings = []
                region_depts = {}
                
                for idx, row in group.iterrows():
                    dept_name = str(row.get(dept_col, 'غير محدد'))
                    r = self._convert_rating(row[rating_col])
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
            # No region column - try to extract from department names
            logger.info("No region column found, attempting to extract from department names")
            
            dept_regions = {}
            for dept_name in depts.keys():
                matched_region = match_region(dept_name)
                if matched_region:
                    if matched_region not in dept_regions:
                        dept_regions[matched_region] = []
                    dept_regions[matched_region].append(dept_name)
            
            if dept_regions:
                logger.info(f"Found regions in departments: {list(dept_regions.keys())}")
                
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
        
        logger.info(f"Found {len(regions)} regions with data")
        self.update_progress('✅ اكتمل!', 100)
        
        return {
            'total_records': len(self.df),
            'valid_ratings': len(ratings),
            'avg_rating': round(np.mean(ratings), 2) if ratings else 0,
            'top_departments': [{'name': d[0], 'rating': d[1]['avg'], 'employees': d[1]['count']} for d in top_depts],
            'regional_data': regions
        }
    
    def _convert_rating(self, val):
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
        except Exception as e:
            logger.debug(f"Rating conversion error for value '{val}': {e}")
            return None


def analyze_background(file_id, sheet_name, file_bytes):
    try:
        with lock:
            if file_id not in progress:
                progress[file_id] = {'status': '📥 جاري قراءة...', 'progress': 1}
        
        logger.info(f"Reading sheet: {sheet_name}")
        df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet_name)
        df = df.dropna(how='all')
        
        logger.info(f"Loaded {len(df)} records")
        
        analyzer = FastAnalyzer(df, file_id)
        result = analyzer.analyze()
        
        with lock:
            analytics_cache[f"{file_id}_{sheet_name}"] = result
        
        logger.info("Analysis complete")
    except Exception as e:
        logger.error(f"Error: {e}")
        with lock:
            progress[file_id] = {'status': f'❌ خطأ: {str(e)}', 'progress': 0}


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(path):
        return send_from_directory('.', path)
    return jsonify({'error': 'Not found'}), 404


@app.route('/init-session', methods=['GET'])
def init_session():
    client_ip = request.remote_addr
    
    with lock:
        now = datetime.now()
        expired = [t for t, data in sessions.items() 
                  if isinstance(data, dict) and data.get('expires', now) < now]
        for t in expired:
            del sessions[t]
        
        ip_sessions = sum(1 for data in sessions.values() 
                         if isinstance(data, dict) and data.get('ip') == client_ip)
        
        if ip_sessions >= MAX_SESSIONS_PER_IP:
            return jsonify({'error': 'Too many sessions'}), 429
        
        token = secrets.token_urlsafe(32)
        sessions[token] = {
            'created': now,
            'expires': now + SESSION_TIMEOUT,
            'ip': client_ip,
            'uploads': 0
        }
    
    logger.info(f"Secure session created for IP: {client_ip}")
    return jsonify({'session_token': token})


@app.route('/upload', methods=['POST'])
def upload():
    token = request.headers.get('X-Session-Token')
    
    with lock:
        if not token or token not in sessions:
            return jsonify({'error': 'Invalid session'}), 401
        
        session_data = sessions[token]
        
        if session_data['expires'] < datetime.now():
            del sessions[token]
            return jsonify({'error': 'Session expired'}), 401
        
        if session_data['ip'] != request.remote_addr:
            return jsonify({'error': 'Invalid session'}), 401
        
        if session_data['uploads'] >= 10:
            return jsonify({'error': 'Upload limit reached'}), 429
        
        session_data['uploads'] += 1
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    
    file = request.files['file']
    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({'error': 'Excel only'}), 400
    
    file_bytes = file.read()
    if not file_bytes:
        return jsonify({'error': 'Empty file'}), 400
    
    file_id = hashlib.sha256(file_bytes).hexdigest()[:16]
    
    with lock:
        files[file_id] = file_bytes
        progress[file_id] = {'status': '✓ تم التحميل', 'progress': 0}
    
    logger.info(f"File: {file.filename} ({len(file_bytes)} bytes)")
    
    try:
        excel = pd.ExcelFile(io.BytesIO(file_bytes))
        sheets = excel.sheet_names
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
    for sheet in sheets:
        thread = threading.Thread(
            target=analyze_background,
            args=(file_id, sheet, file_bytes),
            daemon=True
        )
        thread.start()
    
    return jsonify({'success': True, 'sheets': sheets, 'file_id': file_id})


@app.route('/progress', methods=['GET'])
def get_progress():
    token = request.headers.get('X-Session-Token')
    
    with lock:
        if token not in sessions:
            return jsonify({'error': 'Invalid session'}), 401
        
        session_data = sessions[token]
        if session_data['expires'] < datetime.now():
            del sessions[token]
            return jsonify({'error': 'Session expired'}), 401
    
    file_id = request.args.get('file_id')
    if not file_id:
        return jsonify({'progress': 0, 'status': 'No file'}), 200
    
    with lock:
        if file_id in progress:
            return jsonify(progress[file_id].copy()), 200
    
    return jsonify({'progress': 0, 'status': 'Processing'}), 200


@app.route('/analytics', methods=['POST'])
def analytics():
    token = request.headers.get('X-Session-Token')
    
    with lock:
        if token not in sessions:
            return jsonify({'error': 'Invalid session'}), 401
        
        session_data = sessions[token]
        if session_data['expires'] < datetime.now():
            del sessions[token]
            return jsonify({'error': 'Session expired'}), 401
    
    data = request.get_json()
    file_id = data.get('file_id')
    sheet = data.get('sheet')
    
    if not file_id or not sheet:
        return jsonify({'error': 'Missing params'}), 400
    
    cache_key = f"{file_id}_{sheet}"
    
    for i in range(600):
        if cache_key in analytics_cache:
            with lock:
                result = analytics_cache[cache_key].copy()
            return jsonify(result), 200
        
        import time
        time.sleep(0.1)
    
    return jsonify({'error': 'Timeout'}), 202


@app.route('/clear', methods=['POST'])
def clear():
    token = request.headers.get('X-Session-Token')
    
    with lock:
        if token not in sessions:
            return jsonify({'error': 'Invalid session'}), 401
        
        session_data = sessions[token]
        if session_data['expires'] < datetime.now():
            del sessions[token]
            return jsonify({'error': 'Session expired'}), 401
        
        files.clear()
        analytics_cache.clear()
        progress.clear()
    
    logger.info(f'Data cleared securely for IP: {request.remote_addr}')
    return jsonify({'success': True}), 200


@app.route('/status', methods=['GET'])
def status():
    return jsonify({'status': 'running', 'fast': True}), 200


if __name__ == '__main__':
    print("\n🔒 Enhanced HR Analytics System")
    print("=" * 50)
    print("Features:")
    print("  - Improved region detection")
    print("  - Enhanced data accuracy")
    print("  - Session-based security")
    print("  - Background processing")
    print("=" * 50)
    print(f"Server: http://127.0.0.1:8080")
    print("=" * 50 + "\n")
    
    app.run(debug=False, host='127.0.0.1', port=8080, threaded=True)

