
// Initialize Session
let sessionToken = null;
let currentFileId = null;
let currentSheetName = 'Sheet1';
let availableColumns = [];
let progressInterval = null;
let rawAnalyticsData = null;
let serverAvailable = true;

// Auto-detect API base URL for both local and production
const API_BASE = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost' 
    ? '' 
    : window.location.origin;

// Loading screen
function showLoadingScreen(text, subtext) {
    const screen = document.getElementById('loadingScreen');
    const textEl = document.getElementById('loadingText');
    const subtextEl = document.getElementById('loadingSubtext');
    if (screen) {
        if (textEl) textEl.textContent = text || 'جاري المعالجة...';
        if (subtextEl) subtextEl.textContent = subtext || 'يرجى الانتظار';
        screen.classList.add('active');
    }
}

function hideLoadingScreen() {
    const screen = document.getElementById('loadingScreen');
    if (screen) screen.classList.remove('active');
}

// Error banner
function showError(message, timeout) {
    try {
        hideLoadingScreen();
        const banner = document.getElementById('error-banner');
        if (!banner) return;
        banner.innerHTML = '<i class="fas fa-exclamation-circle"></i> ' + message;
        banner.style.display = 'block';
        banner.classList.add('visible');
        clearTimeout(banner._hideTimer);
        banner._hideTimer = setTimeout(() => {
            banner.classList.remove('visible');
            banner.style.display = 'none';
        }, timeout || 6000);
    } catch (e) { console.error('UI error:', e); }
}

// Initialize session
async function initSession() {
    console.log('Initializing app...');
    hideLoadingScreen();
    attachEventListeners();
}

// DOM ready - attach all event listeners
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM ready, initializing...');
    buildPageHTML();
    initSession();
    attachEventListeners();
});

