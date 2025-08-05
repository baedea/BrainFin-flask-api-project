/**
 * Goal Simulator JavaScript
 * 財務目標模擬器前端邏輯
 */

class GoalSimulator {
    constructor(app) {
        this.app = app;
        this.currentType = 'real_estate';
        this.charts = {};
        this.currentResult = null;
        
        this.init();
    }

    /**
     * 初始化模擬器
     */
    init() {
        this.initTabs();
        this.initForms();
        this.initResultsSection();
        console.log('Goal Simulator initialized');
    }

    /**
     * 初始化標籤頁
     */
    initTabs() {
        const tabButtons = document.querySelectorAll('.tab-btn');
        const forms = document.querySelectorAll('.investment-form');

        tabButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const type = btn.getAttribute('data-type');
                this.switchTab(type);
            });
        });
    }

    /**
     * 切換標籤頁
     */
    switchTab(type) {
        // 更新按鈕狀態
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.getAttribute('data-type') === type) {
                btn.classList.add('active');
            }
        });

        // 更新表單顯示
        document.querySelectorAll('.investment-form').forEach(form => {
            form.classList.remove('active');
            if (form.id === `${this.getFormId(type)}`) {
                form.classList.add('active');
            }
        });

        this.currentType = type;
        this.hideResults();
    }

    /**
     * 取得表單 ID
     */
    getFormId(type) {
        const formIdMap = {
            'real_estate': 'realEstateForm',
            'etf_regular': 'etfRegularForm',
            'stock': 'stockForm',
            'bond_deposit': 'bondDepositForm'
        };
        return formIdMap[type];
    }

    /**
     * 初始化表單
     */
    initForms() {
        const forms = document.querySelectorAll('.calculator-form');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleFormSubmit(form);
            });
        });

        // 重置按鈕
        this.initResetButtons();
        
        // 表單驗證
        this.initFormValidation();
    }

    /**
     * 初始化重置按鈕
     */
    initResetButtons() {
        const resetButtons = document.querySelectorAll('.btn[id^="reset"]');
        resetButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const form = btn.closest('.investment-form').querySelector('form');
                this.resetForm(form);
            });
        });
    }

    /**
     * 初始化表單驗證
     */
    initFormValidation() {
        const inputs = document.querySelectorAll('.calculator-form input');
        inputs.forEach(input => {
            input.addEventListener('blur', () => {
                this.validateInput(input);
            });

            input.addEventListener('input', () => {
                this.clearInputError(input);
            });
        });
    }

    /**
     * 驗證輸入欄位
     */
    validateInput(input) {
        const value = parseFloat(input.value);
        const min = parseFloat(input.getAttribute('min'));
        const max = parseFloat(input.getAttribute('max'));
        let isValid = true;
        let errorMessage = '';

        if (input.hasAttribute('required') && !input.value) {
            isValid = false;
            errorMessage = '此欄位為必填';
        } else if (isNaN(value)) {
            isValid = false;
            errorMessage = '請輸入有效數字';
        } else if (min !== null && !isNaN(min) && value < min) {
            isValid = false;
            errorMessage = `數值不能小於 ${min}`;
        } else if (max !== null && !isNaN(max) && value > max) {
            isValid = false;
            errorMessage = `數值不能大於 ${max}`;
        }

        if (!isValid) {
            this.showInputError(input, errorMessage);
        } else {
            this.clearInputError(input);
        }

        return isValid;
    }

    /**
     * 顯示輸入錯誤
     */
    showInputError(input, message) {
        input.classList.add('error');
        
        let errorElement = input.parentNode.querySelector('.error-message');
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.className = 'error-message';
            input.parentNode.appendChild(errorElement);
        }
        
        errorElement.textContent = message;
    }

    /**
     * 清除輸入錯誤
     */
    clearInputError(input) {
        input.classList.remove('error');
        const errorElement = input.parentNode.querySelector('.error-message');
        if (errorElement) {
            errorElement.remove();
        }
    }

    /**
     * 處理表單提交
     */
    async handleFormSubmit(form) {
        if (!this.validateForm(form)) {
            this.app.showToast('請檢查表單輸入', 'error');
            return;
        }

        const formData = this.getFormData(form);
        const investmentType = form.getAttribute('data-type');

        try {
            const result = await this.app.calculateInvestment(investmentType, formData);
            this.displayResults(result);
        } catch (error) {
            console.error('Calculation failed:', error);
        }
    }

    /**
     * 驗證整個表單
     */
    validateForm(form) {
        const inputs = form.querySelectorAll('input[required], select[required]');
        let isValid = true;

        inputs.forEach(input => {
            if (!this.validateInput(input)) {
                isValid = false;
            }
        });

        return isValid;
    }

    /**
     * 取得表單資料
     */
    getFormData(form) {
        const formData = new FormData(form);
        const data = {};

        for (let [key, value] of formData.entries()) {
            // 處理不同類型的輸入
            if (key === 'is_compound') {
                data[key] = value === 'true';
            } else if (key === 'scenario') {
                data[key] = value;
            } else if (!isNaN(value) && value !== '') {
                data[key] = parseFloat(value);
            } else {
                data[key] = value;
            }
        }

        // 萬元轉換為元 (某些欄位)
        this.convertCurrencyFields(data, form.getAttribute('data-type'));

        return data;
    }

    /**
     * 轉換貨幣欄位 (萬元 -> 元)
     */
    convertCurrencyFields(data, investmentType) {
        const currencyFields = {
            'real_estate': ['house_price', 'down_payment', 'annual_cost'],
            'etf_regular': ['initial_amount', 'monthly_amount'],
            'stock': ['initial_amount', 'monthly_amount'],
            'bond_deposit': ['principal']
        };

        const fieldsToConvert = currencyFields[investmentType] || [];
        fieldsToConvert.forEach(field => {
            if (data[field] !== undefined) {
                data[field] = data[field] * 10000; // 萬元轉元
            }
        });
    }

    /**
     * 重置表單
     */
    resetForm(form) {
        form.reset();
        
        // 清除錯誤訊息
        const errorMessages = form.querySelectorAll('.error-message');
        errorMessages.forEach(msg => msg.remove());
        
        // 清除錯誤樣式
        const errorInputs = form.querySelectorAll('.error');
        errorInputs.forEach(input => input.classList.remove('error'));
        
        this.hideResults();
    }

    /**
     * 顯示計算結果
     */
    displayResults(result) {
        this.currentResult = result;
        const resultsSection = document.getElementById('resultsSection');
        const resultsContent = document.getElementById('resultsContent');

        if (!resultsSection || !resultsContent) return;

        // 根據投資類型生成結果內容
        const resultHTML = this.generateResultHTML(result);
        resultsContent.innerHTML = resultHTML;

        // 顯示結果區域
        resultsSection.style.display = 'block';
        resultsSection.scrollIntoView({ behavior: 'smooth' });

        // 初始化圖表
        this.renderCharts(result);

        // 初始化結果區域按鈕
        this.initResultButtons();
    }

    /**
     * 生成結果 HTML
     */
    generateResultHTML(result) {
        switch (result.investment_type) {
            case 'real_estate':
                return this.generateRealEstateResult(result.result);
            case 'etf_regular':
                return this.generateETFResult(result.result);
            case 'stock':
                return this.generateStockResult(result.result);
            case 'bond_deposit':
                return this.generateBondResult(result.result);
            default:
                return '<p>未知的投資類型</p>';
        }
    }

    /**
     * 生成房地產結果
     */
    generateRealEstateResult(result) {
        return `
            <div class="results-grid">
                <div class="result-card">
                    <div class="result-value ${result.profit >= 0 ? 'positive' : 'negative'}">
                        ${this.app.formatCurrency(result.profit)}
                    </div>
                    <div class="result-label">獲利</div>
                </div>
                <div class="result-card">
                    <div class="result-value ${result.roi >= 0 ? 'positive' : 'negative'}">
                        ${result.roi}%
                    </div>
                    <div class="result-label">投資報酬率</div>
                </div>
                <div class="result-card">
                    <div class="result-value">
                        ${this.app.formatCurrency(result.actual_cash_outflow)}
                    </div>
                    <div class="result-label">實際現金支出</div>
                </div>
                <div class="result-card">
                    <div class="result-value">
                        ${this.app.formatCurrency(result.actual_sale_income)}
                    </div>
                    <div class="result-label">賣房收入</div>
                </div>
            </div>
            
            <div class="result-description">
                <h3>詳細分析</h3>
                <ul>
                    <li><span>分析情境</span><span>${result.scenario}</span></li>
                    <li><span>房屋現值</span><span>${this.app.formatCurrency(result.current_value)}</span></li>
                    <li><span>每月還款</span><span>${this.app.formatCurrency(result.monthly_payment)}</span></li>
                    <li><span>利息支出</span><span>${this.app.formatCurrency(result.interest_paid)}</span></li>
                    <li><span>持有成本</span><span>${this.app.formatCurrency(result.holding_cost)}</span></li>
                    <li><span>剩餘本金</span><span>${this.app.formatCurrency(result.remaining_principal)}</span></li>
                </ul>
            </div>
        `;
    }

    /**
     * 生成 ETF 結果
     */
    generateETFResult(result) {
        return `
            <div class="results-grid">
                <div class="result-card">
                    <div class="result-value positive">
                        ${this.app.formatCurrency(result.final_value)}
                    </div>
                    <div class="result-label">最終價值</div>
                </div>
                <div class="result-card">
                    <div class="result-value">
                        ${this.app.formatCurrency(result.total_investment)}
                    </div>
                    <div class="result-label">總投資金額</div>
                </div>
                <div class="result-card">
                    <div class="result-value ${result.profit >= 0 ? 'positive' : 'negative'}">
                        ${this.app.formatCurrency(result.profit)}
                    </div>
                    <div class="result-label">獲利</div>
                </div>
                <div class="result-card">
                    <div class="result-value positive">
                        ${result.annualized_return}%
                    </div>
                    <div class="result-label">年化報酬率</div>
                </div>
            </div>
            
            <div class="result-description">
                <h3>投資詳情</h3>
                <ul>
                    <li><span>投資報酬率 (ROI)</span><span>${result.roi}%</span></li>
                    <li><span>內部報酬率 (IRR)</span><span>${result.irr}%</span></li>
                    <li><span>累積配息收入</span><span>${this.app.formatCurrency(result.dividend_income)}</span></li>
                    <li><span>資本利得</span><span>${this.app.formatCurrency(result.capital_gain)}</span></li>
                </ul>
            </div>
        `;
    }

    /**
     * 生成股票結果
     */
    generateStockResult(result) {
        return `
            <div class="results-grid">
                <div class="result-card">
                    <div class="result-value positive">
                        ${this.app.formatCurrency(result.mean)}
                    </div>
                    <div class="result-label">平均最終價值</div>
                </div>
                <div class="result-card">
                    <div class="result-value">
                        ${this.app.formatCurrency(result.percentile_5)}
                    </div>
                    <div class="result-label">5% 最差情況</div>
                </div>
                <div class="result-card">
                    <div class="result-value positive">
                        ${this.app.formatCurrency(result.percentile_95)}
                    </div>
                    <div class="result-label">5% 最佳情況</div>
                </div>
                <div class="result-card">
                    <div class="result-value">
                        ${result.mean_return}%
                    </div>
                    <div class="result-label">平均年化報酬率</div>
                </div>
            </div>
            
            <div class="result-description">
                <h3>蒙地卡羅模擬結果</h3>
                <ul>
                    <li><span>總投資金額</span><span>${this.app.formatCurrency(result.total_investment)}</span></li>
                    <li><span>最差情況年化報酬</span><span>${result.worst_case}%</span></li>
                    <li><span>最佳情況年化報酬</span><span>${result.best_case}%</span></li>
                </ul>
                <p style="margin-top: 1rem; font-size: 0.875rem; color: var(--text-secondary);">
                    ※ 以上結果基於 10,000 次蒙地卡羅模擬，實際投資結果可能有所不同
                </p>
            </div>
        `;
    }

    /**
     * 生成債券結果
     */
    generateBondResult(result) {
        return `
            <div class="results-grid">
                <div class="result-card">
                    <div class="result-value positive">
                        ${this.app.formatCurrency(result.final_value)}
                    </div>
                    <div class="result-label">最終價值 (名目)</div>
                </div>
                <div class="result-card">
                    <div class="result-value">
                        ${this.app.formatCurrency(result.real_value)}
                    </div>
                    <div class="result-label">實質價值</div>
                </div>
                <div class="result-card">
                    <div class="result-value">
                        ${result.nominal_return}%
                    </div>
                    <div class="result-label">名目年化報酬</div>
                </div>
                <div class="result-card">
                    <div class="result-value">
                        ${result.real_return}%
                    </div>
                    <div class="result-label">實質年化報酬</div>
                </div>
            </div>
            
            <div class="result-description">
                <h3>債券投資分析</h3>
                <ul>
                    <li><span>通膨影響金額</span><span>${this.app.formatCurrency(result.inflation_impact)}</span></li>
                </ul>
                <p style="margin-top: 1rem; font-size: 0.875rem; color: var(--text-secondary);">
                    ※ 實質報酬率已扣除通膨影響，更能反映真實購買力變化
                </p>
            </div>
        `;
    }

    /**
     * 渲染圖表
     */
    renderCharts(result) {
        const chartCanvas = document.getElementById('resultsChart');
        if (!chartCanvas) return;

        // 銷毀現有圖表
        if (this.charts.results) {
            this.charts.results.destroy();
        }

        const ctx = chartCanvas.getContext('2d');
        
        switch (result.investment_type) {
            case 'real_estate':
                this.renderRealEstateChart(ctx, result.result);
                break;
            case 'etf_regular':
                this.renderETFChart(ctx, result.result);
                break;
            case 'stock':
                this.renderStockChart(ctx, result.result);
                break;
            case 'bond_deposit':
                this.renderBondChart(ctx, result.result);
                break;
        }
    }

    /**
     * 渲染房地產圖表
     */
    renderRealEstateChart(ctx, result) {
        this.charts.results = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['現金支出', '獲利'],
                datasets: [{
                    data: [
                        Math.abs(result.actual_cash_outflow),
                        Math.max(0, result.profit)
                    ],
                    backgroundColor: [
                        '#ef4444',
                        '#10b981'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: '投資成本與獲利分析'
                    },
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    /**
     * 渲染 ETF 圖表
     */
    renderETFChart(ctx, result) {
        this.charts.results = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['投入本金', '配息收入', '資本利得'],
                datasets: [{
                    data: [
                        result.total_investment,
                        result.dividend_income,
                        result.capital_gain
                    ],
                    backgroundColor: [
                        '#3b82f6',
                        '#10b981',
                        '#f59e0b'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'ETF 投資組成分析'
                    },
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    /**
     * 渲染股票圖表
     */
    renderStockChart(ctx, result) {
        this.charts.results = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['5% 最差', '平均', '5% 最佳'],
                datasets: [{
                    label: '最終價值',
                    data: [
                        result.percentile_5,
                        result.mean,
                        result.percentile_95
                    ],
                    backgroundColor: [
                        '#ef4444',
                        '#3b82f6',
                        '#10b981'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: '蒙地卡羅模擬結果分布'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return (value / 10000).toFixed(0) + '萬';
                            }
                        }
                    }
                }
            }
        });
    }

    /**
     * 渲染債券圖表
     */
    renderBondChart(ctx, result) {
        this.charts.results = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['實質價值', '通膨影響'],
                datasets: [{
                    data: [
                        result.real_value,
                        result.inflation_impact
                    ],
                    backgroundColor: [
                        '#10b981',
                        '#ef4444'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: '通膨對投資價值的影響'
                    },
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    /**
     * 初始化結果區域按鈕
     */
    initResultButtons() {
        const saveBtn = document.getElementById('saveResult');
        const exportBtn = document.getElementById('exportPDF');
        const shareBtn = document.getElementById('shareResult');

        if (saveBtn) {
            saveBtn.addEventListener('click', () => {
                if (this.currentResult) {
                    this.app.saveCalculationResult(this.currentResult);
                }
            });
        }

        if (exportBtn) {
            exportBtn.addEventListener('click', () => {
                if (this.currentResult) {
                    this.app.exportToPDF(this.currentResult);
                }
            });
        }

        if (shareBtn) {
            shareBtn.addEventListener('click', () => {
                if (this.currentResult) {
                    this.app.shareResult(this.currentResult);
                }
            });
        }
    }

    /**
     * 隱藏結果區域
     */
    hideResults() {
        const resultsSection = document.getElementById('resultsSection');
        if (resultsSection) {
            resultsSection.style.display = 'none';
        }
        this.currentResult = null;
    }

    /**
     * 初始化結果區域
     */
    initResultsSection() {
        // 結果區域的基本設置
        console.log('Results section initialized');
    }
}

// 確保 GoalSimulator 在全域範圍內可用
window.GoalSimulator = GoalSimulator;