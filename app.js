/* =================== 全域變數 =================== */
let currentChart = null;

// 前端到後端的類型映射
const API_TYPE_MAPPING = {
    'real_estate': 'real_estate',
    'etf': 'etf_regular',
    'stock': 'stock',
    'fund': 'mutual_fund',
    'bond': 'bond_deposit'
};

/* =================== 工具函式 =================== */

/**
 * 安全格式化數值為固定小數位數
 * @param {number} value - 要格式化的數值
 * @param {number} decimals - 小數位數，預設為2
 * @returns {string} 格式化後的字串
 */
const safeToFixed = (value, decimals = 2) => {
    if (value === null || value === undefined || isNaN(value)) return '0.00';
    return Number(value).toFixed(decimals);
};

/**
 * 安全格式化貨幣
 * @param {number} value - 要格式化的數值
 * @returns {string} 格式化後的貨幣字串
 */
const safeCurrency = (value) => {
    if (value === null || value === undefined || isNaN(value)) return 'NT$ 0';
    return formatCurrency(value);
};

/**
 * 格式化貨幣顯示
 * @param {number} amount - 金額
 * @returns {string} 格式化後的貨幣字串
 */
function formatCurrency(amount) {
    if (typeof amount !== 'number') return amount;
    return amount.toLocaleString('zh-TW', { 
        style: 'currency', 
        currency: 'TWD', 
        minimumFractionDigits: 0 
    });
}

/**
 * 從資料物件中安全取得欄位值
 * @param {Object} data - 資料物件
 * @param {Array} possibleFields - 可能的欄位名稱陣列
 * @param {*} defaultValue - 預設值
 * @returns {*} 取得的值或預設值
 */
function getFieldValue(data, possibleFields, defaultValue = 0) {
    for (const field of possibleFields) {
        if (data[field] !== undefined && data[field] !== null) {
            return data[field];
        }
    }
    return defaultValue;
}

/**
 * 取得投資類型的中文標籤
 * @param {string} type - 投資類型代碼
 * @returns {string} 中文標籤
 */
function getTypeLabel(type) {
    const labels = {
        'real_estate': '🏠 房地產投資',
        'etf': '📈 ETF 定期定額',
        'etf_regular': '📈 ETF 定期定額',
        'stock': '📊 股票投資',
        'fund': '💰 基金投資',
        'mutual_fund': '💰 基金投資',
        'bond': '💎 美債/定存',
        'bond_deposit': '💎 美債/定存'
    };
    return labels[type] || type;
}

/* =================== UI 控制函式 =================== */

/**
 * 顯示載入中狀態
 */
function showLoading() {
    document.getElementById('loading').classList.remove('hidden');
}

/**
 * 隱藏載入中狀態
 */
function hideLoading() {
    document.getElementById('loading').classList.add('hidden');
}

/**
 * 顯示錯誤訊息
 * @param {string} message - 錯誤訊息
 */
function showError(message) {
    const errorDiv = document.getElementById('error');
    errorDiv.textContent = message;
    errorDiv.classList.remove('hidden');
}

/**
 * 隱藏錯誤訊息
 */
function hideError() {
    document.getElementById('error').classList.add('hidden');
}

/**
 * 顯示成功訊息
 * @param {string} message - 成功訊息
 */
function showSuccess(message) {
    const successDiv = document.getElementById('success');
    successDiv.textContent = message;
    successDiv.classList.remove('hidden');
    setTimeout(() => hideSuccess(), 3000);
}

/**
 * 隱藏成功訊息
 */
function hideSuccess() {
    document.getElementById('success').classList.add('hidden');
}

/**
 * 隱藏結果區域
 */
function hideResults() {
    document.getElementById('results').classList.add('hidden');
}

/* =================== 表單處理 =================== */

/**
 * 初始化投資類型按鈕事件
 */
function initInvestmentTypeButtons() {
    document.querySelectorAll('.investment-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            // 移除所有按鈕的 active 狀態
            document.querySelectorAll('.investment-btn').forEach(b => b.classList.remove('active'));
            // 設定當前按鈕為 active
            this.classList.add('active');

            // 隱藏所有表單
            document.querySelectorAll('.investment-form').forEach(form => form.classList.add('hidden'));

            // 顯示對應的表單
            const type = this.dataset.type;
            const form = document.getElementById(type + '_form');
            if (form) form.classList.remove('hidden');

            // 隱藏結果
            hideResults();
        });
    });
}

/**
 * 初始化表單提交事件
 */