// Build the main page structure
function buildPageHTML() {
    const app = document.getElementById('app');
    if (!app) return;
    
    app.innerHTML = `
        <!-- Loading Screen -->
        <div id="loadingScreen">
            <div class="loading-spinner"></div>
            <div id="loadingText">جاري المعالجة...</div>
            <div id="loadingSubtext">يرجى الانتظار</div>
        </div>

        <!-- Error Banner -->
        <div id="error-banner"></div>

        <!-- Header -->
        <header class="header">
            <div class="header-content">
                <div class="header-title">
                    <i class="fas fa-chart-bar"></i>
                    <div>
                        <h1>نظام تحليل الأداء الوظيفي</h1>
                        <p>وزارة التعليم - المملكة العربية السعودية</p>
                    </div>
                </div>
            </div>
        </header>

        <!-- Main Container -->
        <div class="container">
            <!-- Upload Section -->
            <div class="upload-section" onclick="document.getElementById('excel-file').click()">
                <i class="fas fa-cloud-upload-alt"></i>
                <h2>رفع ملف Excel</h2>
                <p>اضغط أو اسحب ملف Excel للبدء في التحليل</p>
                <input type="file" id="excel-file" accept=".xlsx,.xls,.csv" />
            </div>

            <!-- Stats Section -->
            <div id="statsSection" class="stats-section" style="display:none;">
                <div class="stat-card">
                    <i class="fas fa-database"></i>
                    <div>
                        <p>إجمالي السجلات</p>
                        <h3 id="total-records">-</h3>
                    </div>
                </div>
                <div class="stat-card">
                    <i class="fas fa-check-circle"></i>
                    <div>
                        <p>التقييمات الصحيحة</p>
                        <h3 id="valid-ratings">-</h3>
                    </div>
                </div>
                <div class="stat-card">
                    <i class="fas fa-star"></i>
                    <div>
                        <p>متوسط التقييم</p>
                        <h3 id="avg-rating">-</h3>
                    </div>
                </div>
            </div>

            <!-- Charts Section -->
            <div id="chartsSection" style="display:none;">
                <div class="chart-container">
                    <div class="chart-header">
                        <i class="fas fa-chart-bar"></i>
                        <h2>التقييمات حسب الأقسام</h2>
                    </div>
                    <canvas id="departmentsChart" height="300"></canvas>
                </div>

                <div class="chart-container">
                    <div class="chart-header">
                        <i class="fas fa-chart-pie"></i>
                        <h2>توزيع التقييمات</h2>
                    </div>
                    <canvas id="ratingsDistribution" height="300"></canvas>
                </div>

                <div class="chart-container">
                    <div class="chart-header">
                        <i class="fas fa-users"></i>
                        <h2>عدد الموظفين حسب القسم</h2>
                    </div>
                    <canvas id="employeesByDept" height="300"></canvas>
                </div>

                <div class="chart-container">
                    <div class="chart-header">
                        <i class="fas fa-compress"></i>
                        <h2>مقارنة الأداء</h2>
                    </div>
                    <canvas id="performanceComparison" height="300"></canvas>
                </div>
            </div>

            <!-- Cities Chart Section -->
            <div id="citiesChartSection" style="display:none;">
                <div class="chart-container">
                    <div class="chart-header">
                        <i class="fas fa-map-marker-alt"></i>
                        <h2>أداء المدن والمناطق</h2>
                    </div>
                    <canvas id="citiesChart" height="300"></canvas>
                </div>
            </div>

            <!-- Filters Section -->
            <div id="filtersSection" style="display:none;">
                <div class="chart-container">
                    <div class="chart-header">
                        <i class="fas fa-filter"></i>
                        <h2>الفلاتر والتحكم</h2>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;">
                        <div>
                            <label style="font-weight: 600; display: block; margin-bottom: 5px;">المنطقة:</label>
                            <select id="filter-region-main" style="width: 100%; padding: 10px; border: 2px solid #D4E5DD; border-radius: 8px;">
                                <option value="">جميع المناطق</option>
                            </select>
                        </div>
                        <div>
                            <label style="font-weight: 600; display: block; margin-bottom: 5px;">القسم:</label>
                            <select id="filter-department" style="width: 100%; padding: 10px; border: 2px solid #D4E5DD; border-radius: 8px;">
                                <option value="">جميع الأقسام</option>
                            </select>
                        </div>
                        <div>
                            <label style="font-weight: 600; display: block; margin-bottom: 5px;">التقييم من:</label>
                            <input type="number" id="filter-rating-min" min="0" max="5" step="0.1" style="width: 100%; padding: 10px; border: 2px solid #D4E5DD; border-radius: 8px;" />
                        </div>
                        <div>
                            <label style="font-weight: 600; display: block; margin-bottom: 5px;">التقييم إلى:</label>
                            <input type="number" id="filter-rating-max" min="0" max="5" step="0.1" style="width: 100%; padding: 10px; border: 2px solid #D4E5DD; border-radius: 8px;" />
                        </div>
                    </div>
                    
                    <div style="display: flex; gap: 10px;">
                        <button id="apply-filters" class="btn btn-primary" style="flex: 1;">
                            <i class="fas fa-check"></i> تطبيق الفلاتر
                        </button>
                        <button id="reset-filters" class="btn btn-secondary" style="flex: 1;">
                            <i class="fas fa-redo"></i> إعادة تعيين
                        </button>
                        <button id="clear-data" class="btn btn-danger" style="flex: 1;">
                            <i class="fas fa-trash"></i> مسح البيانات
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <div class="footer">
            <p>© 2026 منظومة إدارة الأداء الوظيفي - جميع الحقوق محفوظة</p>
        </div>
    `;
}


