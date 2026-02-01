// Initialize
let sessionToken = null;
let currentFileId = null;
let currentSheetName = 'Sheet1';
let availableColumns = [];
let currentData = null;

// API Configuration
const API_BASE = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost' 
    ? 'http://127.0.0.1:8080' 
    : 'https://job-performance.onrender.com';

// ============= Local Storage Management =============

function saveToken(token) {
    localStorage.setItem('sessionToken', token);
}

function getToken() {
    return localStorage.getItem('sessionToken');
}

function clearToken() {
    localStorage.removeItem('sessionToken');
}

function isLoggedIn() {
    return !!getToken();
}

// ============= UI Functions =============

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

// ============= Page Navigation =============

function showLoginPage() {
    const app = document.getElementById('app');
    if (!app) return;
    
    app.innerHTML = `
        <div style="
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #00855D 0%, #006B4A 50%, #1B4D3E 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        ">
            <div style="
                background: white;
                border-radius: 20px;
                padding: 50px 40px;
                max-width: 400px;
                width: 90%;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            ">
                <div style="text-align: center; margin-bottom: 40px;">
                    <i class="fas fa-lock" style="font-size: 50px; color: #00855D; margin-bottom: 15px;"></i>
                    <h1 style="color: #1B4D3E; margin: 0; font-size: 28px;">تسجيل الدخول</h1>
                    <p style="color: #4A5D56; margin: 10px 0 0 0;">نظام تحليل الأداء الوظيفي</p>
                </div>
                
                <form id="login-form" style="display: flex; flex-direction: column; gap: 20px;">
                    <div>
                        <label style="display: block; font-weight: 600; margin-bottom: 8px; color: #1B4D3E;">
                            <i class="fas fa-user"></i> اسم المستخدم
                        </label>
                        <input type="text" id="username-input" placeholder="أدخل اسم المستخدم" style="
                            width: 100%;
                            padding: 12px;
                            border: 2px solid #D4E5DD;
                            border-radius: 10px;
                            font-family: 'Cairo', sans-serif;
                            font-size: 14px;
                        " autocomplete="username" required>
                    </div>
                    
                    <div>
                        <label style="display: block; font-weight: 600; margin-bottom: 8px; color: #1B4D3E;">
                            <i class="fas fa-key"></i> كلمة المرور
                        </label>
                        <input type="password" id="password-input" placeholder="أدخل كلمة المرور" style="
                            width: 100%;
                            padding: 12px;
                            border: 2px solid #D4E5DD;
                            border-radius: 10px;
                            font-family: 'Cairo', sans-serif;
                            font-size: 14px;
                        " autocomplete="current-password" required>
                    </div>
                    
                    <button type="submit" style="
                        padding: 14px;
                        background: #00855D;
                        color: white;
                        border: none;
                        border-radius: 10px;
                        font-family: 'Cairo', sans-serif;
                        font-weight: 600;
                        font-size: 15px;
                        cursor: pointer;
                        transition: all 0.3s;
                    " onmouseover="this.style.background='#006B4A'" onmouseout="this.style.background='#00855D'">
                        <i class="fas fa-sign-in-alt"></i> دخول
                    </button>
                </form>
                
                <p style="color: #4A5D56; font-size: 12px; text-align: center; margin-top: 20px;">
                    <i class="fas fa-shield-alt"></i> هذا النظام محمي بكلمات مرور آمنة
                </p>
            </div>
        </div>
    `;
    
    document.getElementById('login-form').addEventListener('submit', handleLogin);
}