function initFormSubmission() {
    document.querySelectorAll('.investment-form').forEach(form => {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();

            const formData = new FormData(this);
            const data = Object.fromEntries(formData.entries());
            const type = this.id.replace('_form', '');

            // 轉換數值類型
            for (const key in data) {
                if (!isNaN(data[key]) && data[key] !== '') {
                    data[key] = parseFloat(data[key]);
                }
            }

            await submitInvestmentForm(type, data);
        });
    });
}

/**
 * 提交投資表單
 * @param {string} frontendType - 前端投資類型
 * @param {Object} data - 表單資料
 */
async function submitInvestmentForm(frontendType, data) {
    const apiUrl = document.getElementById('api_url').value.trim();
    if (!apiUrl) {
        showError('請輸入 API URL');
        return;
    }

    const backendType = API_TYPE_MAPPING[frontendType];
    if (!backendType) {
        showError('未知的投資類型');
        return;
    }

    showLoading();
    hideResults();
    hideError();
    hideSuccess();

    try {
        const response = await fetch(`${apiUrl}/simulate/${backendType}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            let errorText = `API 請求失敗: ${response.status}`;
            try {
                const errorData = await response.json();
                if (errorData && errorData.error) errorText = errorData.error;
            } catch(_) {}
            throw new Error(errorText);
        }

        const apiResponse = await response.json();
        if (apiResponse.success && apiResponse.result) {
            displayResults(apiResponse.result);
            showSuccess('模擬計算完成！');
        } else {
            throw new Error('API 回應格式錯誤');
        }

        await loadHistory();
    } catch (error) {
        console.error('API Error:', error);
        showError(`模擬失敗: ${error.message}`);
    } finally {
        hideLoading();
    }
}

/* =================== 結果顯示 =================== */

/**
 * 顯示投資模擬結果
 * @param {Object} data - 結果資料
 */
function displayResults(data) {
    if (!data || typeof data !== 'object') {
        showError('結果資料格式錯誤');
        return;
    }

    const resultsDiv = document.getElementById('results');
    const resultItems = document.getElementById('result_items');
    resultItems.innerHTML = '';

    if (data.type === 'real_estate') {
        displayRealEstateResults(data, resultItems);
    } else {
        displayGeneralResults(data, resultItems);
    }

    if (Array.isArray(data.yearly_data) && data.yearly_data.length > 0) {
        displayChart(data);
    }

    resultsDiv.classList.remove('hidden');
}

/**
 * 顯示房地產投資結果
 * @param {Object} data - 結果資料
 * @param {HTMLElement} container - 容器元素
 */
function displayRealEstateResults(data, container) {
    const items = [
        { label: '投資類型', value: getTypeLabel(data.type) },
        { label: '房屋總價', value: safeCurrency(data.house_price) },
        { label: '頭期款', value: safeCurrency(data.down_payment) },
        { label: '貸款金額', value: safeCurrency(data.loan_amount) },
        { label: '每月還款', value: safeCurrency(data.monthly_payment) },
        { label: '總還款金額', value: safeCurrency(data.total_payments) },
        { label: '總利息支出', value: safeCurrency(data.total_interest) },
        { label: '總持有成本', value: safeCurrency(data.total_cost) },
        { label: `${data.simulation_years || data.years}年後房價`, value: safeCurrency(data.final_value) },
        { label: '投資報酬率', value: `${safeToFixed(data.roi)}%` },
        { label: '年化報酬率', value: `${safeToFixed(data.annualized_return)}%` }
    ];

    items.forEach(item => container.appendChild(createResultItem(item.label, item.value)));
}

/**
 * 顯示一般投資結果
 * @param {Object} data - 結果資料
 * @param {HTMLElement} container - 容器元素
 */
function displayGeneralResults(data, container) {
    const items = [
        { label: '投資類型', value: getTypeLabel(data.type) }
    ];

    const initialAmount = getFieldValue(data, ['initial_amount', 'principal']);
    if (initialAmount > 0) items.push({ label: '初始投資', value: safeCurrency(initialAmount) });

    const monthlyAmount = getFieldValue(data, ['monthly_amount']);
    if (monthlyAmount > 0) items.push({ label: '每月投入', value: safeCurrency(monthlyAmount) });

    const totalInvested = getFieldValue(data, ['total_investment', 'total_invested', 'principal']);
    items.push({ label: '總投入金額', value: safeCurrency(totalInvested) });

    const finalValue = getFieldValue(data, ['final_value', 'current_value']);
    const years = getFieldValue(data, ['years', 'simulation_years']) || 10;
    items.push({ label: `${years}年後總值`, value: safeCurrency(finalValue) });

    const totalProfit = getFieldValue(data, ['profit', 'total_profit']);
    items.push({ label: '總獲利', value: safeCurrency(totalProfit) });

    const roi = getFieldValue(data, ['roi', 'investment_ratio']);
    items.push({ label: '投資報酬率', value: `${safeToFixed(roi)}%` });

    const annualizedReturn = getFieldValue(data, ['annualized_return', 'irr', 'mean_return']);
    if (annualizedReturn !== 0) {
        items.push({ label: '年化報酬率', value: `${safeToFixed(annualizedReturn)}%` });
    }

    items.forEach(item => container.appendChild(createResultItem(item.label, item.value)));
}

/**
 * 建立結果項目元素
 * @param {string} label - 標籤
 * @param {string} value - 值
 * @returns {HTMLElement} 建立的元素
 */
function createResultItem(label, value) {
    const div = document.createElement('div');
    div.className = 'result-item';
    div.innerHTML = `
        <span class="label">${label}:</span>
        <span class="value">${value}</span>
    `;
    return div;
}

/* =================== 圖表顯示 =================== */

/**
 * 顯示投資成長圖表
 * @param {Object} data - 包含圖表資料的物件
 */
function displayChart(data) {
    const ctx = document.getElementById('investmentChart').getContext('2d');

    if (currentChart) currentChart.destroy();

    const labels = data.yearly_data.map((_, index) => `第${index + 1}年`);
    const values = data.yearly_data.map(item => item.total_value);
    const investments = data.yearly_data.map(item => item.total_invested);

    currentChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [
                {
                    label: '總資產價值',
                    data: values,
                    borderColor: '#8B7355',
                    backgroundColor: 'rgba(139, 115, 85, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4
                },
                {
                    label: '累計投入',
                    data: investments,
                    borderColor: '#CD853F',
                    backgroundColor: 'rgba(205, 133, 63, 0.1)',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: '投資成長趨勢圖',
                    font: { size: 16, weight: 'bold' },
                    color: '#654321'
                },
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return formatCurrency(value);
                        }
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    });
}

/* =================== 歷史記錄 =================== */

/**
 * 載入歷史記錄
 */
async function loadHistory() {
    const apiUrl = document.getElementById('api_url').value.trim();
    if (!apiUrl) return;

    try {
        const response = await fetch(`${apiUrl}/history`);
        if (!response.ok) throw new Error('無法載入歷史記錄');

        const history = await response.json();
        displayHistory(history);
    } catch (error) {
        console.error('載入歷史記錄失敗:', error);
        document.getElementById('history_list').innerHTML = 
            '<p style="text-align: center; color: #999;">載入歷史記錄失敗</p>';
    }
}

/**
 * 顯示歷史記錄
 * @param {Object|Array} history - 歷史記錄資料
 */
function displayHistory(history) {
    const historyList = document.getElementById('history_list');

    let historyData;
    if (Array.isArray(history)) {
        historyData = history;
    } else if (history && history.success && Array.isArray(history.data)) {
        historyData = history.data;
    } else {
        historyList.innerHTML = '<p style="text-align: center; color: #666;">尚無模擬記錄</p>';
        return;
    }

    if (historyData.length === 0) {
        historyList.innerHTML = '<p style="text-align: center; color: #666;">尚無模擬記錄</p>';
        return;
    }

    historyList.innerHTML = historyData.slice(0, 5).map(record => {
        const result = record.result || record;

        const totalProfit = getFieldValue(result, ['profit', 'total_profit']);
        const roi = getFieldValue(result, ['roi', 'investment_ratio']);

        const typeLabel = getTypeLabel(record.investment_type || result.type || 'unknown');
        const timeStr = record.created_at ? new Date(record.created_at).toLocaleString('zh-TW') : '';

        return `
            <div class="history-item">
                <div class="history-item-header">
                    ${typeLabel} ${timeStr ? '- ' + timeStr : ''}
                </div>
                <div class="history-item-details">
                    總獲利: ${safeCurrency(totalProfit)} | ROI: ${safeToFixed(roi)}%
                </div>
            </div>
        `;
    }).join('');
}

/* =================== 應用程式初始化 =================== */

/**
 * 初始化應用程式
 */
function initApp() {
    // 初始化投資類型按鈕
    initInvestmentTypeButtons();
    
    // 初始化表單提交
    initFormSubmission();
    
    // 載入歷史記錄
    loadHistory();
}

/* =================== 事件監聽器 =================== */

// DOM 載入完成後初始化應用程式
window.addEventListener('DOMContentLoaded', initApp);