function attachEventListeners() {
    const fileInput = document.getElementById('excel-file');
    if (!fileInput) {
        console.error('File input not found');
        showError('عنصر الملف غير موجود');
        return;
    }
    
    fileInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        if (!serverAvailable) {
            showError('⚠️ الخادم لا يستجيب. تأكد من تشغيل:\npython3 app.py');
            return;
        }
        
        showLoadingScreen('جاري رفع الملف...', file.name);
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
        const response = await fetch(`${API_BASE}/upload`, { 
                method: 'POST', 
                body: formData, 
                headers: { 'X-Session-Token': sessionToken } 
            });
            
            if (!response.ok) {
                throw new Error('Upload failed');
            }
            
            const data = await response.json();
            
            if (data.success) {
                currentFileId = data.file_id;
                currentSheetName = data.sheets[0] || 'Sheet1';
                hideLoadingScreen();
                // جلب الأعمدة وعرض نافذة الاختيار
                showColumnSelectionModal(currentSheetName);
            } else {
                throw new Error(data.error || 'Upload failed');
            }
        } catch (error) {
            console.error('Upload error:', error);
            showError('خطأ في الرفع: ' + error.message);
            hideLoadingScreen();
        }
    });
    
    // Clear button
    const clearBtn = document.getElementById('clear-data');
    if (clearBtn) {
        clearBtn.addEventListener('click', clearData);
    }
    
    // Filter buttons
    const applyFiltersBtn = document.getElementById('apply-filters');
    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', applyFilters);
    }
    
    const resetFiltersBtn = document.getElementById('reset-filters');
    if (resetFiltersBtn) {
        resetFiltersBtn.addEventListener('click', resetFilters);
    }
}

// Load analytics
async function loadAnalyticsForSheet(sheetName) {
    showLoadingScreen('جاري تحميل النتائج...', 'الرجاء الانتظار');
    let retries = 0;
    const maxRetries = 20;
    
    async function fetchAnalytics() {
        try {
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), 120000);
            
            const response = await fetch(`${API_BASE}/analytics`, {
                method: 'POST',
                headers: { 
                    'X-Session-Token': sessionToken, 
                    'Content-Type': 'application/json' 
                },
                body: JSON.stringify({ 
                    file_id: currentFileId, 
                    sheet: sheetName 
                }),
                signal: controller.signal
            });
            
            clearTimeout(timeout);
            
            if (response.status === 202) {
                if (retries < maxRetries) { 
                    retries++; 
                    await new Promise(r => setTimeout(r, 1500)); 
                    return fetchAnalytics(); 
                } else {
                    throw new Error('تجاوز زمن المعالجة');
                }
            }
            
            if (!response.ok) {
                throw new Error('Analytics failed: ' + response.status);
            }
            
            const data = await response.json();
            renderDashboard(data);
            
        } catch (error) {
            hideLoadingScreen();
            if (error.name === 'AbortError') {
                showError('انتهت مهلة الانتظار');
            } else {
                showError('خطأ: ' + error.message);
            }
        }
    }
    
    fetchAnalytics();
}

// Render dashboard
function renderDashboard(data) {
    try {
        hideLoadingScreen();
        
        // Guard: ensure data is valid
        if (!data || typeof data !== 'object') {
            showError('خطأ: البيانات المستقبلة غير صحيحة');
            return;
        }
        
        console.log('Rendering dashboard with data:', data);
        
        // Show sections
        const statsSection = document.getElementById('statsSection');
        const chartsSection = document.getElementById('chartsSection');
        const citiesChartSection = document.getElementById('citiesChartSection');
        const filtersSection = document.getElementById('filtersSection');
        
        if (statsSection) statsSection.style.display = 'grid';
        if (chartsSection) chartsSection.style.display = 'block';
        if (citiesChartSection) citiesChartSection.style.display = 'block';
        if (filtersSection) filtersSection.style.display = 'block';
        
        // Stats - guard against missing or undefined values
        if (data.total_records !== undefined) {
            const totalEl = document.getElementById('total-records');
            const validEl = document.getElementById('valid-ratings');
            const avgEl = document.getElementById('avg-rating');
            
            if (totalEl) totalEl.textContent = (data.total_records || 0).toLocaleString('ar-SA');
            if (validEl) validEl.textContent = (data.valid_ratings || 0).toLocaleString('ar-SA');
            if (avgEl) avgEl.textContent = parseFloat(data.avg_rating || 0).toFixed(2);
        }
        
        // Charts - guard against empty or missing departments
        if (data.top_departments && Array.isArray(data.top_departments) && data.top_departments.length > 0) {
            renderDepartmentsChart(data.top_departments);
            renderRatingsDistribution(data.top_departments);
            renderEmployeesByDept(data.top_departments);
            renderPerformanceComparison(data.top_departments);
            renderCitiesChart(data.top_departments);
        } else {
            console.warn('No top_departments data available for charts');
            showError('لا توجد بيانات كافية لعرض الرسوم البيانية');
        }
        
        rawAnalyticsData = data;
        populateFilters(data);
        
        console.log('✓ Dashboard rendered successfully');
        
    } catch (error) {
        console.error('Dashboard render error:', error);
        showError('خطأ في عرض لوحة المعلومات: ' + error.message);
    }
}

