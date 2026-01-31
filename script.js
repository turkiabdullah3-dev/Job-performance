// Initialize Session
let sessionToken = null;
let currentFileId = null;
let currentSheetName = 'Sheet1';
let availableColumns = [];
let currentData = null;

// API Configuration
const API_BASE = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost' 
    ? 'http://127.0.0.1:8080' 
    : 'https://job-performance.onrender.com';

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

// ============= Session Management =============

async function initSession() {
    showLoadingScreen('جاري تهيئة الجلسة...', 'يرجى الانتظار');
    try {
        const response = await fetch(`${API_BASE}/init-session`, { 
            method: 'GET', 
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin'
        });
        
        if (!response.ok) {
            throw new Error('Session init failed');
        }
        
        const data = await response.json();
        sessionToken = data.session_token;
        hideLoadingScreen();
        console.log('✓ Session initialized');
    } catch (error) {
        console.error('Session init error:', error);
        hideLoadingScreen();
        showError('❌ فشل الاتصال بالخادم. تأكد من تشغيل الخادم.');
    }
}

// ============= File Upload =============

async function handleFileUpload(file) {
    if (!sessionToken) {
        showError('❌ الجلسة غير نشطة');
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
            showChartBuilderModal(data.columns);
        } else {
            throw new Error(data.error || 'Upload failed');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showError('❌ خطأ في الرفع: ' + error.message);
        hideLoadingScreen();
    }
}

// ============= Dynamic Chart Builder Modal =============

function showChartBuilderModal(columns) {
    // Remove old modal
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
    
    content.innerHTML = `
        <div style="text-align: center; margin-bottom: 30px;">
            <h2 style="color: #00855D; margin: 0; font-size: 28px;">
                <i class="fas fa-chart-bar"></i> بناء رسم بياني
            </h2>
            <p style="color: #666; margin: 10px 0 0 0;">اختر الأعمدة والخيارات لإنشاء رسم بياني مخصص</p>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 25px;">
            <!-- X Axis Column -->
            <div>
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
                    ${columns.map(col => `<option value="${col}">${col}</option>`).join('')}
                </select>
            </div>
            
            <!-- Y Axis Column -->
            <div>
                <label style="display: block; font-weight: 600; margin-bottom: 10px; color: #1B4D3E;">
                    <i class="fas fa-arrows-alt-v"></i> المحور العمودي (Y):
                </label>
                <select id="y-column-select" style="
                    width: 100%;
                    padding: 12px;
                    border: 2px solid #D4E5DD;
                    border-radius: 10px;
                    font-family: 'Cairo', sans-serif;
                    font-size: 14px;
                    background: white;
                ">
                    <option value="">-- اختر العمود --</option>
                    ${columns.map(col => `<option value="${col}">${col}</option>`).join('')}
                </select>
            </div>
        </div>
        
        <!-- Group By Column (Optional) -->
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
                ${columns.map(col => `<option value="${col}">${col}</option>`).join('')}
            </select>
        </div>
        
        <!-- Chart Type -->
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
        
        <!-- Aggregation Function -->
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
        
        <!-- Buttons -->
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
                transition: all 0.3s;
            " onmouseover="this.style.background='#D4E5DD'" onmouseout="this.style.background='#E8F5E9'">
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
                transition: all 0.3s;
            " onmouseover="this.style.background='#006642'" onmouseout="this.style.background='#00855D'">
                <i class="fas fa-chart-line"></i> إنشاء الرسم البياني
            </button>
        </div>
    `;
    
    modal.appendChild(content);
    document.body.appendChild(modal);
    
    // Event Listeners
    document.getElementById('cancel-chart-builder-btn').onclick = () => {
        modal.remove();
        currentFileId = null;
        document.getElementById('excel-file').value = '';
    };
    
    document.getElementById('create-chart-btn').onclick = async () => {
        const xCol = document.getElementById('x-column-select').value;
        const yCol = document.getElementById('y-column-select').value;
        const groupBy = document.getElementById('group-by-select').value || null;
        const chartType = document.querySelector('input[name="chart-type"]:checked').value;
        const aggregation = document.getElementById('aggregation-select').value;
        
        if (!xCol || !yCol) {
            showError('❌ يرجى اختيار العمودين الأفقي والعمودي');
            return;
        }
        
        modal.remove();
        await runDynamicAnalysis(xCol, yCol, groupBy, chartType, aggregation);
    };
}

// ============= Dynamic Analysis =============

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
        
        if (!response.ok) {
            throw new Error('Analysis failed: ' + response.status);
        }
        
        const data = await response.json();
        currentData = { xCol, yCol, groupBy, chartType, aggregation, ...data };
        
        hideLoadingScreen();
        renderDynamicChart(data, chartType);
        showChartControls(xCol, yCol, groupBy, chartType, aggregation);
        
    } catch (error) {
        console.error('Analysis error:', error);
        showError('❌ خطأ في التحليل: ' + error.message);
        hideLoadingScreen();
    }
}