function showDashboard() {
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
                <div class="header-actions">
                    <span id="username-display" style="color: white; margin-right: 15px;"></span>
                    <button class="btn btn-secondary" id="logout-btn">
                        <i class="fas fa-sign-out-alt"></i> خروج
                    </button>
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
            
            <!-- Chart Container -->
            <div class="chart-container" id="chartContainer-wrapper">
                <div class="chart-header">
                    <i class="fas fa-chart-line"></i>
                    <h2>التحليل الديناميكي</h2>
                </div>
                <div id="chartContainer"></div>
                <div id="chartControls" class="chart-controls"></div>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <p>© 2026 منظومة إدارة الأداء الوظيفي - جميع الحقوق محفوظة</p>
        </div>
    `;
    
    // Add event listeners
    document.getElementById('excel-file').addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) handleFileUpload(file);
    });
    
    document.getElementById('logout-btn').addEventListener('click', handleLogout);
    
    // Update username display
    checkAuthStatus();
}

// ============= Authentication =============

async function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('username-input').value.trim();
    const password = document.getElementById('password-input').value.trim();
    
    if (!username || !password) {
        showError('❌ يرجى إدخال اسم المستخدم وكلمة المرور');
        return;
    }
    
    showLoadingScreen('جاري التحقق...', 'يرجى الانتظار');
    
    try {
        const response = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            hideLoadingScreen();
            showError(`❌ ${data.error || 'فشل تسجيل الدخول'}`);
            return;
        }
        
        sessionToken = data.session_token;
        saveToken(sessionToken);
        
        hideLoadingScreen();
        showDashboard();
        
    } catch (error) {
        hideLoadingScreen();
        showError(`❌ خطأ في الاتصال: ${error.message}`);
    }
}

async function handleLogout() {
    showLoadingScreen('جاري تسجيل الخروج...', 'يرجى الانتظار');
    
    try {
        await fetch(`${API_BASE}/logout`, {
            method: 'POST',
            headers: { 'X-Session-Token': sessionToken }
        });
    } catch (e) {
        console.log('Logout request failed, clearing local token');
    }
    
    sessionToken = null;
    clearToken();
    hideLoadingScreen();
    showLoginPage();
}

async function checkAuthStatus() {
    try {
        const response = await fetch(`${API_BASE}/auth-check`, {
            method: 'GET',
            headers: { 'X-Session-Token': sessionToken }
        });
        
        if (response.ok) {
            const data = await response.json();
            const usernameDisplay = document.getElementById('username-display');
            if (usernameDisplay) {
                usernameDisplay.textContent = `مرحباً ${data.username} 👋`;
            }
        }
    } catch (e) {
        console.error('Auth check failed:', e);
    }
}

// ============= File Upload =============

async function handleFileUpload(file) {
    if (!sessionToken) {
        showError('❌ لم تقم بتسجيل الدخول');
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
        
        console.log('Upload response status:', response.status);
        
        if (response.status === 401) {
            // Session expired or invalid - clear and redirect to login
            console.warn('Session invalid - redirecting to login');
            clearToken();
            sessionToken = null;
            hideLoadingScreen();
            showError('❌ انتهت جلسة المستخدم - يرجى تسجيل الدخول مرة أخرى');
            setTimeout(() => showLoginPage(), 2000);
            return;
        }
        
        if (!response.ok) {
            const errorData = await response.json();
            console.error('Upload error response:', errorData);
            throw new Error(errorData.error || 'Upload failed');
        }
        
        const data = await response.json();
        console.log('Upload success response:', data);
        
        if (data.success && data.columns) {
            currentFileId = data.file_id;
            currentSheetName = data.sheets[0] || 'Sheet1';
            hideLoadingScreen();
            showChartBuilderModal(data.columns);
        } else {
            throw new Error(data.error || 'Upload returned invalid data');
        }
    } catch (error) {
        console.error('Upload error:', error);
        hideLoadingScreen();
        showError('❌ خطأ في الرفع: ' + error.message);
    }
}

// ============= Chart Builder Modal =============

function showChartBuilderModal(columns) {
    console.log('🚀 showChartBuilderModal called with:', columns);
    
    // Validate columns
    if (!Array.isArray(columns) || columns.length === 0) {
        showError('❌ لا توجد أعمدة متاحة في الملف');
        console.error('Invalid columns array:', columns);
        return;
    }
    
    // Check if columns is array of objects (with type info) or strings
    const isColumnInfo = columns.length > 0 && typeof columns[0] === 'object';
    const columnNames = isColumnInfo ? columns.map(c => c.name) : columns;
    const numericColumns = isColumnInfo ? columns.filter(c => c.is_numeric === 1 || c.is_numeric === true).map(c => c.name) : columnNames;
    
    console.log('📊 Column info:', { isColumnInfo, columnNames, numericColumns });
    
    const existingModal = document.getElementById('chart-builder-modal');
    if (existingModal) existingModal.remove();
    
    const modal = document.createElement('div');
    modal.id = 'chart-builder-modal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.7);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        overflow-y: auto;
    `;
    
    const content = document.createElement('div');
    content.style.cssText = `
        background: linear-gradient(135deg, #ffffff 0%, #f5f5f5 100%);
        border-radius: 20px;
        padding: 40px;
        max-width: 650px;
        width: 90%;
        margin: 20px auto;
        box-shadow: 0 10px 40px rgba(0,0,0,0.3);
    `;
    
    // Build column options HTML with info badges
    const buildColumnOption = (colName) => {
        const colInfo = isColumnInfo ? columns.find(c => c.name === colName) : null;
        const isNumeric = colInfo?.is_numeric || false;
        const numericPct = colInfo?.numeric_percentage || 0;
        const badge = isNumeric ? `<span style="font-size: 10px; background: #43a047; color: white; padding: 2px 6px; border-radius: 3px; margin-right: 8px;">${numericPct}% رقمي</span>` : '';
        return `<option value="${colName}">${colName} ${badge}</option>`;
    };
    
    content.innerHTML = `
        <div style="text-align: center; margin-bottom: 30px;">
            <h2 style="color: #00855D; margin: 0; font-size: 28px;">
                <i class="fas fa-chart-bar"></i> بناء رسم بياني
            </h2>
            <p style="color: #666; margin: 10px 0 0 0;">اختر الأعمدة والخيارات لإنشاء رسم بياني مخصص</p>
            ${numericColumns.length < columnNames.length ? `<p style="color: #ff9800; margin: 10px 0 0 0; font-size: 12px;"><i class="fas fa-info-circle"></i> ⚠️ بعض الأعمدة تحتوي على نصوص</p>` : ''}
        </div>
        
        <div style="margin-bottom: 25px;">
            <label style="display: block; font-weight: 600; margin-bottom: 10px; color: #1B4D3E;">
                <i class="fas fa-arrows-alt-h"></i> المحور الأفقي (X):
            </label>
            <select id="x-column-select" style="
                width: 100%;
                padding: 12px;
                border: 2px solid #D4E5DD;
                border-radius: 10px;
                font-family: 'Cairo', sans-serif;
                font-size: 14px;
                background: white;
            ">
                <option value="">-- اختر العمود --</option>
                ${columnNames.map(col => `<option value="${col}">${col}</option>`).join('')}
            </select>
        </div>
            
        <div style="margin-bottom: 25px;">
            <label style="display: block; font-weight: 600; margin-bottom: 10px; color: #1B4D3E;">
                <i class="fas fa-arrows-alt-v"></i> الأعمدة المراد عرضها (Y) - اختر أعمدة رقمية:
            </label>
            <div id="y-columns-container" style="display: grid; gap: 8px; max-height: 200px; overflow-y: auto; padding: 10px; border: 2px solid #D4E5DD; border-radius: 8px; background: white;">
                ${columnNames.map(col => {
                    const colInfo = isColumnInfo ? columns.find(c => c.name === col) : null;
                    const isNumeric = colInfo && (colInfo.is_numeric === 1 || colInfo.is_numeric === true);
                    const numericPct = colInfo?.numeric_percentage || 0;
                    const style = !isNumeric ? 'opacity: 0.5;' : '';
                    const badge = isNumeric ? `<span style="font-size: 10px; background: #43a047; color: white; padding: 2px 6px; border-radius: 3px;">${numericPct}%</span>` : '<span style="font-size: 10px; background: #ccc; color: #666; padding: 2px 6px; border-radius: 3px;">نص</span>';
                    return `
                        <label style="display: flex; align-items: center; gap: 8px; cursor: pointer; padding: 6px; border-radius: 6px; transition: all 0.2s; ${style}">
                            <input type="checkbox" value="${col}" ${!isNumeric ? 'disabled' : ''} style="width: 16px; height: 16px; accent-color: #00855D;">
                            <span style="font-family: 'Cairo', sans-serif; flex: 1;">${col}</span>
                            ${badge}
                        </label>
                    `;
                }).join('')}
            </div>
        </div>
        
        <div style="margin-bottom: 25px;">
            <label style="display: block; font-weight: 600; margin-bottom: 10px; color: #1B4D3E;">
                <i class="fas fa-layer-group"></i> تجميع حسب (اختياري):
            </label>
            <select id="group-by-select" style="
                width: 100%;
                padding: 12px;
                border: 2px solid #D4E5DD;
                border-radius: 10px;
                font-family: 'Cairo', sans-serif;
                font-size: 14px;
                background: white;
            ">
                <option value="">-- بدون تجميع --</option>
                ${columnNames.map(col => `<option value="${col}">${col}</option>`).join('')}
            </select>
        </div>
        
        <div style="margin-bottom: 25px;">
            <label style="display: block; font-weight: 600; margin-bottom: 10px; color: #1B4D3E;">
                <i class="fas fa-palette"></i> نوع الرسم البياني:
            </label>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">
                <label style="display: flex; align-items: center; gap: 10px; padding: 10px; border: 2px solid #D4E5DD; border-radius: 8px; cursor: pointer; background: white;">
                    <input type="radio" name="chart-type" value="bar" checked style="width: 18px; height: 18px; accent-color: #00855D;">
                    <span style="font-family: 'Cairo', sans-serif; font-weight: 500;">📊 أعمدة</span>
                </label>
                <label style="display: flex; align-items: center; gap: 10px; padding: 10px; border: 2px solid #D4E5DD; border-radius: 8px; cursor: pointer; background: white;">
                    <input type="radio" name="chart-type" value="line" style="width: 18px; height: 18px; accent-color: #00855D;">
                    <span style="font-family: 'Cairo', sans-serif; font-weight: 500;">📈 خطوط</span>
                </label>
                <label style="display: flex; align-items: center; gap: 10px; padding: 10px; border: 2px solid #D4E5DD; border-radius: 8px; cursor: pointer; background: white;">
                    <input type="radio" name="chart-type" value="pie" style="width: 18px; height: 18px; accent-color: #00855D;">
                    <span style="font-family: 'Cairo', sans-serif; font-weight: 500;">🥧 دائرة</span>
                </label>
                <label style="display: flex; align-items: center; gap: 10px; padding: 10px; border: 2px solid #D4E5DD; border-radius: 8px; cursor: pointer; background: white;">
                    <input type="radio" name="chart-type" value="scatter" style="width: 18px; height: 18px; accent-color: #00855D;">
                    <span style="font-family: 'Cairo', sans-serif; font-weight: 500;">⚫ نقاط</span>
                </label>
            </div>
        </div>
        
        <div style="margin-bottom: 30px;">
            <label style="display: block; font-weight: 600; margin-bottom: 10px; color: #1B4D3E;">
                <i class="fas fa-calculator"></i> طريقة التجميع:
            </label>
            <select id="aggregation-select" style="
                width: 100%;
                padding: 12px;
                border: 2px solid #D4E5DD;
                border-radius: 10px;
                font-family: 'Cairo', sans-serif;
                font-size: 14px;
                background: white;
            ">
                <option value="avg" selected>متوسط (Average)</option>
                <option value="sum">المجموع (Sum)</option>
                <option value="count">العدد (Count)</option>
                <option value="max">الأقصى (Max)</option>
                <option value="min">الأدنى (Min)</option>
            </select>
        </div>
        
        <div style="display: flex; gap: 10px; justify-content: center;">
            <button id="cancel-chart-builder-btn" style="
                padding: 14px 28px;
                background: #E8F5E9;
                color: #1B4D3E;
                border: none;
                border-radius: 10px;
                font-family: 'Cairo', sans-serif;
                font-weight: 600;
                font-size: 15px;
                cursor: pointer;
            ">
                <i class="fas fa-times"></i> إلغاء
            </button>
            <button id="create-chart-btn" style="
                padding: 14px 28px;
                background: #00855D;
                color: white;
                border: none;
                border-radius: 10px;
                font-family: 'Cairo', sans-serif;
                font-weight: 600;
                font-size: 15px;
                cursor: pointer;
            ">
                <i class="fas fa-chart-line"></i> إنشاء الرسم البياني
            </button>
        </div>
    `;
    
    modal.appendChild(content);
    document.body.appendChild(modal);
    
    document.getElementById('cancel-chart-builder-btn').onclick = () => {
        modal.remove();
        currentFileId = null;
        document.getElementById('excel-file').value = '';
    };
    
    document.getElementById('create-chart-btn').onclick = async () => {
        const xCol = document.getElementById('x-column-select').value;
        const yCheckboxes = Array.from(document.querySelectorAll('#y-columns-container input[type="checkbox"]:checked'));
        const yColumns = yCheckboxes.map(cb => cb.value);
        const groupBy = document.getElementById('group-by-select').value || null;
        const chartType = document.querySelector('input[name="chart-type"]:checked').value;
        const aggregation = document.getElementById('aggregation-select').value;
        
        // Validation
        if (!xCol) {
            showError('❌ يرجى اختيار المحور الأفقي (X)');
            return;
        }
        
        if (yColumns.length === 0) {
            showError('❌ يرجى اختيار عمود واحد على الأقل للمحور العمودي (Y)\n💡 تأكد من اختيار أعمدة رقمية (بها نسبة أعلى من 0%)');
            return;
        }
        
        // Check for numeric data
        const disabledCheckboxes = yCheckboxes.filter(cb => cb.disabled);
        if (disabledCheckboxes.length > 0) {
            const textColumns = disabledCheckboxes.map(cb => cb.value);
            showError(`⚠️ الأعمدة المختارة تحتوي على نصوص: ${textColumns.join(', ')}\nاختر أعمدة رقمية فقط`);
            return;
        }
        
        modal.remove();
        
        // If single Y column, use old flow
        if (yColumns.length === 1) {
            await runDynamicAnalysis(xCol, yColumns[0], groupBy, chartType, aggregation);
        } else {
            // Multiple Y columns - create multi-column chart
            await runMultiColumnAnalysis(xCol, yColumns, chartType, aggregation);
        }
    };
}