// Charts
function renderDepartmentsChart(depts) {
    const ctx = document.getElementById('departmentsChart');
    if (!ctx || !depts || depts.length === 0) {
        console.warn('Cannot render departments chart: missing context or data');
        return;
    }
    
    try {
        const names = depts.map(d => d.name || 'Unknown');
        const ratings = depts.map(d => parseFloat(d.rating) || 0);
        
        if (window.deptChart) {
            try { window.deptChart.destroy(); } catch (e) {}
        }
        
        window.deptChart = new Chart(ctx, {
            type: 'bar',
            data: { 
                labels: names, 
                datasets: [{ 
                    label: 'التقييم', 
                    data: ratings, 
                    backgroundColor: 'rgba(0, 133, 93, 0.8)', 
                    borderColor: '#00855D', 
                    borderWidth: 2 
                }] 
            },
            options: { 
                indexAxis: 'y', 
                responsive: true, 
                maintainAspectRatio: false, 
                scales: { 
                    x: { 
                        beginAtZero: true, 
                        max: 5, 
                        grid: { color: 'rgba(0,0,0,0.05)' } 
                    }, 
                    y: { 
                        grid: { display: false } 
                    } 
                }, 
                plugins: { 
                    legend: { display: false } 
                } 
            }
        });
    } catch (error) {
        console.error('Error rendering departments chart:', error);
    }
}

function renderRatingsDistribution(depts) {
    const ctx = document.getElementById('ratingsDistribution');
    if (!ctx || !depts || depts.length === 0) {
        console.warn('Cannot render ratings chart: missing context or data');
        return;
    }
    
    try {
        const buckets = { 'ممتاز': 0, 'جيد جداً': 0, 'جيد': 0, 'مقبول': 0, 'ضعيف': 0 };
        
        depts.forEach(d => {
            const rating = parseFloat(d.rating) || 0;
            const employees = parseInt(d.employees) || 1;
            if (rating >= 4.5) buckets['ممتاز'] += employees;
            else if (rating >= 3.5) buckets['جيد جداً'] += employees;
            else if (rating >= 2.5) buckets['جيد'] += employees;
            else if (rating >= 1.5) buckets['مقبول'] += employees;
            else buckets['ضعيف'] += employees;
        });
        
        if (window.ratingsChart) {
            try { window.ratingsChart.destroy(); } catch (e) {}
        }
        
        window.ratingsChart = new Chart(ctx, {
            type: 'doughnut',
            data: { 
                labels: Object.keys(buckets), 
                datasets: [{ 
                    data: Object.values(buckets), 
                    backgroundColor: ['#00855D', '#43a047', '#ffc107', '#ff9800', '#e53935'], 
                    borderWidth: 3, 
                    borderColor: '#fff' 
                }] 
            },
            options: { 
                responsive: true, 
                maintainAspectRatio: false, 
                plugins: { 
                    legend: { 
                        position: 'bottom', 
                        labels: { padding: 10 } 
                    } 
                } 
            }
        });
    } catch (error) {
        console.error('Error rendering ratings chart:', error);
    }
}

