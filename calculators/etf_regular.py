import numpy as np
from scipy.optimize import newton
import math

def ETFRegularInvestment(initial_amount, monthly_amount, dividend_yield, price_growth, years):
    """
    ETF定期定額投資計算函式（分離配息與價格成長）
    
    Args:
        initial_amount (float): 初始投入金額 (TWD)
        monthly_amount (float): 每月定期投入 (TWD)
        dividend_yield (float): 年配息率 (%)
        price_growth (float): 年價格成長率 (%)
        years (int): 投資年限
    
    Returns:
        dict: 包含投資結果的字典
            - final_value: 最終價值
            - total_investment: 總投資金額
            - profit: 獲利
            - roi: 投資報酬率 (%)
            - irr: 內部報酬率 (%)
            - annualized_return: 年化報酬率 (%)
            - dividend_income: 累積配息收入
            - capital_gain: 資本利得
    """
    
    # 轉換百分比為小數
    dividend_rate = dividend_yield / 100
    growth_rate = price_growth / 100
    total_annual_return = dividend_rate + growth_rate
    
    monthly_dividend_rate = dividend_rate / 12
    monthly_growth_rate = growth_rate / 12
    total_months = years * 12
    
    # 計算最終價值（考慮配息再投入）
    # 使用逐月計算來精確處理配息再投入
    
    current_shares = 0  # 持有股數
    current_price = 100  # 假設初始股價為100（基準價格）
    total_dividend_income = 0  # 累積配息收入
    
    # 初始投入
    if initial_amount > 0:
        initial_shares = initial_amount / current_price
        current_shares += initial_shares
    
    # 逐月計算
    for month in range(total_months):
        # 股價成長
        current_price *= (1 + monthly_growth_rate)
        
        # 月配息（假設每月配息1/12）
        monthly_dividend = current_shares * current_price * monthly_dividend_rate
        total_dividend_income += monthly_dividend
        
        # 配息再投入購買股份
        if monthly_dividend > 0:
            dividend_shares = monthly_dividend / current_price
            current_shares += dividend_shares
        
        # 每月定投
        if monthly_amount > 0:
            monthly_shares = monthly_amount / current_price
            current_shares += monthly_shares
    
    # 最終價值
    final_value = current_shares * current_price
    
    # 計算總投資金額
    total_investment = initial_amount + monthly_amount * total_months
    
    # 計算獲利
    profit = final_value - total_investment
    
    # 計算資本利得（最終價值減去總投資和配息收入）
    capital_gain = final_value - total_investment - total_dividend_income
    
    # 計算年化報酬率
    if total_investment > 0:
        annualized_return = ((final_value / total_investment) ** (1/years) - 1) * 100
    else:
        annualized_return = 0
    
    # 計算內部報酬率 (IRR)
    def npv(monthly_rate_guess):
        """淨現值函數，用於計算IRR"""
        if monthly_rate_guess <= -1:
            return float('inf')
            
        npv_value = 0
        
        # 第0個月：初始投入 + 第一次定投
        npv_value -= (initial_amount + monthly_amount)
        
        # 第1到第total_months-1個月：每月定投
        for month in range(1, total_months):
            npv_value -= monthly_amount / (1 + monthly_rate_guess) ** month
        
        # 第total_months個月：收回最終價值
        npv_value += final_value / (1 + monthly_rate_guess) ** total_months
        
        return npv_value
    
    try:
        # 使用牛頓法求解月IRR，然後轉換為年IRR
        monthly_irr = newton(npv, total_annual_return/12)
        irr = ((1 + monthly_irr) ** 12 - 1) * 100
    except:
        # 如果無法收斂，使用近似值
        irr = annualized_return
    
    # 計算投資報酬率 (ROI)
    if total_investment > 0:
        roi = (profit / total_investment) * 100
    else:
        roi = 0
    
    return {
        'final_value': round(final_value, 2),
        'total_investment': round(total_investment, 2),
        'profit': round(profit, 2),
        'roi': round(roi, 2),
        'irr': round(irr, 2),
        'annualized_return': round(annualized_return, 2),
        'dividend_income': round(total_dividend_income, 2),
        'capital_gain': round(capital_gain, 2)
    }