// ============= Chart Rendering =============

function renderDynamicChart(data, chartType) {
    const container = document.getElementById('chartContainer');
    if (!container) {
        console.error('Chart container not found');
        return;
    }
    
    // Remove old canvas
    container.innerHTML = '<canvas id="dynamicChart" style="width: 100%; height: 400px;"></canvas>';
    
    const ctx = document.getElementById('dynamicChart').getContext('2d');
    
    // Destroy previous chart
    if (window.dynamicChart) window.dynamicChart.destroy();
    
    const chartConfig = {
        bar: {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: data.datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: data.datasets.length > 1 ? 'y' : undefined,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(0,0,0,0.05)' }
                    },
                    x: {
                        grid: { display: false }
                    }
                },
                plugins: { legend: { display: data.datasets.length > 1 } }
            }
        },
        
        line: {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: data.datasets.map(ds => ({
                    ...ds,
                    borderColor: ds.backgroundColor,
                    backgroundColor: 'transparent',
                    tension: 0.3,
                    borderWidth: 3
                }))
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
                        grid: { display: false }
                    }
                },
                plugins: { legend: { display: data.datasets.length > 1 } }
            }
        },
        
        pie: {
            type: 'doughnut',
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.datasets[0].data,
                    backgroundColor: ['#00855D', '#43a047', '#ffc107', '#ff9800', '#e53935', '#9c27b0', '#3f51b5', '#00bcd4'],
                    borderColor: '#fff',
                    borderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        },
        
        scatter: {
            type: 'scatter',
            data: {
                datasets: [{
                    label: data.y_column,
                    data: data.datasets[0].data.map((y, i) => ({ x: i, y: y })),
                    backgroundColor: 'rgba(0, 133, 93, 0.8)',
                    borderColor: '#00855D',
                    borderWidth: 2,
                    pointRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true },
                    x: { display: false }
                },
                plugins: { legend: { display: false } }
            }
        }
    };
    
    window.dynamicChart = new Chart(ctx, chartConfig[chartType]);
}

function showChartControls(xCol, yCol, groupBy, chartType, aggregation) {
    const controlsDiv = document.getElementById('chartControls');
    if (!controlsDiv) return;
    
    controlsDiv.style.display = 'block';
    controlsDiv.innerHTML = `
        <div style="display: flex; gap: 15px; flex-wrap: wrap; justify-content: center; padding: 20px; background: #f5f5f5; border-radius: 10px;">
            <button onclick="exportChartAsImage()" style="
                padding: 10px 20px;
                background: #00855D;
                color: white;
                border: none;
                border-radius: 8px;
                font-family: 'Cairo', sans-serif;
                cursor: pointer;
            ">
                <i class="fas fa-download"></i> تحميل الرسم
            </button>
            <button onclick="exportChartData()" style="
                padding: 10px 20px;
                background: #43a047;
                color: white;
                border: none;
                border-radius: 8px;
                font-family: 'Cairo', sans-serif;
                cursor: pointer;
            ">
                <i class="fas fa-file-excel"></i> تحميل البيانات
            </button>
            <button id="new-chart-btn" style="
                padding: 10px 20px;
                background: #ffc107;
                color: #333;
                border: none;
                border-radius: 8px;
                font-family: 'Cairo', sans-serif;
                cursor: pointer;
            ">
                <i class="fas fa-plus"></i> رسم جديد
            </button>
        </div>
    `;
    
    document.getElementById('new-chart-btn').onclick = () => {
        document.getElementById('excel-file').value = '';
        document.getElementById('chartContainer').innerHTML = '';
        document.getElementById('chartControls').style.display = 'none';
    };
}

// ============= Export Functions =============

function exportChartAsImage() {
    if (!window.dynamicChart) return;
    const link = document.createElement('a');
    link.href = window.dynamicChart.canvas.toDataURL('image/png');
    link.download = 'chart.png';
    link.click();
}

function exportChartData() {
    if (!currentData) return;
    
    const csv = [
        ['العمود الأفقي', 'القيمة', ...(currentData.groupBy ? ['التجميع'] : [])].join(','),
        ...currentData.labels.map((label, i) => {
            const value = currentData.datasets[0].data[i] || 0;
            const groupValue = currentData.groupBy ? (currentData.datasets[0].label || '') : '';
            return [label, value, groupValue].join(',');
        })
    ].join('\n');
    
    const link = document.createElement('a');
    link.href = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv);
    link.download = 'chart-data.csv';
    link.click();
}

// ============= Initialize =============

document.addEventListener('DOMContentLoaded', function() {
    console.log('✓ HR Analytics v2 loaded');
    initSession();
    
    const fileInput = document.getElementById('excel-file');
    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) handleFileUpload(file);
        });
    }
});