function renderEmployeesByDept(depts) {
    const ctx = document.getElementById('employeesByDept');
    if (!ctx || !depts || depts.length === 0) {
        console.warn('Cannot render employees chart: missing context or data');
        return;
    }
    
    try {
        const names = depts.map(d => d.name || 'Unknown');
        const employees = depts.map(d => parseInt(d.employees) || 0);
        
        if (window.empChart) {
            try { window.empChart.destroy(); } catch (e) {}
        }
        
        window.empChart = new Chart(ctx, {
            type: 'bar',
            data: { 
                labels: names, 
                datasets: [{ 
                    label: 'الموظفين', 
                    data: employees, 
                    backgroundColor: 'rgba(184, 134, 11, 0.8)', 
                    borderColor: '#B8860B', 
                    borderWidth: 2 
                }] 
            },
            options: { 
                responsive: true, 
                maintainAspectRatio: false, 
                scales: { 
                    y: { 
                        beginAtZero: true, 
                        grid: { color: 'rgba(0,0,0,0.05)' } 
                    }, 
                    x: { 
                        grid: { display: false }, 
                        ticks: { maxRotation: 45 } 
                    } 
                }, 
                plugins: { 
                    legend: { display: false } 
                } 
            } 
        });
    } catch (error) {
        console.error('Error rendering employees chart:', error);
    }
}

function renderPerformanceComparison(depts) {
    const ctx = document.getElementById('performanceComparison');
    if (!ctx || !depts || depts.length === 0) {
        console.warn('Cannot render performance chart: missing context or data');
        return;
    }
    
    try {
        if (window.perfChart) {
            try { window.perfChart.destroy(); } catch (e) {}
        }
        
        const scatterData = depts
            .filter(d => d.employees && d.rating !== undefined)
            .map(d => ({ 
                x: parseInt(d.employees) || 0, 
                y: parseFloat(d.rating) || 0 
            }));
        
        window.perfChart = new Chart(ctx, {
            type: 'scatter',
            data: { 
                datasets: [{ 
                    label: 'الأقسام', 
                    data: scatterData, 
                    backgroundColor: 'rgba(255, 193, 7, 0.8)', 
                    borderColor: '#ffc107', 
                    borderWidth: 2, 
                    pointRadius: 10 
                }] 
            },
            options: { 
                responsive: true, 
                maintainAspectRatio: false, 
                scales: { 
                    x: { 
                        title: { display: true, text: 'الموظفين' }, 
                        grid: { color: 'rgba(0,0,0,0.05)' } 
                    }, 
                    y: { 
                        title: { display: true, text: 'التقييم' }, 
                        beginAtZero: true, 
                        max: 5, 
                        grid: { color: 'rgba(0,0,0,0.05)' } 
                    } 
                }, 
                plugins: { 
                    legend: { display: false }
                } 
            }
        });
    } catch (error) {
        console.error('Error rendering performance chart:', error);
    }
}

// Cities Chart - أداء المدن
function renderCitiesChart(depts) {
    const ctx = document.getElementById('citiesChart');
    if (!ctx || !depts || depts.length === 0) {
        console.warn('Cannot render cities chart: missing context or data');
        return;
    }
    
    try {
        // Group by city (extract city from department name)
        const cityData = {};
        depts.forEach(d => {
            const city = extractCityFromName(d.name) || 'أخرى';
            if (!cityData[city]) {
                cityData[city] = { totalRating: 0, count: 0, employees: 0 };
            }
            const rating = parseFloat(d.rating) || 0;
            const employees = parseInt(d.employees) || 1;
            cityData[city].totalRating += rating * employees;
            cityData[city].count += 1;
            cityData[city].employees += employees;
        });
        
        const cities = Object.keys(cityData);
        if (cities.length === 0) {
            console.warn('No cities data available');
            return;
        }
        
        const avgRatings = cities.map(c => cityData[c].totalRating / Math.max(cityData[c].employees, 1));
        const employees = cities.map(c => cityData[c].employees);
        
        if (window.citiesChart) {
            try { window.citiesChart.destroy(); } catch (e) {}
        }
        
        window.citiesChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: cities,
                datasets: [
                    {
                        label: 'متوسط التقييم',
                        data: avgRatings,
                        backgroundColor: 'rgba(0, 133, 93, 0.8)',
                        borderColor: '#00855D',
                        borderWidth: 2,
                        yAxisID: 'y'
                    },
                    {
                        label: 'عدد الموظفين',
                        data: employees,
                        backgroundColor: 'rgba(184, 134, 11, 0.8)',
                        borderColor: '#B8860B',
                        borderWidth: 2,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        type: 'linear',
                        position: 'right',
                        title: { display: true, text: 'التقييم', color: '#00855D' },
                        beginAtZero: true,
                        max: 5,
                        grid: { color: 'rgba(0,0,0,0.05)' }
                    },
                    y1: {
                        type: 'linear',
                        position: 'left',
                        title: { display: true, text: 'الموظفين', color: '#B8860B' },
                        beginAtZero: true,
                        grid: { display: false }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { maxRotation: 45 }
                    }
                },
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error rendering cities chart:', error);
    }
}