// ============= Dynamic Analysis =============

async function runMultiColumnAnalysis(xCol, yColumns, chartType, aggregation) {
    showLoadingScreen('جاري التحليل...' , 'تحليل أعمدة متعددة');
    
    try {
        // Send requests for each Y column - handle failures gracefully
        const promises = yColumns.map(yCol =>
            fetch(`${API_BASE}/dynamic-analysis`, {
                method: 'POST',
                headers: {
                    'X-Session-Token': sessionToken,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    file_id: currentFileId,
                    sheet: currentSheetName,
                    x_column: xCol,
                    y_column: yCol,
                    group_by: null,
                    chart_type: chartType,
                    aggregation: aggregation
                })
            }).then(async r => {
                if (r.status === 401) {
                    clearToken();
                    sessionToken = null;
                    throw new Error('انتهت جلسة المستخدم - يرجى تسجيل الدخول مرة أخرى');
                }
                const data = await r.json();
                if (!r.ok) {
                    console.error(`❌ Failed for ${yCol}:`, data.error);
                    throw new Error(data.error || `Analysis failed for ${yCol}`);
                }
                console.log(`✅ Loaded ${yCol}:`, data.labels?.length || 0, 'labels');
                return { success: true, yColumn: yCol, data };
            }).catch(err => {
                console.error(`Error for ${yCol}:`, err.message);
                return { success: false, yColumn: yCol, error: err.message };
            })
        );
        
        const results = await Promise.all(promises);
        console.log('Multi-column results:', results);
        
        // Filter successful results
        const successfulResults = results.filter(r => r.success);
        
        if (successfulResults.length === 0) {
            throw new Error('فشل تحليل جميع الأعمدة: ' + results.map(r => r.error).join(', '));
        }
        
        if (successfulResults.length < yColumns.length) {
            const failedColumns = results.filter(r => !r.success).map(r => r.yColumn).join(', ');
            showError(`⚠️ فشل تحليل الأعمدة: ${failedColumns}. سيتم عرض الأعمدة الأخرى.`);
        }
        
        // Get labels from first successful result
        const labels = successfulResults[0].data.labels;
        
        if (!Array.isArray(labels) || labels.length === 0) {
            throw new Error('لا توجد تسميات في البيانات');
        }
        
        // Combine results into single chart with multiple datasets
        const combinedData = {
            chart_type: chartType,
            x_column: xCol,
            y_columns: successfulResults.map(r => r.yColumn),
            aggregation: aggregation,
            labels: labels,
            datasets: successfulResults.flatMap((result, idx) => {
                const data = result.data;
                return (data.datasets || []).map(ds => ({
                    ...ds,
                    label: result.yColumn,
                    backgroundColor: ['#00855D', '#43a047', '#ffc107', '#ff9800', '#e53935', '#9c27b0'][idx % 6],
                    borderColor: ['#00855D', '#43a047', '#ffc107', '#ff9800', '#e53935', '#9c27b0'][idx % 6]
                }))
            })
        };
        
        console.log('Combined multi-column data:', combinedData);
        hideLoadingScreen();
        renderDynamicChart(combinedData, chartType);
        
    } catch (error) {
        console.error('Multi-column analysis error:', error);
        showError('❌ خطأ في تحليل الأعمدة المتعددة: ' + error.message);
        hideLoadingScreen();
    }
}

