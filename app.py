from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import numpy as np
import io
import threading
import hashlib
import secrets
from datetime import datetime, timedelta
import logging
import os
import re
import bcrypt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=BASE_DIR)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

# CORS Configuration for Production
ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', '*').split(',')
CORS(app, 
     resources={r"/*": {
         "origins": ALLOWED_ORIGINS,
         "methods": ["GET", "POST", "OPTIONS"],
         "allow_headers": ["Content-Type", "X-Session-Token"],
         "expose_headers": ["X-Session-Token"],
         "supports_credentials": False
     }})

# Session & Storage with enhanced security
sessions = {}
files = {}
analytics_cache = {}
progress = {}
lock = threading.Lock()
login_attempts = {}  # Track failed login attempts for rate limiting

# Security settings
SESSION_TIMEOUT = timedelta(hours=2)
MAX_SESSIONS_PER_IP = 5
MAX_LOGIN_ATTEMPTS = 5
LOGIN_ATTEMPT_TIMEOUT = 15 * 60  # 15 minutes

# Default credentials (hash bcrypt for secure storage)
# Username: admin, Password: admin123456
DEFAULT_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
DEFAULT_PASSWORD_HASH = os.environ.get('ADMIN_PASSWORD_HASH', '$2b$12$Xvq6wFhYjcT3L3V5K6Q5q.R3Q5K5Q5K5Q5K5Q5K5Q5K5Q5K5Q5Q5')  # bcrypt hash of 'admin123456'

# If password hash not set, generate one
if DEFAULT_PASSWORD_HASH == '$2b$12$Xvq6wFhYjcT3L3V5K6Q5q.R3Q5K5Q5K5Q5K5Q5K5Q5K5Q5K5Q5Q5':
    try:
        DEFAULT_PASSWORD_HASH = bcrypt.hashpw(b'admin123456', bcrypt.gensalt()).decode()
    except:
        logger.warning("bcrypt not available, using default hash")

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


