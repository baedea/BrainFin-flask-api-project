def bond_deposit(principal, interest_rate, years, is_compound=True, inflation_rate=2.0):
    """
    債券/定存投資模擬計算器
    
    參數:
        principal (float): 本金 (TWD)
        interest_rate (float): 利率 (%)
        years (int): 投資年限
        is_compound (bool): 是否複利，預設為 True
        inflation_rate (float): 通膨率 (%)，預設為 2.0%
    
    回傳:
        dict: 包含以下鍵值的字典
            - final_value: 最終價值 (名目) (TWD)
            - real_value: 實質價值 (扣除通膨) (TWD)
            - nominal_return: 名目年化報酬率 (%)
            - real_return: 實質年化報酬率 (%)
            - inflation_impact: 通膨影響金額 (TWD)
    """
    
    # 輸入驗證
    if principal <= 0:
        raise ValueError("本金必須大於 0")
    if years <= 0:
        raise ValueError("投資年限必須大於 0")
    if interest_rate < 0:
        raise ValueError("利率不能為負數")
    
    # 將百分比轉換為小數
    interest_rate_decimal = interest_rate / 100
    inflation_rate_decimal = inflation_rate / 100
    
    # 計算最終價值 (名目價值)
    if is_compound:
        # 複利計算
        final_value = principal * (1 + interest_rate_decimal) ** years
    else:
        # 單利計算
        final_value = principal * (1 + interest_rate_decimal * years)
    
    # 計算實質價值 (扣除通膨影響)
    real_value = final_value / ((1 + inflation_rate_decimal) ** years)
    
    # 計算名目年化報酬率
    nominal_return = interest_rate
    
    # 計算實質年化報酬率
    # 使用費雪方程式: (1 + 實質利率) = (1 + 名目利率) / (1 + 通膨率)
    real_return = ((1 + interest_rate_decimal) / (1 + inflation_rate_decimal) - 1) * 100
    
    # 計算通膨影響金額
    inflation_impact = final_value - real_value
    
    return {
        'final_value': round(final_value, 2),
        'real_value': round(real_value, 2),
        'nominal_return': round(nominal_return, 2),
        'real_return': round(real_return, 2),
        'inflation_impact': round(inflation_impact, 2)
    }