// Helper to extract city name from department name
function extractCityFromName(name) {
    if (!name) return null;
    
    const saudiCities = [
        'الرياض', 'جدة', 'مكة', 'المدينة', 'الدمام', 'الخبر', 'الظهران',
        'تبوك', 'أبها', 'خميس مشيط', 'جازان', 'ينبع', 'الطائف', 'عرعر',
        'سكاكا', 'حفر الباطن', 'الجبيل', 'القطيف', 'نجران', 'الباحة',
        'رابغ', 'المدينة المنورة', 'مكة المكرمة'
    ];
    
    for (const city of saudiCities) {
        if (name.includes(city)) return city;
    }
    return null;
}

// Clear data
async function clearData() {
    try {
        const response = await fetch(`${API_BASE}/clear`, { 
            method: 'POST',
            headers: { 'X-Session-Token': sessionToken } 
        });
        
        if (response.ok) {
            currentFileId = null;
            rawAnalyticsData = null;
            document.getElementById('excel-file').value = '';
            
            ['statsSection', 'chartsSection', 'citiesChartSection', 'filtersSection'].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.style.display = 'none';
            });
            
            ['total-records', 'valid-ratings', 'avg-rating'].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.textContent = '-';
            });
            
            ['deptChart', 'ratingsChart', 'empChart', 'perfChart', 'citiesChart'].forEach(chart => {
                if (window[chart]) { window[chart].destroy(); window[chart] = null; }
            });
            
            showError('✓ تم مسح البيانات', 3000);
        }
    } catch (error) { 
        showError('حدث خطأ: ' + error.message, 3000); 
    }
}

// Populate filters
function populateFilters(data) {
    const deptSelect = document.getElementById('filter-department');
    const regionSelect = document.getElementById('filter-region-main');
    
    if (deptSelect) {
        deptSelect.innerHTML = '<option value="">الكل</option>';
        if (data.top_departments) {
            data.top_departments.forEach(dept => {
                const option = document.createElement('option');
                option.value = dept.name;
                option.textContent = dept.name;
                deptSelect.appendChild(option);
            });
        }
    }
    
    if (regionSelect) {
        regionSelect.innerHTML = '<option value="">جميع المناطق</option>';
        // Add unique regions from department names
        const cities = new Set();
        if (data.top_departments) {
            data.top_departments.forEach(dept => {
                const city = extractCityFromName(dept.name);
                if (city) cities.add(city);
            });
        }
        Array.from(cities).sort().forEach(city => {
            const option = document.createElement('option');
            option.value = city;
            option.textContent = city;
            regionSelect.appendChild(option);
        });
    }
}

// Apply filters
function applyFilters() {
    if (!rawAnalyticsData) { 
        showError('لا توجد بيانات', 3000); 
        return; 
    }
    
    const regionMain = document.getElementById('filter-region-main').value;
    const department = document.getElementById('filter-department').value;
    const ratingMin = parseFloat(document.getElementById('filter-rating-min').value) || 0;
    const ratingMax = parseFloat(document.getElementById('filter-rating-max').value) || 5;
    
    let filteredDepts = rawAnalyticsData.top_departments || [];
    
    // Apply region filter
    if (regionMain) {
        filteredDepts = filteredDepts.filter(d => extractCityFromName(d.name) === regionMain);
    }
    
    // Apply department filter
    if (department) {
        filteredDepts = filteredDepts.filter(d => d.name === department);
    }
    
    // Apply rating filter
    filteredDepts = filteredDepts.filter(d => d.rating >= ratingMin && d.rating <= ratingMax);
    
    // Calculate stats
    const totalEmployees = filteredDepts.reduce((sum, d) => sum + d.employees, 0);
    const avgRating = filteredDepts.length > 0 ? filteredDepts.reduce((sum, d) => sum + (d.rating * d.employees), 0) / totalEmployees : 0;
    
    document.getElementById('total-records').textContent = totalEmployees.toLocaleString();
    document.getElementById('valid-ratings').textContent = totalEmployees.toLocaleString();
    document.getElementById('avg-rating').textContent = avgRating.toFixed(2);
    
    renderDepartmentsChart(filteredDepts);
    renderRatingsDistribution(filteredDepts);
    renderEmployeesByDept(filteredDepts);
    renderPerformanceComparison(filteredDepts);
    renderCitiesChart(filteredDepts);
    
    showError('✓ تم تطبيق الفلاتر', 2000);
}