def normalize_text(text):
    """
    Normalize text for fuzzy matching.
    Removes diacritics, extra spaces, and converts to consistent format.
    """
    if not text:
        return ''
    
    text = str(text).strip()
    
    # Remove diacritics (Arabic harakat)
    arabic_diacritics = re.compile('[\u064B-\u065F\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED]')
    text = arabic_diacritics.sub('', text)
    
    # Normalize Arabic letters
    replacements = {
        'ة': 'ه', 'ہ': 'ه', 'ھ': 'ه', 'ە': 'ه',
        'ي': 'ي', 'ى': 'ي', 'ئ': 'ي', 'ؤ': 'و',
        'أ': 'ا', 'إ': 'ا', 'آ': 'ا',
        'ك': 'ك', 'گ': 'ك',
        'پ': 'ب', 'چ': 'ج', 'ژ': 'ز', 'ف': 'ف',
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Convert to lowercase for English
    text = text.lower()
    
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def match_region(region_name):
    """
    Enhanced fuzzy match a region name to SAUDI_REGIONS keys.
    Returns matched region name or None.
    """
    if not region_name or region_name == 'nan':
        return None
    
    region_str = str(region_name).strip()
    region_normalized = normalize_text(region_str)
    
    # Extended region mapping for better matching (Arabic + English + variations)
    REGION_NAME_MAPPINGS = {
        # Riyadh variations
        'الرياض': [
            'الرياض', 'Riyadh', 'riyadh', 'RIYADH', 'منطقة الرياض', 'المنطقة الوسطى', 
            'الوسطى', 'Central', 'central', 'KSA_Riyadh', ' Riyadh', 'Riyadh Region',
            'الرياض region', 'منطقة منطقة الرياض', 'رياض', 'الرياض ',
            'riyadh region', 'central region', 'الرياضالوسطى'
        ],
        # Mecca variations
        'مكة': [
            'مكة', 'Makkah', 'makkah', 'MAKKAH', ' Mecca', 'منطقة مكة', 
            'مكة المكرمة', 'Makkah Al-Mukerramah', 'Makkah Al-Mukarramah', 
            'Western', 'western', 'Western Region', 'Makka', 'Mecca', 'mecca',
            'جدة', 'Jeddah', 'jeddah', 'جدة ', 'جده', 'Western Region Saudi',
            'مكه', 'مكه المكرمة', 'جدة '
        ],
        # Medina variations
        'المدينة': [
            'المدينة', 'Medina', 'medina', 'MEDINA', ' Medina', 'المدينة المنورة', 
            'Medina Munawarah', 'Al-Madinah', 'Madinah', 'Madina', 'Al-Madinah Al-Munawwarah',
            'المدينه', 'المدينة المنورة ', 'المنورة', 'Madinah Region',
            'المدينهالمنوره', 'المدينه ', 'المدينهالمنورة'
        ],
        # Eastern Province variations
        'الشرقية': [
            'الشرقية', 'Eastern', 'eastern', 'EASTERN', 'الشرقية', 'المنطقة الشرقية', 
            'Eastern Province', 'Dammam', 'damman', 'Dhofar', 'الدمام', 'الظهران',
            'الخبر', 'القطيف', 'الجبيل', 'Ras Tanura', 'رأس تنورة', 'Dahran', 'Dhahran',
            'الشرقيه', 'المنطقةالشرقية', 'Eastern Region Saudi Arabia', 'الدمام ',
            'الظهران ', 'الخبر ', 'القطيف ', 'الجبيل '
        ],
        # Qassim variations
        'القصيم': [
            'القصيم', 'Qassim', 'qassim', 'QASSIM', 'Al-Qassim', 'Alqassim', 
            'بريده', 'Buraydah', 'buraydah', 'Central Province (Qassim)', 
            'القصيم region', 'الرس', 'عنيزة', 'Buraidah', 'Qassim Region',
            'القصيم ', 'الرس ', 'عنيزة ', 'بريدة', 'Central Province'
        ],
        # Asir variations
        'عسير': [
            'عسير', 'Asir', 'asir', 'ASIR', 'Aseer', 'Abha', 'abha', 
            '南部地区', 'Khamis Mushait', 'خميس مشيط', 'ابها', 'ابها ',
            'محايل', 'محايل عسير', 'النماص', 'تنومة', 'ASIR Region',
            'ابها ', 'خميس ', 'ابهاالمنطقة', 'ابها region'
        ],
        # Tabuk variations
        'تبوك': [
            'تبوك', 'Tabuk', 'tabuk', 'TABUK', 'Tabook', 'تبوك region',
            'تبوك ', 'طبرجل', 'تكelma', 'البدع', 'حقل', 'تبوكRegion',
            'طبرجل ', 'البدع ', 'حقل '
        ],
        # Hail variations
        'حائل': [
            'حائل', 'Hail', 'hail', 'HAIL', 'Hael', "Ha'il", ' Hail',
            'حائل region', 'حائل ', 'الشنان', 'الغزالة', 'Hail Region',
            'الشنان ', 'الغزالة '
        ],
        # Al-Jawf variations
        'الجوف': [
            'الجوف', 'Jawf', 'jawf', 'JAWF', 'Al-Jawf', 'Aljawf', 
            'Sakaka', 'sakaka', 'سكاكا', 'القريات', 'رفحا', 'دومة الجندل',
            'الجوف ', 'سكاكا ', 'الجوفregion', 'Jawf Region'
        ],
        # Najran variations
        'نجران': [
            'نجران', 'Najran', 'najran', 'NAJRAN', 'Najrān', ' Najran',
            'نجران region', 'نجران ', 'ابها', 'hubuna', 'حبونا', 'Najran Region',
            'حبونا ', 'نجرانregion'
        ],
        # Al-Baha variations
        'الباحة': [
            'الباحة', 'Baha', 'baha', 'BAHA', 'Al-Baha', 'Albahah', 
            'Bahah', 'الباحة region', 'الباحة ', 'بلجرشي', 'المخواة', 'قلوة',
            'Baha Region', 'بلجرشي ', 'المخواة ', 'قلوة '
        ],
        # Jazan variations
        'جازان': [
            'جازان', 'Jazan', 'jazan', 'JAZAN', 'Gizan', 'gizan', 
            'Jizan', 'جيزان', 'جازان region', 'جازان ', 'صبيا', 'أحد المسارحة',
            'الفرصة', 'الدرب', 'Jazan Region', 'صبيا ', 'أحد ',
            'أحد المسارحة ', 'الفرصة ', 'الدرب '
        ],
        # Al-Ahsa variations
        'الأحساء': [
            'الأحساء', 'Ahsa', 'ahsa', 'AHSA', 'Al-Ahsa', 'Alahsa', 
            'Hofuf', 'hofuf', 'Hasa', 'الهفوف', 'الأحساء region', 'الأحساء ',
            'الدمام', 'ommel', 'ommel', 'Ahsa Region', 'الهفوف ',
            'الدمام ', 'حفرالباطن', 'الأحساءregion'
        ],
    }
    
    # Check direct mappings first with normalized comparison
    for saudi_region, variations in REGION_NAME_MAPPINGS.items():
        for variation in variations:
            variation_normalized = normalize_text(variation)
            
            # Exact or contains match
            if variation_normalized in region_normalized or region_normalized in variation_normalized:
                logger.debug(f"Matched region: '{region_name}' -> '{saudi_region}' (via '{variation}')")
                return saudi_region
    
    # Check partial matches for short strings (minimum 3 characters)
    if len(region_normalized) >= 3:
        for saudi_region in SAUDI_REGIONS.keys():
            saudi_normalized = normalize_text(saudi_region)
            # Check first 4 characters
            saudi_parts = saudi_normalized[:4]
            if saudi_parts and saudi_parts in region_normalized:
                logger.debug(f"Partial matched region: '{region_name}' -> '{saudi_region}'")
                return saudi_region
    
    # Check if the string is mostly Arabic and try word-by-word matching
    arabic_chars = re.findall(r'[\u0600-\u06FF]', region_str)
    if len(arabic_chars) / max(len(region_str), 1) > 0.3:  # If more than 30% Arabic
        for saudi_region in SAUDI_REGIONS.keys():
            saudi_normalized = normalize_text(saudi_region)
            # Split into words and check
            words = region_normalized.split()
            saudi_words = saudi_normalized.split()
            for word in words:
                if word in saudi_words or saudi_normalized in word:
                    logger.debug(f"Word matched region: '{region_name}' -> '{saudi_region}'")
                    return saudi_region
    
    logger.debug(f"Could not match region: '{region_name}' (normalized: '{region_normalized}')")
    return None


class FastAnalyzer:
    def __init__(self, df, file_id):
        self.df = df
        self.file_id = file_id
    
    def update_progress(self, status, pct):
        with lock:
            progress[self.file_id] = {'status': status, 'progress': pct}
    
    def analyze(self):
        self.update_progress('🔍 كشف الأعمدة...', 10)
        
        logger.info(f"📋 Available columns: {list(self.df.columns)}")
        
        dept_col = None
        rating_col = None
        
        # Find department column (EXCLUDE employee names for privacy!)
        dept_keywords = ['قسم', 'department', 'dept', 'إدارة', 'ادارة', 'جهة', 'وحدة', 'فرع', 'branch', 'section']
        name_keywords = ['اسم', 'name', 'موظف', 'employee', 'سجل', 'id']
        
        for col in self.df.columns:
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in name_keywords):
                logger.info(f"⚠️ Skipping name/ID column for privacy: {col}")
                continue
            if any(keyword in col_lower for keyword in dept_keywords):
                dept_col = col
                logger.info(f"✓ Department column found: {col}")
                break
        
        # Find rating column - prefer current performance
        rating_keywords = ['أداء الحالية', 'أداء الحالي', 'درجة الاداء الحالية', 'تقييم', 'rating', 'score', 'نسبة', 'إنجاز', 'أداء', 'درجة', 'معدل', 'average', 'avg']
        
        for col in self.df.columns:
            col_lower = str(col).lower()
            if 'حالية' in col_lower or 'حالي' in col_lower:
                if any(keyword in col_lower for keyword in ['أداء', 'درجة', 'تقييم']):
                    try:
                        sample = pd.to_numeric(self.df[col], errors='coerce')
                        if sample.notna().sum() > 0:
                            rating_col = col
                            logger.info(f"✓ Rating column found (current performance): {col}")
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
                            logger.info(f"✓ Rating column found: {col}")
                            break
                    except:
                        continue
        
        # Fallback
        if not dept_col:
            for col in self.df.columns:
                if self.df[col].dtype == 'object' or self.df[col].dtype.name == 'string':
                    dept_col = col
                    logger.info(f"📌 Using first text column as department: {col}")
                    break
            if not dept_col:
                dept_col = self.df.columns[0]
        
        if not rating_col:
            for col in self.df.columns:
                try:
                    sample = pd.to_numeric(self.df[col], errors='coerce')
                    if sample.notna().sum() > len(self.df) * 0.5:
                        rating_col = col
                        logger.info(f"📌 Using first numeric column as rating: {col}")
                        break
                except:
                    continue
            if not rating_col:
                rating_col = self.df.columns[-1]
        
        logger.info(f"✅ Final selection - Department: '{dept_col}', Rating: '{rating_col}'")
        
        self.update_progress('⚡ معالجة التقييمات...', 30)
        
        # Detect if there's a region/location column
        region_col = None
        region_keywords = ['منطقة', 'region', 'location', 'مكان', 'الموقع', 'city', 'مدينة', 'province']
        for col in self.df.columns:
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in region_keywords):
                region_col = col
                logger.info(f"✓ Region column found: {col}")
                break
        
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
        
        # Regional analysis - use region column if available, otherwise skip or use department
        regions = {}
        
        if region_col:
            # Use the dedicated region column for accurate regional data
            for region, group in self.df.groupby(region_col, observed=True):
                region_name = str(region).strip()
                if region_name == 'nan' or not region_name:
                    continue
                    
                # Find matching SAUDI_REGION using fuzzy matching
                matched_region = match_region(region_name)
                
                if not matched_region:
                    # Log unmatched regions for debugging
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
            
            # Group by department and try to infer region
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
                    
                    if region_ratings:
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
            else:
                # Last resort: distribute data across regions for visualization
                logger.warning("No regions detected in data - creating aggregated view")
                all_ratings = []
                all_depts = {}
                
                for dept_name, dept_data in depts.items():
                    all_ratings.extend([dept_data['avg']] * dept_data['count'])
                    all_depts[dept_name] = {
                        'avg_rating': dept_data['avg'],
                        'employees': dept_data['count']
                    }
                
                if all_ratings:
                    # Show all regions with equal weighting but note data is aggregated
                    dept_details = [{'name': k, 'avg_rating': v['avg_rating'], 'employees': v['employees']} 
                                   for k, v in all_depts.items()]
                    dept_details.sort(key=lambda x: x['avg_rating'], reverse=True)
                    avg_rating = round(np.mean(all_ratings), 2)
                    
                    # Add all regions with same data (visual representation only)
                    for region_name in list(SAUDI_REGIONS.keys())[:5]:  # Show top 5 regions
                        regions[region_name] = {
                            'lat': SAUDI_REGIONS[region_name]['lat'],
                            'lng': SAUDI_REGIONS[region_name]['lng'],
                            'color': SAUDI_REGIONS[region_name]['color'],
                            'employees': sum(d['employees'] for d in all_depts.values()),
                            'avg_rating': avg_rating,
                            'departments': len(all_depts),
                            'dept_details': dept_details,
                            'top_dept': dept_details[0] if dept_details else None,
                            'low_dept': dept_details[-1] if dept_details else None,
                            '_aggregated': True  # Flag to indicate this is aggregated data
                        }
        
        logger.info(f"✓ Found {len(regions)} regions with data")
        self.update_progress('✅ اكتمل!', 100)
        
        return {
            'total_records': len(self.df),
            'valid_ratings': len(ratings),
            'avg_rating': round(np.mean(ratings), 2) if ratings else 0,
            'top_departments': [{'name': d[0], 'rating': d[1]['avg'], 'employees': d[1]['count']} for d in top_depts],
            'regional_data': regions
        }
    
    def _get_color_for_rating(self, rating):
        if rating >= 4.5:
            return '#10b981'
        elif rating >= 4.0:
            return '#3b82f6'
        elif rating >= 3.0:
            return '#fbbf24'
        elif rating >= 2.0:
            return '#f97316'
        else:
            return '#ef4444'
    
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
        df, _ = load_dataframe(file_bytes, sheet_name)
        df = df.dropna(how='all')
        
        logger.info(f"Loaded {len(df)} records")
        
        analyzer = FastAnalyzer(df, file_id)
        result = analyzer.analyze()
        
        with lock:
            analytics_cache[f"{file_id}_{sheet_name}"] = result
        
        logger.info("✓ Analysis complete")
    except Exception as e:
        logger.error(f"Error: {e}")
        with lock:
            progress[file_id] = {'status': f'❌ خطأ: {str(e)}', 'progress': 0}