async function runDynamicAnalysis(xCol, yCol, groupBy, chartType, aggregation) {
    showLoadingScreen('جاري التحليل...', 'الرجاء الانتظار');
    
    try {
        const response = await fetch(`${API_BASE}/dynamic-analysis`, {
            method: 'POST',
            headers: {
                'X-Session-Token': sessionToken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                file_id: currentFileId,
                sheet: currentSheetName,
                x_column: xCol,
                y_column: yCol,
                group_by: groupBy,
                chart_type: chartType,
                aggregation: aggregation
            })
        });
        
        if (response.status === 401) {
            clearToken();
            sessionToken = null;
            throw new Error('انتهت جلسة المستخدم - يرجى تسجيل الدخول مرة أخرى');
        }
        
        if (!response.ok) {
            throw new Error('Analysis failed: ' + response.status);
        }
        
        const data = await response.json();
        
        // Diagnostic logging
        console.log('API response:', data);
        
        // Validate data structure
        if (!data || typeof data !== 'object') {
            throw new Error('البيانات المستلمة غير صالحة');
        }
        
        if (!Array.isArray(data.labels)) {
            console.error('❌ Missing labels:', data.labels);
            throw new Error(`لا توجد تسميات في البيانات - Response: ${JSON.stringify(data)}`);
        }
        
        if (data.labels.length === 0) {
            throw new Error('البيانات فارغة - تحقق من اختيار الأعمدة وتأكد من وجود بيانات صحيحة');
        }
        
        if (!Array.isArray(data.datasets) || data.datasets.length === 0) {
            throw new Error('لا توجد مجموعات بيانات للرسم');
        }
        
        currentData = { xCol, yCol, groupBy, chartType, aggregation, ...data };
        
        hideLoadingScreen();
        renderDynamicChart(data, chartType);
        
    } catch (error) {
        console.error('Analysis error:', error);
        showError('❌ خطأ في التحليل: ' + error.message);
        hideLoadingScreen();
    }
}