// Reset filters
function resetFilters() {
    document.getElementById('filter-region-main').selectedIndex = 0;
    document.getElementById('filter-department').selectedIndex = 0;
    document.getElementById('filter-city').selectedIndex = 0;
    document.getElementById('filter-rating-min').value = '';
    document.getElementById('filter-rating-max').value = '';
    
    if (rawAnalyticsData) {
        document.getElementById('total-records').textContent = rawAnalyticsData.total_records.toLocaleString();
        document.getElementById('valid-ratings').textContent = rawAnalyticsData.valid_ratings.toLocaleString();
        document.getElementById('avg-rating').textContent = rawAnalyticsData.avg_rating.toFixed(2);
        renderDepartmentsChart(rawAnalyticsData.top_departments);
        renderRatingsDistribution(rawAnalyticsData.top_departments);
        renderEmployeesByDept(rawAnalyticsData.top_departments);
        renderPerformanceComparison(rawAnalyticsData.top_departments);
        renderCitiesChart(rawAnalyticsData.top_departments);
        showError('✓ تم إعادة تعيين', 2000);
    }
}

// نافذة اختيار الأعمدة
async function showColumnSelectionModal(sheetName) {
    try {
        showLoadingScreen('جاري جلب الأعمدة...', '');
        
        const response = await fetch(`${API_BASE}/get-columns`, {
            method: 'POST',
            headers: {
                'X-Session-Token': sessionToken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                file_id: currentFileId,
                sheet: sheetName
            })
        });
        
        hideLoadingScreen();
        
        if (!response.ok) {
            throw new Error('Failed to get columns');
        }
        
        const data = await response.json();
        // Extract column names from column objects {name, numeric_percentage, is_numeric}
        const columnObjects = data.columns || [];
        availableColumns = columnObjects.map(c => c.name || c);
        
        // إنشاء نافذة الاختيار
        createColumnSelectionUI(availableColumns);
        
    } catch (error) {
        console.error('Error getting columns:', error);
        showError('خطأ في جلب الأعمدة: ' + error.message);
    }
}

