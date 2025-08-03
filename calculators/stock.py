import numpy as np
from typing import Dict, Union

def stock_investment_simulation(
    initial_amount: float,
    monthly_amount: float,
    expected_return: float,
    volatility: float,
    years: int,
    simulations: int = 10000
) -> Dict[str, Union[float, int]]:
    """
    股票投資蒙地卡羅模擬
    
    參數:
        initial_amount: 初始投入金額 (TWD)
        monthly_amount: 每年額外投入金額 (TWD)
        expected_return: 預期年報酬率 (%)
        volatility: 波動率 (%)
        years: 投資年限
        simulations: 模擬次數 (預設 10,000)
    
    回傳:
        dict: 包含以下鍵值的字典
            - mean: 平均最終價值
            - percentile_5: 5% 最差情況
            - percentile_95: 95% 最佳情況
            - total_investment: 總投資金額
            - mean_return: 平均年化報酬率 (%)
            - worst_case: 最差情況年化報酬率 (%)
            - best_case: 最佳情況年化報酬率 (%)
    """
    
    # 轉換百分比為小數
    expected_return_decimal = expected_return / 100
    volatility_decimal = volatility / 100
    
    # 儲存所有模擬結果
    final_values = []
    
    # 執行蒙地卡羅模擬
    for _ in range(simulations):
        portfolio_value = initial_amount
        
        for year in range(years):
            # 每年額外投入
            portfolio_value += monthly_amount
            
            # 生成隨機年報酬率 (常態分布)
            random_return = np.random.normal(expected_return_decimal, volatility_decimal)
            
            # 計算該年結束後的投資組合價值
            portfolio_value *= (1 + random_return)
        
        final_values.append(portfolio_value)
    
    # 轉換為 numpy 陣列並排序
    final_values = np.array(final_values)
    final_values_sorted = np.sort(final_values)
    
    # 計算統計值
    mean = np.mean(final_values)
    percentile_5 = np.percentile(final_values_sorted, 5)
    percentile_95 = np.percentile(final_values_sorted, 95)
    total_investment = initial_amount + (monthly_amount * years)
    
    # 計算年化報酬率 = (最終價值 / 總投資金額) ^ (1/年數) - 1
    mean_return = (pow(mean / total_investment, 1/years) - 1) * 100
    worst_case = (pow(percentile_5 / total_investment, 1/years) - 1) * 100
    best_case = (pow(percentile_95 / total_investment, 1/years) - 1) * 100
    
    return {
        'mean': round(mean, 0),
        'percentile_5': round(percentile_5, 0),
        'percentile_95': round(percentile_95, 0),
        'total_investment': total_investment,
        'mean_return': round(mean_return, 2),
        'worst_case': round(worst_case, 2),
        'best_case': round(best_case, 2)
    }