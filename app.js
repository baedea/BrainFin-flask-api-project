/* =======================
   全域工具 / 常數
   ======================= */

let currentChart = null;

// 前端型別 -> 後端 Enum
const API_TYPE_ENUM = {
  real_estate: 'REAL_ESTATE',
  etf: 'ETF_REGULAR',
  stock: 'STOCK',
  fund: 'MUTUAL_FUND',
  bond: 'BOND_DEPOSIT'
};

// 後端 Enum -> 前端型別
const ENUM_TO_FRONT = {
  REAL_ESTATE: 'real_estate',
  ETF_REGULAR: 'etf',
  STOCK: 'stock',
  MUTUAL_FUND: 'fund',
  BOND_DEPOSIT: 'bond'
};

// 顯示標籤
const FRONT_LABELS = {
  real_estate: '🏠 房地產投資',
  etf: '📈 ETF 定期定額',
  stock: '📊 股票投資',
  fund: '💰 基金投資',
  bond: '💎 美債/定存'
};

const BACKEND_LABELS = {
  REAL_ESTATE: '🏠 房地產投資',
  ETF_REGULAR: '📈 ETF 定期定額',
  STOCK: '📊 股票投資',
  MUTUAL_FUND: '💰 基金投資',
  BOND_DEPOSIT: '💎 美債/定存'
};

function safeToFixed(value, decimals = 2) {
  if (value === null || value === undefined || isNaN(value)) return '0.00';
  return Number(value).toFixed(decimals);
}

function formatCurrency(amount) {
  if (typeof amount !== 'number') return amount;
  return amount.toLocaleString('zh-TW', { style: 'currency', currency: 'TWD', minimumFractionDigits: 0 });
}

function safeCurrency(value) {
  if (value === null || value === undefined || isNaN(value)) return 'NT$ 0';
  return formatCurrency(value);
}

function getFieldValue(data, fields, def = 0) {
  for (const f of fields) {
    if (data[f] !== undefined && data[f] !== null) return data[f];
  }
  return def;
}

function getTypeLabel(type) {
  if (FRONT_LABELS[type]) return FRONT_LABELS[type];
  if (BACKEND_LABELS[type]) return BACKEND_LABELS[type];
  return type || '未知類型';
}

function getLabelFromRecord(record) {
  if (record && record.investment_type) return getTypeLabel(record.investment_type);
  if (record && record.result && record.result.type) return getTypeLabel(record.result.type);
  return '未知類型';
}

function showLoading() { document.getElementById('loading').classList.remove('hidden'); }
function hideLoading() { document.getElementById('loading').classList.add('hidden'); }
function showError(message) {
  const el = document.getElementById('error');
  el.textContent = message;
  el.classList.remove('hidden');
}
function hideError() { document.getElementById('error').classList.add('hidden'); }
function showSuccess(message) {
  const el = document.getElementById('success');
  el.textContent = message;
  el.classList.remove('hidden');
  setTimeout(hideSuccess, 3000);
}
function hideSuccess() { document.getElementById('success').classList.add('hidden'); }
function hideResults() { document.getElementById('results').classList.add('hidden'); }

/**
 * 將不同投資類型的欄位統一化
 */
function normalizeResult(result, frontendType) {
  const r = { ...result };
  r.type = r.type || frontendType;

  // 總投入金額
  const totalInvested = getFieldValue(r, [
    'total_investment', 'total_cost', 'total_invested',
    'initial_amount', 'principal', 'total_principal', 'total_contribution', 'invested_total'
  ], 0);

  if (!r.total_investment || r.total_investment === 0) {
    r.total_investment = totalInvested;
  }

  if (!r.total_investment || r.total_investment === 0) {
    const init = Number(r.initial_amount || 0);
    const monthly = Number(r.monthly_amount || 0);
    const years = Number(r.years || r.simulation_years || 0);
    const estimated = init + monthly * years * 12;
    if (estimated > 0) r.total_investment = estimated;
  }

  let roi = getFieldValue(r, ['roi', 'investment_ratio'], 0);
  r.roi = roi <= 1 ? roi * 100 : roi;

  let ann = getFieldValue(r, ['annualized_return', 'irr', 'mean_return'], 0);
  r.annualized_return = ann <= 1 ? ann * 100 : ann;

  return r;
}