function createColumnSelectionUI(columns) {
    // إزالة نافذة قديمة إن وجدت
    const existingModal = document.getElementById('column-modal');
    if (existingModal) existingModal.remove();
    
    // إنشاء النافذة
    const modal = document.createElement('div');
    modal.id = 'column-modal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.6);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
    `;
    
    const content = document.createElement('div');
    content.style.cssText = `
        background: white;
        border-radius: 16px;
        padding: 30px;
        max-width: 550px;
        width: 90%;
        max-height: 80vh;
        overflow-y: auto;
    `;
    
    content.innerHTML = `
        <h2 style="color: #00855D; margin-bottom: 20px; text-align: center;">
            <i class="fas fa-columns"></i> اختيار الأعمدة للتحليل
        </h2>
        <p style="color: #666; margin-bottom: 20px; text-align: center;">
            يمكنك اختيار أكثر من عمود تقييم للمقارنة
        </p>
        
        <div style="margin-bottom: 15px;">
            <label style="display: block; font-weight: bold; margin-bottom: 8px; color: #1B4D3E;">
                <i class="fas fa-building"></i> عمود الإدارة/القسم:
            </label>
            <select id="dept-column-select" style="
                width: 100%;
                padding: 12px;
                border: 2px solid #D4E5DD;
                border-radius: 10px;
                font-family: 'Cairo', sans-serif;
                font-size: 14px;
            ">
                <option value="">-- اختر العمود --</option>
                ${columns.map(col => `<option value="${col}">${col}</option>`).join('')}
            </select>
        </div>
        
        <div style="margin-bottom: 20px;">
            <label style="display: block; font-weight: bold; margin-bottom: 10px; color: #1B4D3E;">
                <i class="fas fa-star"></i> أعمدة التقييم (اختر واحد أو أكثر):
            </label>
            <div id="rating-columns-checkboxes" style="
                max-height: 200px;
                overflow-y: auto;
                border: 2px solid #D4E5DD;
                border-radius: 10px;
                padding: 10px;
            ">
                ${columns.map((col, idx) => `
                    <label style="
                        display: flex;
                        align-items: center;
                        gap: 10px;
                        padding: 8px;
                        cursor: pointer;
                        border-radius: 6px;
                        transition: background 0.2s;
                    " onmouseover="this.style.background='#E8F5E9'" onmouseout="this.style.background='transparent'">
                        <input type="checkbox" 
                            class="rating-col-checkbox" 
                            value="${col}" 
                            style="width: 18px; height: 18px; accent-color: #00855D;"
                            ${idx === 0 ? 'checked' : ''}>
                        <span style="font-family: 'Cairo', sans-serif;">${col}</span>
                    </label>
                `).join('')}
            </div>
            <p style="font-size: 12px; color: #888; margin-top: 5px;">
                <i class="fas fa-info-circle"></i> يمكنك تحديد عدة أعمدة للمقارنة
            </p>
        </div>
        
        <div style="display: flex; gap: 10px; justify-content: center;">
            <button id="cancel-columns-btn" style="
                padding: 12px 24px;
                background: #E8F5E9;
                color: #1B4D3E;
                border: none;
                border-radius: 10px;
                font-family: 'Cairo', sans-serif;
                font-weight: 600;
                cursor: pointer;
            ">
                <i class="fas fa-times"></i> إلغاء
            </button>
            <button id="confirm-columns-btn" style="
                padding: 12px 24px;
                background: #00855D;
                color: white;
                border: none;
                border-radius: 10px;
                font-family: 'Cairo', sans-serif;
                font-weight: 600;
                cursor: pointer;
            ">
                <i class="fas fa-check"></i> تحليل
            </button>
        </div>
    `;
    
    modal.appendChild(content);
    document.body.appendChild(modal);
    
    // أحداث الأزرار
    document.getElementById('cancel-columns-btn').onclick = () => {
        modal.remove();
        currentFileId = null;
        document.getElementById('excel-file').value = '';
    };
    
    document.getElementById('confirm-columns-btn').onclick = () => {
        const deptCol = document.getElementById('dept-column-select').value;
        
        // جلب الأعمدة المحددة
        const ratingCheckboxes = document.querySelectorAll('.rating-col-checkbox:checked');
        const ratingCols = Array.from(ratingCheckboxes).map(cb => cb.value);
        
        if (!deptCol || ratingCols.length === 0) {
            showError('الرجاء اختيار القسم وعمود تقييم واحد على الأقل');
            return;
        }
        
        modal.remove();
        runCustomAnalysis(deptCol, ratingCols);
    };
}

// تشغيل التحليل بالأعمدة المحددة
async function runCustomAnalysis(deptCol, ratingCols) {
    showLoadingScreen('جاري التحليل...', 'الرجاء الانتظار');
    
    try {
        const response = await fetch(`${API_BASE}/analyze-custom`, {
            method: 'POST',
            headers: {
                'X-Session-Token': sessionToken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                file_id: currentFileId,
                sheet: currentSheetName,
                dept_column: deptCol,
                rating_columns: ratingCols
            })
        });
        
        if (!response.ok) {
            throw new Error('Analysis failed');
        }
        
        const data = await response.json();
        renderDashboard(data);
        
    } catch (error) {
        console.error('Analysis error:', error);
        showError('خطأ في التحليل: ' + error.message);
        hideLoadingScreen();
    }
}

console.log('✓ HR Analytics script loaded');