// ============= Chart Rendering =============

function renderDynamicChart(data, chartType) {
    const container = document.getElementById('chartContainer');
    if (!container) return;
    
    // Final validation before rendering
    if (!data || !Array.isArray(data.labels) || !Array.isArray(data.datasets)) {
        showError('❌ لا توجد بيانات صالحة للعرض');
        return;
    }
    
    // Safely destroy old chart before creating new one
    if (window.dynamicChart && typeof window.dynamicChart.destroy === 'function') {
        try {
            window.dynamicChart.destroy();
        } catch (e) {
            console.warn('Error destroying old chart:', e);
        }
    }
    
    container.innerHTML = '<canvas id="dynamicChart" style="width: 100%; height: 400px;"></canvas>';
    
    const ctx = document.getElementById('dynamicChart').getContext('2d');
    
    // Safe datasets access
    const safeDatasets = data.datasets || [];
    const firstDataset = safeDatasets[0] || { data: [] };
    
    const chartConfig = {
        bar: {
            type: 'bar',
            data: { labels: data.labels, datasets: safeDatasets },
            options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true } } }
        },
        line: {
            type: 'line',
            data: { labels: data.labels, datasets: safeDatasets.map(ds => ({...ds, borderColor: ds.backgroundColor, backgroundColor: 'transparent', tension: 0.3, borderWidth: 3})) },
            options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true } } }
        },
        pie: {
            type: 'doughnut',
            data: { labels: data.labels, datasets: [{data: firstDataset.data || [], backgroundColor: ['#00855D', '#43a047', '#ffc107', '#ff9800', '#e53935', '#9c27b0'], borderColor: '#fff', borderWidth: 3}] },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } }
        },
        scatter: {
            type: 'scatter',
            data: { datasets: [{label: data.y_column || 'Y', data: (firstDataset.data || []).map((y, i) => ({ x: i, y: y })), backgroundColor: 'rgba(0, 133, 93, 0.8)', borderColor: '#00855D', borderWidth: 2, pointRadius: 8}] },
            options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true }, x: { display: false } } }
        }
    };
    
    window.dynamicChart = new Chart(ctx, chartConfig[chartType]);
}

// ============= Initialize =============

document.addEventListener('DOMContentLoaded', function() {
    console.log('✓ HR Analytics v3 (Secured) loaded');
    
    if (isLoggedIn()) {
        sessionToken = getToken();
        showDashboard();
        checkAuthStatus();
    } else {
        showLoginPage();
    }
});
