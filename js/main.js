/**
 * Investment Calculator - Main Application Controller
 * 主控制器，負責頁面導航、全域功能和API通訊
 */

class InvestmentApp {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8001/api/v1'; // FastAPI backend URL
        this.currentPage = 'home';
        this.calculationHistory = this.loadHistory();
        this.currentSimulationId = null;
        
        this.init();
    }

    /**
     * 初始化應用程式
     */
    init() {
        this.initNavigation();
        this.initEventListeners();
        this.initGoalSimulator();
        this.loadInitialData();
        this.updateStats();
        
        console.log('Investment Calculator App initialized');
    }

    /**
     * 初始化導航功能
     */
    initNavigation() {
        const navLinks = document.querySelectorAll('.nav-link');
        const pages = document.querySelectorAll('.page');
        const navToggle = document.getElementById('navToggle');
        const navMenu = document.getElementById('navMenu');

        // 處理導航點擊
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const targetPage = link.getAttribute('data-page');
                this.navigateToPage(targetPage);
            });
        });

        // 移動端導航切換
        if (navToggle) {
            navToggle.addEventListener('click', () => {
                navMenu.classList.toggle('active');
            });
        }

        // URL 路由處理
        window.addEventListener('hashchange', () => {
            const hash = window.location.hash.slice(1);
            if (hash) {
                this.navigateToPage(hash);
            }
        });

        // 初始頁面路由
        const initialHash = window.location.hash.slice(1);
        if (initialHash) {
            this.navigateToPage(initialHash);
        }
    }

    /**
     * 導航到指定頁面
     */
    navigateToPage(pageName) {
        // 更新活動導航連結
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('data-page') === pageName) {
                link.classList.add('active');
            }
        });

        // 顯示目標頁面
        document.querySelectorAll('.page').forEach(page => {
            page.classList.remove('active');
            if (page.id === pageName) {
                page.classList.add('active');
            }
        });

        this.currentPage = pageName;
        window.location.hash = pageName;

        // 頁面特定初始化
        this.handlePageLoad(pageName);
    }

    /**
     * 處理頁面載入邏輯
     */
    handlePageLoad(pageName) {
        switch (pageName) {
            case 'goal-simulator':
                this.loadGoalSimulatorPage();
                break;
            case 'history':
                this.loadHistoryPage();
                break;
            case 'backtesting':
                this.loadBacktestingPage();
                break;
            default:
                break;
        }
    }

    /**
     * 初始化事件監聽器
     */
    initEventListeners() {
        // 功能卡片點擊事件
        document.querySelectorAll('.feature-card').forEach(card => {
            card.addEventListener('click', () => {
                const investmentType = card.getAttribute('data-investment');
                this.navigateToPage('goal-simulator');
                setTimeout(() => {
                    this.switchInvestmentType(investmentType);
                }, 100);
            });
        });

        // 歷史記錄篩選
        const historyFilter = document.getElementById('historyFilter');
        if (historyFilter) {
            historyFilter.addEventListener('change', () => {
                this.filterHistory(historyFilter.value);
            });
        }

        // 清除歷史記錄
        const clearHistoryBtn = document.getElementById('clearHistory');
        if (clearHistoryBtn) {
            clearHistoryBtn.addEventListener('click', () => {
                this.clearHistory();
            });
        }

        // 鍵盤快捷鍵
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case '1':
                        e.preventDefault();
                        this.navigateToPage('home');
                        break;
                    case '2':
                        e.preventDefault();
                        this.navigateToPage('goal-simulator');
                        break;
                    case '3':
                        e.preventDefault();
                        this.navigateToPage('history');
                        break;
                }
            }
        });
    }

    /**
     * 初始化財務目標模擬器
     */
    initGoalSimulator() {
        // 這個方法會在 goal-simulator.js 中擴展
        if (typeof GoalSimulator !== 'undefined') {
            this.goalSimulator = new GoalSimulator(this);
        }
    }

    /**
     * 載入財務目標模擬器頁面
     */
    loadGoalSimulatorPage() {
        const content = document.getElementById('goalSimulatorContent');
        if (content && content.innerHTML.trim() === '') {
            // 載入模擬器內容
            fetch('pages/goal-simulator.html')
                .then(response => response.text())
                .then(html => {
                    content.innerHTML = html;
                    this.initGoalSimulator();
                })
                .catch(error => {
                    console.error('Error loading goal simulator:', error);
                    content.innerHTML = '<p>載入模擬器時發生錯誤</p>';
                });
        }
    }

    /**
     * 載入歷史記錄頁面
     */
    loadHistoryPage() {
        this.renderHistory();
    }

    /**
     * 載入回測分析頁面
     */
    loadBacktestingPage() {
        // 未來功能
        console.log('Backtesting page loaded');
    }

    /**
     * API 請求通用方法
     */
    async apiRequest(endpoint, method = 'GET', data = null) {
        const url = `${this.apiBaseUrl}${endpoint}`;
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            },
        };

        if (data) {
            options.body = JSON.stringify(data);
        }

        try {
            this.showLoading();
            const response = await fetch(url, options);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            this.hideLoading();
            return result;
        } catch (error) {
            this.hideLoading();
            console.error('API request failed:', error);
            this.showToast('API 請求失敗: ' + error.message, 'error');
            throw error;
        }
    }

    /**
     * 計算投資
     */
    async calculateInvestment(investmentType, parameters) {
        try {
            const requestData = {
                investment_type: investmentType,
                parameters: parameters,
                save_to_db: true
            };

            const result = await this.apiRequest('/calculate', 'POST', requestData);
            
            this.currentSimulationId = result.id;
            this.addToHistory(result);
            this.showToast('計算完成！', 'success');
            
            return result;
        } catch (error) {
            this.showToast('計算失敗，請檢查輸入參數', 'error');
            throw error;
        }
    }

    /**
     * 取得歷史記錄
     */
    async getHistory(limit = 50, investmentType = null) {
        try {
            let endpoint = `/history?limit=${limit}`;
            if (investmentType) {
                endpoint += `&investment_type=${investmentType}`;
            }
            
            const result = await this.apiRequest(endpoint);
            return result;
        } catch (error) {
            console.error('Failed to fetch history:', error);
            return [];
        }
    }

    /**
     * 顯示載入動畫
     */
    showLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.add('show');
        }
    }

    /**
     * 隱藏載入動畫
     */
    hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.remove('show');
        }
    }

    /**
     * 顯示通知
     */
    showToast(message, type = 'info', duration = 3000) {
        const container = document.getElementById('toastContainer');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;

        container.appendChild(toast);

        // 自動移除
        setTimeout(() => {
            toast.remove();
        }, duration);
    }

    /**
     * 本地歷史記錄管理
     */
    loadHistory() {
        try {
            const history = localStorage.getItem('investmentHistory');
            return history ? JSON.parse(history) : [];
        } catch (error) {
            console.error('Failed to load history:', error);
            return [];
        }
    }

    saveHistory() {
        try {
            localStorage.setItem('investmentHistory', JSON.stringify(this.calculationHistory));
        } catch (error) {
            console.error('Failed to save history:', error);
        }
    }

    addToHistory(calculation) {
        this.calculationHistory.unshift({
            ...calculation,
            timestamp: new Date().toISOString()
        });

        // 限制歷史記錄數量
        if (this.calculationHistory.length > 100) {
            this.calculationHistory = this.calculationHistory.slice(0, 100);
        }

        this.saveHistory();
        this.updateStats();
    }

    clearHistory() {
        if (confirm('確定要清除所有計算歷史嗎？此操作無法復原。')) {
            this.calculationHistory = [];
            this.saveHistory();
            this.renderHistory();
            this.updateStats();
            this.showToast('歷史記錄已清除', 'success');
        }
    }

    filterHistory(type) {
        this.renderHistory(type);
    }

    /**
     * 渲染歷史記錄
     */
    renderHistory(filterType = '') {
        const container = document.getElementById('historyContent');
        if (!container) return;

        let filteredHistory = this.calculationHistory;
        if (filterType) {
            filteredHistory = this.calculationHistory.filter(item => 
                item.investment_type === filterType
            );
        }

        if (filteredHistory.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-inbox"></i>
                    <h3>尚無計算記錄</h3>
                    <p>開始使用投資計算器，這裡會顯示您的計算歷史</p>
                </div>
            `;
            return;
        }

        const historyHTML = filteredHistory.map(item => this.renderHistoryItem(item)).join('');
        container.innerHTML = historyHTML;
    }

    /**
     * 渲染單個歷史記錄項目
     */
    renderHistoryItem(item) {
        const typeMap = {
            'real_estate': { icon: 'fas fa-home', name: '房地產投資' },
            'etf_regular': { icon: 'fas fa-chart-pie', name: 'ETF定期定額' },
            'stock': { icon: 'fas fa-chart-line', name: '股票投資' },
            'bond_deposit': { icon: 'fas fa-piggy-bank', name: '債券定存' }
        };

        const type = typeMap[item.investment_type] || { icon: 'fas fa-calculator', name: '未知類型' };
        const date = new Date(item.timestamp || item.created_at).toLocaleString('zh-TW');

        // 根據投資類型顯示不同的摘要資訊
        let summaryHTML = '';
        switch (item.investment_type) {
            case 'real_estate':
                summaryHTML = `
                    <div class="summary-item">
                        <div class="summary-value">${this.formatCurrency(item.result.profit)}</div>
                        <div class="summary-label">獲利</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-value">${item.result.roi}%</div>
                        <div class="summary-label">ROI</div>
                    </div>
                `;
                break;
            case 'etf_regular':
                summaryHTML = `
                    <div class="summary-item">
                        <div class="summary-value">${this.formatCurrency(item.result.final_value)}</div>
                        <div class="summary-label">最終價值</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-value">${item.result.annualized_return}%</div>
                        <div class="summary-label">年化報酬</div>
                    </div>
                `;
                break;
            case 'stock':
                summaryHTML = `
                    <div class="summary-item">
                        <div class="summary-value">${this.formatCurrency(item.result.mean)}</div>
                        <div class="summary-label">平均最終價值</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-value">${item.result.mean_return}%</div>
                        <div class="summary-label">平均年化報酬</div>
                    </div>
                `;
                break;
            case 'bond_deposit':
                summaryHTML = `
                    <div class="summary-item">
                        <div class="summary-value">${this.formatCurrency(item.result.final_value)}</div>
                        <div class="summary-label">最終價值</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-value">${item.result.real_return}%</div>
                        <div class="summary-label">實質報酬率</div>
                    </div>
                `;
                break;
        }

        return `
            <div class="history-item" data-id="${item.id}">
                <div class="history-header">
                    <div class="history-type">
                        <i class="${type.icon}"></i>
                        <span>${type.name}</span>
                    </div>
                    <div class="history-date">${date}</div>
                </div>
                <div class="history-summary">
                    ${summaryHTML}
                </div>
            </div>
        `;
    }

    /**
     * 更新統計資訊
     */
    updateStats() {
        const totalCalculationsElement = document.getElementById('totalCalculations');
        if (totalCalculationsElement) {
            totalCalculationsElement.textContent = this.calculationHistory.length.toLocaleString();
        }
    }

    /**
     * 載入初始資料
     */
    async loadInitialData() {
        try {
            // 檢查 API 連線狀態
            await this.apiRequest('/health');
            console.log('API connection established');
        } catch (error) {
            console.warn('API not available, using local mode');
            this.showToast('後端服務暫時無法連線，將使用本地模式', 'warning');
        }
    }

    /**
     * 切換投資類型
     */
    switchInvestmentType(type) {
        if (this.goalSimulator) {
            this.goalSimulator.switchTab(type);
        }
    }

    /**
     * 格式化貨幣
     */
    formatCurrency(amount) {
        if (typeof amount !== 'number') return '---';
        
        if (amount >= 10000) {
            return (amount / 10000).toFixed(1) + '萬';
        }
        return amount.toLocaleString();
    }

    /**
     * 格式化百分比
     */
    formatPercentage(value, decimals = 2) {
        if (typeof value !== 'number') return '---';
        return value.toFixed(decimals) + '%';
    }

    /**
     * 匯出計算結果為 PDF
     */
    async exportToPDF(simulationData) {
        try {
            // 實現 PDF 匯出功能
            this.showToast('PDF 匯出功能開發中', 'info');
        } catch (error) {
            this.showToast('PDF 匯出失敗', 'error');
        }
    }

    /**
     * 分享計算結果
     */
    async shareResult(simulationData) {
        try {
            if (navigator.share) {
                await navigator.share({
                    title: '投資計算結果',
                    text: '查看我的投資計算結果',
                    url: window.location.href
                });
            } else {
                // 複製到剪貼簿
                await navigator.clipboard.writeText(window.location.href);
                this.showToast('連結已複製到剪貼簿', 'success');
            }
        } catch (error) {
            this.showToast('分享失敗', 'error');
        }
    }

    /**
     * 儲存計算結果
     */
    saveCalculationResult(data) {
        this.addToHistory(data);
        this.showToast('計算結果已儲存', 'success');
    }
}

// 全域實用函數
window.InvestmentUtils = {
    formatCurrency: function(amount) {
        if (typeof amount !== 'number') return '---';
        return amount.toLocaleString() + ' 元';
    },

    formatPercentage: function(value, decimals = 2) {
        if (typeof value !== 'number') return '---';
        return value.toFixed(decimals) + '%';
    },

    formatNumber: function(value, decimals = 0) {
        if (typeof value !== 'number') return '---';
        return value.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    },

    calculateAnnualizedReturn: function(finalValue, initialValue, years) {
        if (initialValue <= 0 || years <= 0) return 0;
        return (Math.pow(finalValue / initialValue, 1 / years) - 1) * 100;
    },

    calculateCompoundInterest: function(principal, rate, years, compoundFreq = 1) {
        return principal * Math.pow(1 + rate / compoundFreq, compoundFreq * years);
    }
};

// 確保在 DOM 載入完成後初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.app = new InvestmentApp();
    });
} else {
    window.app = new InvestmentApp();
}