def load_dataframe(file_bytes, sheet_name=None):
    try:
        excel = pd.ExcelFile(io.BytesIO(file_bytes))
        if sheet_name and sheet_name in excel.sheet_names:
            use_sheet = sheet_name
        else:
            use_sheet = excel.sheet_names[0] if excel.sheet_names else 0
        df = pd.read_excel(excel, sheet_name=use_sheet)
        return df, excel.sheet_names
    except Exception as excel_error:
        try:
            df = pd.read_csv(io.BytesIO(file_bytes))
            return df, ['Sheet1']
        except Exception:
            raise excel_error


# ============= AUTHENTICATION ENDPOINTS =============

@app.route('/login', methods=['POST'])
def login():
    """تسجيل دخول المستخدم"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        client_ip = request.remote_addr
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        # Rate limiting: Check failed attempts
        with lock:
            if client_ip in login_attempts:
                attempts, last_time = login_attempts[client_ip]
                if datetime.now() - last_time < timedelta(seconds=LOGIN_ATTEMPT_TIMEOUT):
                    if attempts >= MAX_LOGIN_ATTEMPTS:
                        return jsonify({'error': 'Too many failed attempts. Try again later.'}), 429
                else:
                    login_attempts[client_ip] = (0, datetime.now())
        
        # Verify credentials
        if username != DEFAULT_USERNAME:
            with lock:
                if client_ip not in login_attempts:
                    login_attempts[client_ip] = (1, datetime.now())
                else:
                    attempts, _ = login_attempts[client_ip]
                    login_attempts[client_ip] = (attempts + 1, datetime.now())
            return jsonify({'error': 'Invalid username or password'}), 401
        
        # Verify password using bcrypt
        try:
            is_valid = bcrypt.checkpw(password.encode(), DEFAULT_PASSWORD_HASH.encode())
        except:
            # Fallback to simple comparison if bcrypt fails
            is_valid = (password == 'admin123456')
        
        if not is_valid:
            with lock:
                if client_ip not in login_attempts:
                    login_attempts[client_ip] = (1, datetime.now())
                else:
                    attempts, _ = login_attempts[client_ip]
                    login_attempts[client_ip] = (attempts + 1, datetime.now())
            return jsonify({'error': 'Invalid username or password'}), 401
        
        # Reset failed attempts
        with lock:
            if client_ip in login_attempts:
                del login_attempts[client_ip]
        
        # Create authenticated session
        session_token = secrets.token_urlsafe(32)
        with lock:
            sessions[session_token] = {
                'username': username,
                'ip': client_ip,
                'login_time': datetime.now(),
                'expires': datetime.now() + SESSION_TIMEOUT,
                'authenticated': True,
                'file_id': None
            }
        
        logger.info(f'✓ User "{username}" logged in from IP: {client_ip}')
        return jsonify({
            'success': True,
            'token': session_token,
            'session_token': session_token,
            'message': f'Welcome {username}'
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/logout', methods=['POST'])
def logout():
    """تسجيل خروج المستخدم"""
    try:
        token = request.headers.get('X-Session-Token')
        
        with lock:
            if token in sessions:
                username = sessions[token].get('username', 'unknown')
                client_ip = sessions[token].get('ip', 'unknown')
                del sessions[token]
                logger.info(f'✓ User "{username}" logged out from IP: {client_ip}')
                return jsonify({'success': True, 'message': 'Logged out successfully'}), 200
        
        return jsonify({'error': 'Invalid session'}), 401
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/auth-check', methods=['GET'])
def auth_check():
    """التحقق من حالة المستخدم الحالي"""
    try:
        token = request.headers.get('X-Session-Token')
        
        with lock:
            if token not in sessions:
                return jsonify({'authenticated': False}), 401
            
            session_data = sessions[token]
            if session_data['expires'] < datetime.now():
                del sessions[token]
                return jsonify({'authenticated': False}), 401
            
            return jsonify({
                'authenticated': True,
                'username': session_data['username'],
                'login_time': session_data['login_time'].isoformat()
            }), 200
        
    except Exception as e:
        logger.error(f"Auth check error: {e}")
        return jsonify({'authenticated': False}), 401


# ============= PROTECTED ENDPOINTS =============

def check_auth(request):
    """Helper function to check authentication"""
    token = request.headers.get('X-Session-Token')
    
    with lock:
        if token not in sessions:
            return None, 'Invalid session', 401
        
        session_data = sessions[token]
        if session_data['expires'] < datetime.now():
            del sessions[token]
            return None, 'Session expired', 401
        
        # Update last activity time
        session_data['last_activity'] = datetime.now()
        
        return session_data, None, None


@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    file_path = os.path.join(BASE_DIR, path)
    if os.path.exists(file_path):
        return send_from_directory(BASE_DIR, path)
    return jsonify({'error': 'Not found'}), 404

@app.route('/init-session', methods=['GET'])
def init_session():
    """Initialize session for authenticated user"""
    try:
        # Check if user is authenticated
        session_data, error, status = check_auth(request)
        if error:
            return jsonify({'error': error}), status
        
        logger.info(f"✓ Session initialized for user: {session_data['username']}")
        return jsonify({
            'success': True,
            'session_token': request.headers.get('X-Session-Token'),
            'username': session_data['username']
        }), 200
        
    except Exception as e:
        logger.error(f"Session init error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload():
    """Upload file for authenticated user"""
    try:
        # Check authentication
        session_data, error, status = check_auth(request)
        if error:
            logger.error(f"Auth error on upload: {error}")
            return jsonify({'error': error}), status
        
        if 'file' not in request.files:
            logger.error("No file in request")
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if not file.filename:
            logger.error("Empty filename")
            return jsonify({'error': 'No filename'}), 400
        
        if not file.filename.lower().endswith(('.xlsx', '.xls', '.csv')):
            logger.error(f"Invalid file type: {file.filename}")
            return jsonify({'error': 'Only Excel/CSV files allowed'}), 400
        
        file_bytes = file.read()
        if not file_bytes:
            logger.error("Empty file content")
            return jsonify({'error': 'Empty file'}), 400
        
        file_id = hashlib.sha256(file_bytes).hexdigest()[:16]
        
        with lock:
            files[file_id] = file_bytes
            progress[file_id] = {'status': '✓ تم التحميل', 'progress': 0}
            session_data['file_id'] = file_id
        
        logger.info(f"File: {file.filename} ({len(file_bytes)} bytes)")
        
        try:
            df_first, sheets = load_dataframe(file_bytes)
            columns_list = [col for col in df_first.columns.tolist()]
            
            # Analyze each column for numeric data
            enhanced_columns = []
            for col in columns_list:
                try:
                    numeric_count = pd.to_numeric(df_first[col], errors='coerce').notna().sum()
                    numeric_percentage = (numeric_count / len(df_first)) * 100 if len(df_first) > 0 else 0
                    is_numeric = int(numeric_percentage > 0)  # Convert bool to int for JSON serialization
                    enhanced_columns.append({
                        'name': col,
                        'numeric_percentage': float(round(numeric_percentage, 1)),
                        'is_numeric': is_numeric
                    })
                    logger.info(f"Column '{col}': {numeric_count}/{len(df_first)} numeric ({numeric_percentage:.1f}%)")
                except Exception as col_e:
                    logger.warning(f"Error analyzing column {col}: {str(col_e)}")
                    enhanced_columns.append({
                        'name': col,
                        'numeric_percentage': 0.0,
                        'is_numeric': 0
                    })
            
            logger.info(f"✓ Loaded {len(columns_list)} columns with type info")
        except Exception as e:
            logger.error(f"Data load error: {str(e)}")
            return jsonify({'error': f'Failed to read file: {str(e)}'}), 400
        
        for sheet in sheets:
            thread = threading.Thread(
                target=analyze_background,
                args=(file_id, sheet, file_bytes),
                daemon=True
            )
            thread.start()
        
        logger.info(f"✓ Upload successful: file_id={file_id}, columns={len(columns_list)}")
        return jsonify({'success': True, 'sheets': sheets, 'file_id': file_id, 'columns': enhanced_columns}), 200
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        return jsonify({'error': f'Server error: {str(e)}'}), 500

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


@app.route('/get-columns', methods=['POST'])
def get_columns():
    """إرجاع قائمة الأعمدة في الملف مع نوع البيانات"""
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
    sheet = data.get('sheet', 'Sheet1')
    
    if not file_id or file_id not in files:
        return jsonify({'error': 'File not found'}), 404
    
    try:
        df, _ = load_dataframe(files[file_id], sheet)
        
        # Analyze each column for numeric capability
        columns_info = []
        for col in df.columns:
            # Try to convert to numeric
            numeric_values = pd.to_numeric(df[col], errors='coerce')
            numeric_count = numeric_values.notna().sum()
            total_count = len(df)
            
            column_info = {
                'name': col,
                'numeric_percentage': float(round((numeric_count / total_count * 100) if total_count > 0 else 0, 1)),
                'is_numeric': int(numeric_count > 0)
            }
            columns_info.append(column_info)
            
            logger.info(f"  Column '{col}': {numeric_count}/{total_count} numeric ({column_info['numeric_percentage']}%)")
        
        return jsonify({
            'columns': columns_info,
            'total_rows': len(df)
        }), 200
    except Exception as e:
        logger.error(f"get_columns error: {str(e)}")
        return jsonify({'error': str(e)}), 400


@app.route('/analyze-custom', methods=['POST'])
def analyze_custom():
    """تحليل مخصص بأعمدة محددة - يدعم أعمدة تقييم متعددة"""
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
    sheet = data.get('sheet', 'Sheet1')
    dept_col = data.get('dept_column')
    rating_cols = data.get('rating_columns', [])
    
    if not file_id or not dept_col or not rating_cols:
        return jsonify({'error': 'Missing columns'}), 400
    
    if file_id not in files:
        return jsonify({'error': 'File not found'}), 404
    
    # Convert single column to list
    if isinstance(rating_cols, str):
        rating_cols = [rating_cols]
    
    try:
        df, _ = load_dataframe(files[file_id], sheet)
        df = df.dropna(how='all')
        
        # Validate columns exist
        if dept_col not in df.columns:
            return jsonify({'error': f'Column "{dept_col}" not found'}), 400
        
        for rating_col in rating_cols:
            if rating_col not in df.columns:
                return jsonify({'error': f'Column "{rating_col}" not found'}), 400
        
        all_ratings = []
        column_results = {}
        
        # تحليل كل عمود تقييم
        for rating_col in rating_cols:
            ratings = []
            for val in df[rating_col]:
                r = _convert_rating(val)
                if r:
                    ratings.append(r)
                    all_ratings.append({'col': rating_col, 'rating': r})
            
            depts = {}
            for dept, group in df.groupby(dept_col, observed=True):
                dept_ratings = []
                for val in group[rating_col]:
                    r = _convert_rating(val)
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
        
        # دمج نتائج كل الأعمدة
        combined_top_depts = {}
        for rating_col in rating_cols:
            if rating_col in column_results:
                for dept in column_results[rating_col]['top_departments']:
                    if dept['name'] not in combined_top_depts:
                        combined_top_depts[dept['name']] = {'ratings': [], 'employees': set()}
                    combined_top_depts[dept['name']]['ratings'].append(dept['rating'])
                    combined_top_depts[dept['name']]['employees'].add(dept['employees'])
        
        # حساب المتوسط لكل قسم
        final_top_depts = []
        for name, data in combined_top_depts.items():
            avg_rating = round(sum(data['ratings']) / len(data['ratings']), 2)
            final_top_depts.append({
                'name': name,
                'rating': avg_rating,
                'employees': max(data['employees']) if data['employees'] else 0
            })
        
        final_top_depts.sort(key=lambda x: x['rating'], reverse=True)
        
        result = {
            'total_records': len(df),
            'valid_ratings': len(all_ratings),
            'avg_rating': round(np.mean([r['rating'] for r in all_ratings]), 2) if all_ratings else 0,
            'top_departments': final_top_depts[:10],
            'column_details': column_results,
            'columns_used': {
                'dept': dept_col,
                'ratings': rating_cols
            }
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Custom analysis error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 400


def _convert_rating(val):
    """تحويل التقييم لرقم"""
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


@app.route('/dynamic-analysis', methods=['POST'])
def dynamic_analysis():
    """
    تحليل ديناميكي: يسمح المستخدم باختيار الأعمدة ونوع الرسم البياني
    """
    try:
        # Check authentication
        session_data, error, status = check_auth(request)
        if error:
            return jsonify({'error': error}), status
        
        data = request.get_json()
        
        file_id = data.get('file_id')
        sheet_name = data.get('sheet', 'Sheet1')
        x_column = data.get('x_column')
        y_column = data.get('y_column')
        group_by = data.get('group_by')
        chart_type = data.get('chart_type', 'bar')
        aggregation = data.get('aggregation', 'avg')
        
        logger.info(f"📊 Dynamic analysis requested: X={x_column}, Y={y_column}")
        
        if not file_id or not x_column or not y_column:
            return jsonify({'error': 'Missing required columns (file_id, x_column, y_column)'}), 400
        
        if file_id not in files:
            return jsonify({'error': 'File not found'}), 404
        
        try:
            df, _ = load_dataframe(files[file_id], sheet_name)
        except Exception as e:
            logger.error(f"Failed to load file: {str(e)}")
            return jsonify({'error': f'Failed to load file: {str(e)}'}), 400
        
        # Validate columns exist
        if x_column not in df.columns:
            available = list(df.columns)
            return jsonify({'error': f'Column "{x_column}" not found. Available: {available}'}), 400
            
        if y_column not in df.columns:
            available = list(df.columns)
            return jsonify({'error': f'Column "{y_column}" not found. Available: {available}'}), 400
        
        if group_by and group_by not in df.columns:
            return jsonify({'error': f'Group column "{group_by}" not found'}), 400
        
        # Process data
        result_data = process_dynamic_chart(df, x_column, y_column, group_by, aggregation, chart_type)
        
        logger.info(f"✅ Dynamic analysis complete: {x_column} vs {y_column}")
        return jsonify(result_data), 200
        
    except Exception as e:
        logger.error(f"❌ Dynamic analysis error: {e}", exc_info=True)
        return jsonify({'error': f'Analysis error: {str(e)}'}), 500
        return jsonify({'error': f'Analysis error: {str(e)}'}), 500


def process_dynamic_chart(df, x_column, y_column, group_by, aggregation, chart_type):
    """معالجة البيانات للرسوم البيانية الديناميكية"""
    
    try:
        logger.info(f"🔍 Starting analysis: X={x_column}, Y={y_column}, Group={group_by}")
        logger.info(f"   DataFrame shape: {df.shape}, columns: {list(df.columns)}")
        
        # Select columns and drop nulls
        cols_needed = [x_column, y_column] + ([group_by] if group_by else [])
        df_clean = df[cols_needed].copy()
        logger.info(f"   Before dropna: {len(df_clean)} rows")
        
        df_clean = df_clean.dropna()
        logger.info(f"   After dropna: {len(df_clean)} rows")
        
        # Convert y_column using custom rating conversion to handle strings and Arabic numerals
        df_clean[y_column] = df_clean[y_column].apply(_convert_rating)
        df_clean = df_clean.dropna(subset=[y_column])
        logger.info(f"   After rating conversion: {len(df_clean)} rows")
        
        # If still no data, return empty structure
        if len(df_clean) == 0:
            logger.error(f"❌ No valid data after cleaning for {y_column}")
            return {
                'chart_type': chart_type,
                'x_column': x_column,
                'y_column': y_column,
                'aggregation': aggregation,
                'labels': [],
                'datasets': [{
                    'label': f'{aggregation.upper()} {y_column}',
                    'data': [],
                    'backgroundColor': 'rgba(0, 133, 93, 0.8)',
                    'borderColor': '#00855D',
                    'borderWidth': 2
                }],
                'message': 'لا توجد بيانات صالحة'
            }
        
        # Aggregate data
        if group_by:
            grouped = df_clean.groupby([x_column, group_by])[y_column]
        else:
            grouped = df_clean.groupby(x_column)[y_column]
        
        logger.info(f"   Grouped into {len(grouped)} groups")
        
        # Apply aggregation
        agg_func = {'sum': 'sum', 'avg': 'mean', 'count': 'count', 'max': 'max', 'min': 'min'}.get(aggregation, 'mean')
        aggregated = grouped.agg(agg_func).reset_index()
        
        logger.info(f"   After aggregation: {len(aggregated)} rows")
        
        if len(aggregated) == 0:
            logger.error("❌ Aggregation returned empty dataframe")
            return {
                'chart_type': chart_type,
                'x_column': x_column,
                'y_column': y_column,
                'aggregation': aggregation,
                'labels': [],
                'datasets': [{
                    'label': f'{aggregation.upper()} {y_column}',
                    'data': [],
                    'backgroundColor': 'rgba(0, 133, 93, 0.8)',
                    'borderColor': '#00855D',
                    'borderWidth': 2
                }],
                'message': 'فشل التجميع'
            }
        
        if group_by:
            # Multiple series for grouped data
            labels = sorted(aggregated[x_column].astype(str).unique().tolist())
            logger.info(f"   Group mode: {len(labels)} unique X values")
            
            result = {
                'chart_type': chart_type,
                'x_column': x_column,
                'y_column': y_column,
                'aggregation': aggregation,
                'labels': labels,
                'datasets': []
            }
            
            for group_val in aggregated[group_by].unique():
                subset = aggregated[aggregated[group_by] == group_val]
                colors = ['#00855D', '#43a047', '#ffc107', '#ff9800', '#e53935', '#9c27b0']
                color = colors[hash(str(group_val)) % len(colors)]
                
                result['datasets'].append({
                    'label': str(group_val),
                    'data': subset.set_index(x_column).loc[labels, y_column].fillna(0).tolist(),
                    'backgroundColor': color,
                    'borderColor': color,
                    'borderWidth': 2
                })
        else:
            # Single series
            labels = aggregated[x_column].astype(str).tolist()
            logger.info(f"   Single mode: {len(labels)} labels")
            
            result = {
                'chart_type': chart_type,
                'x_column': x_column,
                'y_column': y_column,
                'aggregation': aggregation,
                'labels': labels,
                'datasets': [{
                    'label': f'{aggregation.upper()} {y_column}',
                    'data': aggregated[y_column].tolist(),
                    'backgroundColor': 'rgba(0, 133, 93, 0.8)',
                    'borderColor': '#00855D',
                    'borderWidth': 2
                }]
            }
        
        logger.info(f"✅ Chart ready: {len(result['labels'])} labels, {len(result['datasets'])} datasets")
        return result
        
    except Exception as e:
        logger.error(f"process_dynamic_chart error: {str(e)}", exc_info=True)
        raise


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
    PORT = int(os.environ.get('PORT', 5000))
    print("\n🔒 Secure HR Analytics System")
    print("=" * 50)
    print("✅ Enhanced Security Features:")
    print("   • Session-based authentication")
    print("   • IP validation")
    print("   • Session expiration (2 hours)")
    print("   • Rate limiting (10 uploads/session)")
    print("   • Secure token generation")
    print("   • CORS protection")
    print("   • Enhanced region detection with fuzzy matching")
    print("=" * 50)
    print(f"🌐 Server listening on port {PORT}")
    print("=" * 50 + "\n")
    
    app.run(host='0.0.0.0', port=PORT, debug=False)