/* =======================
   投資類型切換
   ======================= */
document.querySelectorAll('.investment-btn').forEach(btn => {
  btn.addEventListener('click', function() {
    document.querySelectorAll('.investment-btn').forEach(b => b.classList.remove('active'));
    this.classList.add('active');

    document.querySelectorAll('.investment-form').forEach(f => f.classList.add('hidden'));

    const type = this.dataset.type;
    const form = document.getElementById(type + '_form');
    if (form) form.classList.remove('hidden');

    hideResults();
  });
});

/* =======================
   表單提交（統一端點）
   ======================= */
document.querySelectorAll('.investment-form').forEach(form => {
  form.addEventListener('submit', async function(e) {
    e.preventDefault();

    const formData = new FormData(this);
    const data = Object.fromEntries(formData.entries());
    const frontendType = this.id.replace('_form', '');

    for (const k in data) {
      if (!isNaN(data[k]) && data[k] !== '') data[k] = parseFloat(data[k]);
    }

    await submitInvestmentForm(frontendType, data);
  });
});

async function submitInvestmentForm(frontendType, parameters) {
  const apiUrl = document.getElementById('api_url').value.trim();
  if (!apiUrl) {
    showError('請輸入 API URL');
    return;
  }

  const enumType = API_TYPE_ENUM[frontendType];
  if (!enumType) {
    showError('未知的投資類型');
    return;
  }

  showLoading();
  hideResults();
  hideError();
  hideSuccess();

  try {
    const response = await fetch(`${apiUrl}/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        investment_type: enumType,
        parameters,
        save_to_db: true
      })
    });

    if (!response.ok) {
      let msg = `API 請求失敗: ${response.status}`;
      try {
        const err = await response.json();
        if (err && (err.detail || err.error)) msg = err.detail || err.error;
      } catch(_) {}
      throw new Error(msg);
    }

    const apiResponse = await response.json();
    if (!apiResponse.success || !apiResponse.result) {
      throw new Error('API 回應格式錯誤');
    }

    const backendEnum = apiResponse.investment_type;
    const frontType = ENUM_TO_FRONT[backendEnum] || frontendType;

    const normalized = normalizeResult(apiResponse.result, frontType);
    displayResults(normalized);

    showSuccess('模擬計算完成！');
    await loadHistory();

  } catch (err) {
    console.error(err);
    showError(`模擬失敗: ${err.message}`);
  } finally {
    hideLoading();
  }
}

/* =======================
   結果顯示
   ======================= */

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

function displayRealEstateResults(data, container) {
  const years = getFieldValue(data, ['years', 'simulation_years'], 0);

  const items = [
    { label: '投資類型', value: getTypeLabel(data.type) },
    { label: '總持有成本', value: safeCurrency(getFieldValue(data, ['total_cost'])) },
    { label: '目前房價', value: safeCurrency(getFieldValue(data, ['current_value'])) },
    { label: '每月還款', value: safeCurrency(getFieldValue(data, ['monthly_payment'])) },
    { label: '總獲利', value: safeCurrency(getFieldValue(data, ['profit'])) },
    { label: '投資報酬率', value: `${safeToFixed(data.roi)}%` },
    { label: '年化報酬率', value: `${safeToFixed(data.annualized_return)}%` }
  ];

  const finalVal = getFieldValue(data, ['final_value'], null);
  if (finalVal !== null) {
    items.splice(2, 0, { label: `${years}年後房價`, value: safeCurrency(finalVal) });
  }

  items.forEach(i => container.appendChild(createResultItem(i.label, i.value)));
}

function displayGeneralResults(data, container) {
  const years = getFieldValue(data, ['years', 'simulation_years'], 0);

  let roi = getFieldValue(data, ['roi', 'investment_ratio'], 0);
  roi = roi <= 1 ? roi * 100 : roi;

  let ann = getFieldValue(data, ['annualized_return', 'irr', 'mean_return'], 0);
  ann = ann <= 1 ? ann * 100 : ann;

  const items = [
    { label: '投資類型', value: getTypeLabel(data.type) }
  ];

  const init = getFieldValue(data, ['initial_amount', 'principal']);
  if (init > 0) items.push({ label: '初始投資', value: safeCurrency(init) });

  const monthly = getFieldValue(data, ['monthly_amount']);
  if (monthly > 0) items.push({ label: '每月投入', value: safeCurrency(monthly) });

  const totalInvested = getFieldValue(data, [
    'total_investment', 'total_cost', 'total_invested',
    'initial_amount', 'principal', 'total_principal', 'total_contribution', 'invested_total'
  ]);
  items.push({ label: '總投入金額', value: safeCurrency(totalInvested) });

  const finalValue = getFieldValue(data, ['final_value', 'current_value', 'mean']);
  if (finalValue) items.push({ label: `${years || ''}年後總值`, value: safeCurrency(finalValue) });

  const totalProfit = getFieldValue(data, ['profit', 'total_profit', 'mean_profit']);
  if (totalProfit || totalProfit === 0) items.push({ label: '總獲利', value: safeCurrency(totalProfit) });

  items.push({ label: '投資報酬率', value: `${safeToFixed(roi)}%` });
  if (ann !== 0) items.push({ label: '年化報酬率', value: `${safeToFixed(ann)}%` });

  const p5 = getFieldValue(data, ['percentile_5'], null);
  const p95 = getFieldValue(data, ['percentile_95'], null);
  if (p5 !== null && p95 !== null) {
    items.push({ label: '5% 最差情境總值', value: safeCurrency(p5) });
    items.push({ label: '95% 最佳情境總值', value: safeCurrency(p95) });
  }

  const worst = getFieldValue(data, ['worst_case'], null);
  const best = getFieldValue(data, ['best_case'], null);
  if (worst !== null && best !== null) {
    items.push({ label: '最差年化報酬', value: `${safeToFixed(worst)}%` });
    items.push({ label: '最佳年化報酬', value: `${safeToFixed(best)}%` });
  }

  items.forEach(i => container.appendChild(createResultItem(i.label, i.value)));
}

function createResultItem(label, value) {
  const div = document.createElement('div');
  div.className = 'result-item';
  div.innerHTML = `
    <span class="label">${label}:</span>
    <span class="value">${value}</span>
  `;
  return div;
}

function displayChart(data) {
  const ctx = document.getElementById('investmentChart').getContext('2d');

  if (currentChart) currentChart.destroy();

  const labels = data.yearly_data.map((_, i) => `第${i + 1}年`);
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
            callback: v => formatCurrency(v)
          }
        }
      },
      interaction: { intersect: false, mode: 'index' }
    }
  });
}

/* =======================
   歷史紀錄
   ======================= */
async function loadHistory() {
  const apiUrl = document.getElementById('api_url').value.trim();
  if (!apiUrl) return;

  try {
    const resp = await fetch(`${apiUrl}/history`);
    if (!resp.ok) throw new Error('無法載入歷史記錄');
    const history = await resp.json();
    displayHistory(history);
  } catch (e) {
    console.error('載入歷史記錄失敗:', e);
    document.getElementById('history_list').innerHTML =
      '<p style="text-align: center; color: #999;">載入歷史記錄失敗</p>';
  }
}

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
    const result = record.result || {};
    const label = getLabelFromRecord(record);

    let roi = getFieldValue(result, ['roi', 'investment_ratio'], 0);
    roi = roi <= 1 ? roi * 100 : roi;

    const profit = getFieldValue(result, ['profit', 'total_profit', 'mean_profit'], 0);
    const timeStr = record.created_at ? new Date(record.created_at).toLocaleString('zh-TW') : '';

    return `
      <div class="history-item">
        <div class="history-item-header">
          ${label} ${timeStr ? '- ' + timeStr : ''}
        </div>
        <div class="history-item-details">
          總獲利: ${safeCurrency(profit)} | ROI: ${safeToFixed(roi)}%
        </div>
      </div>
    `;
  }).join('');
}

// 初始化
window.addEventListener('DOMContentLoaded', () => {
  loadHistory();
});