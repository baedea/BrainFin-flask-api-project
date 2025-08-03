def house_investment_analysis(house_price, down_payment, loan_rate, loan_years, 
                              appreciation_rate_a, appreciation_rate_b, annual_cost, simulation_years, scenario="A"):
    """
    房屋投資分析函數
    
    參數:
    house_price: 房屋價格 (TWD)
    down_payment: 頭期款 (TWD)
    loan_rate: 貸款利率 (%)
    loan_years: 貸款年限
    appreciation_rate_a: 情境A預期房價總漲幅 (%)
    appreciation_rate_b: 情境B預期房價總漲幅 (%)
    annual_cost: 年度持有成本 (TWD)
    simulation_years: 模擬年數
    scenario: 情境選擇 ("A"=提前賣出, "B"=持有到貸款還完)
    
    回傳:
    dict: 包含完整投資分析結果
    """
    
    # 計算貸款金額
    loan_amount = house_price - down_payment
    
    # 計算月利率
    monthly_rate = loan_rate / 100 / 12
    
    # 計算總還款月數
    total_months = loan_years * 12
    
    # 計算每月還款金額 (本息均攤)
    if monthly_rate > 0:
        monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** total_months) / \
                         ((1 + monthly_rate) ** total_months - 1)
    else:
        monthly_payment = loan_amount / total_months
    
    if scenario == "A":
        # 情境A：持有simulation_years年後賣出
        
        # 使用情境A的漲幅
        annual_appreciation_rate = ((1 + appreciation_rate_a / 100) ** (1 / simulation_years) - 1) * 100
        current_value = house_price * (1 + appreciation_rate_a / 100)
        
        # 計算模擬期間的還款金額
        months_in_simulation = simulation_years * 12
        total_loan_payments = monthly_payment * months_in_simulation
        
        # 計算模擬期間已還本金
        if monthly_rate > 0:
            # 使用貸款餘額公式計算剩餘本金
            remaining_principal = loan_amount * ((1 + monthly_rate) ** total_months - 
                                               (1 + monthly_rate) ** months_in_simulation) / \
                                 ((1 + monthly_rate) ** total_months - 1)
        else:
            remaining_principal = loan_amount * (total_months - months_in_simulation) / total_months
        
        principal_paid = loan_amount - remaining_principal
        interest_paid = total_loan_payments - principal_paid
        
        # 計算持有成本
        total_holding_cost = annual_cost * simulation_years
        
        # 實際現金支出 = 頭期款 + 模擬期間還款 + 持有成本
        actual_cash_outflow = down_payment + total_loan_payments + total_holding_cost
        
        # 賣房實際收入 = 房屋現值 - 剩餘本金（還債）
        actual_sale_income = current_value - remaining_principal
        
        scenario_description = f"情境A：持有{simulation_years}年後賣出"
        
    else:  # scenario == "B"
        # 情境B：持有到貸款還完
        
        # 使用情境B的漲幅和貸款年限
        annual_appreciation_rate = ((1 + appreciation_rate_b / 100) ** (1 / loan_years) - 1) * 100
        current_value = house_price * (1 + appreciation_rate_b / 100)
        
        # 計算整個貸款期間的總還款
        total_loan_payments = monthly_payment * total_months
        
        # 計算整個貸款期間的利息支出
        interest_paid = total_loan_payments - loan_amount
        
        # 計算持有成本（以貸款年限計算）
        total_holding_cost = annual_cost * loan_years
        
        # 實際現金支出 = 頭期款 + 全部還款 + 持有成本
        actual_cash_outflow = down_payment + total_loan_payments + total_holding_cost
        
        # 賣房實際收入 = 房屋現值（債務已還完）
        actual_sale_income = current_value
        
        remaining_principal = 0  # 貸款已還完
        scenario_description = f"情境B：持有到貸款還完({loan_years}年)"
    
    # 計算獲利 = 賣房實際收入 - 實際現金支出
    profit = actual_sale_income - actual_cash_outflow
    
    # 計算投資報酬率 = 獲利 / 實際現金支出 * 100
    roi = (profit / actual_cash_outflow) * 100 if actual_cash_outflow > 0 else 0
    
    return {
        'scenario': scenario_description,
        'actual_cash_outflow': round(actual_cash_outflow, 0),
        'actual_sale_income': round(actual_sale_income, 0),
        'current_value': round(current_value, 0),
        'profit': round(profit, 0),
        'roi': round(roi, 2),
        'annual_return': round(annual_appreciation_rate, 2),  # 改名為預期年報酬
        'monthly_payment': round(monthly_payment, 0),
        'loan_years': loan_years,
        'interest_paid': round(interest_paid, 0),
        'total_loan_payments': round(total_loan_payments, 0),
        'remaining_principal': round(remaining_principal, 0),
        'holding_cost': round(total_holding_cost, 0)
    }