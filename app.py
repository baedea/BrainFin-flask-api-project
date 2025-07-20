from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union
import numpy as np
import pandas as pd
import math
import sqlite3
import json
from datetime import datetime
from enum import Enum
from contextlib import contextmanager
import uuid
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Investment Simulation API", version="1.0.0")

app.add_middleware(
   CORSMiddleware,
   allow_origins=["https://baedea.github.io"],
   allow_credentials=True,
   allow_methods=["*"],
   allow_headers=["*"],
)
# =================================
# Database Setup
# =================================

DATABASE_PATH = "investment_simulations.db"

def init_database():
    """初始化資料庫"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # 創建投資模擬記錄表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS simulations (
            id TEXT PRIMARY KEY,
            investment_type TEXT NOT NULL,
            parameters TEXT NOT NULL,
            result TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

@contextmanager
def get_db_connection():
    """資料庫連接上下文管理器"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# 初始化資料庫
init_database()

# =================================
# Pydantic Models for Request/Response
# =================================

class InvestmentType(str, Enum):
    REAL_ESTATE = "real_estate"
    ETF_REGULAR = "etf_regular"
    STOCK = "stock"
    MUTUAL_FUND = "mutual_fund"
    BOND_DEPOSIT = "bond_deposit"

class RealEstateRequest(BaseModel):
    house_price: float = Field(..., description="房屋價格 (TWD)")
    down_payment: float = Field(..., description="頭期款 (TWD)")
    loan_rate: float = Field(..., description="貸款利率 (%)")
    loan_years: int = Field(..., description="貸款年限")
    appreciation_rate: float = Field(..., description="預期房價年漲幅 (%)")
    annual_cost: float = Field(..., description="年度持有成本 (TWD)")
    simulation_years: int = Field(..., description="模擬年數")

class ETFRegularRequest(BaseModel):
    initial_amount: float = Field(..., description="初始投入金額 (TWD)")
    monthly_amount: float = Field(..., description="每月定期投入 (TWD)")
    annual_return: float = Field(..., description="預期年報酬率 (%)")
    years: int = Field(..., description="投資年限")

class StockRequest(BaseModel):
    monthly_amount: float = Field(..., description="每月投入金額 (TWD)")
    expected_return: float = Field(..., description="預期年報酬率 (%)")
    volatility: float = Field(..., description="波動率 (%)")
    years: int = Field(..., description="投資年限")
    simulations: int = Field(1000, description="Monte Carlo 模擬次數")

class MutualFundRequest(BaseModel):
    initial_amount: float = Field(..., description="初始投入金額 (TWD)")
    annual_return: float = Field(..., description="預期年報酬率 (%)")
    years: int = Field(..., description="投資年限")

class BondDepositRequest(BaseModel):
    principal: float = Field(..., description="本金 (TWD)")
    interest_rate: float = Field(..., description="利率 (%)")
    years: int = Field(..., description="投資年限")
    is_compound: bool = Field(True, description="是否複利")
    inflation_rate: float = Field(2.0, description="通膨率 (%)")

class SimulationRequest(BaseModel):
    investment_type: InvestmentType
    parameters: Union[RealEstateRequest, ETFRegularRequest, StockRequest, MutualFundRequest, BondDepositRequest]
    save_to_db: bool = Field(True, description="是否儲存到資料庫")

class SimulationRecord(BaseModel):
    id: str
    investment_type: str
    parameters: Dict
    result: Dict
    created_at: str
    updated_at: str

class UpdateSimulationRequest(BaseModel):
    parameters: Union[RealEstateRequest, ETFRegularRequest, StockRequest, MutualFundRequest, BondDepositRequest]

# =================================
# Database Functions
# =================================

def save_simulation_to_db(simulation_id: str, investment_type: str, parameters: Dict, result: Dict) -> str:
    """儲存模擬結果到資料庫"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO simulations (id, investment_type, parameters, result)
            VALUES (?, ?, ?, ?)
        ''', (simulation_id, investment_type, json.dumps(parameters), json.dumps(result)))
        conn.commit()
        return simulation_id

def get_simulation_from_db(simulation_id: str) -> Optional[Dict]:
    """從資料庫取得模擬結果"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM simulations WHERE id = ?', (simulation_id,))
        row = cursor.fetchone()
        
        if row:
            return {
                "id": row["id"],
                "investment_type": row["investment_type"],
                "parameters": json.loads(row["parameters"]),
                "result": json.loads(row["result"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
        return None

def get_all_simulations_from_db() -> List[Dict]:
    """取得所有模擬記錄"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM simulations ORDER BY created_at DESC')
        rows = cursor.fetchall()
        
        return [
            {
                "id": row["id"],
                "investment_type": row["investment_type"],
                "parameters": json.loads(row["parameters"]),
                "result": json.loads(row["result"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
            for row in rows
        ]

def update_simulation_in_db(simulation_id: str, parameters: Dict, result: Dict) -> bool:
    """更新資料庫中的模擬結果"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE simulations 
            SET parameters = ?, result = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (json.dumps(parameters), json.dumps(result), simulation_id))
        conn.commit()
        return cursor.rowcount > 0

def delete_simulation_from_db(simulation_id: str) -> bool:
    """從資料庫刪除模擬記錄"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM simulations WHERE id = ?', (simulation_id,))
        conn.commit()
        return cursor.rowcount > 0

# =================================
# Investment Simulation Classes (from original code)
# =================================

class RealEstateSimulation:
    def __init__(self, house_price: float, down_payment: float, loan_rate: float, 
                 loan_years: int, appreciation_rate: float, annual_cost: float):
        self.house_price = house_price
        self.down_payment = down_payment
        self.loan_amount = house_price - down_payment
        self.loan_rate = loan_rate / 100
        self.loan_years = loan_years
        self.appreciation_rate = appreciation_rate / 100
        self.annual_cost = annual_cost
    
    def calculate_monthly_payment(self) -> float:
        """計算月付金"""
        monthly_rate = self.loan_rate / 12
        total_payments = self.loan_years * 12
        
        if monthly_rate == 0:
            return self.loan_amount / total_payments
        
        return (self.loan_amount * monthly_rate * (1 + monthly_rate)**total_payments) / \
               ((1 + monthly_rate)**total_payments - 1)
    
    def simulate(self, years: int) -> Dict:
        """模擬房地產投資"""
        monthly_payment = self.calculate_monthly_payment()
        total_monthly_payments = monthly_payment * min(years, self.loan_years) * 12
        total_holding_cost = self.annual_cost * years
        total_cost = self.down_payment + total_monthly_payments + total_holding_cost
        
        current_value = self.house_price * (1 + self.appreciation_rate)**years
        profit = current_value - total_cost
        roi = (profit / total_cost) * 100 if total_cost > 0 else 0
        annualized_return = ((current_value / total_cost)**(1/years) - 1) * 100 if total_cost > 0 else 0
        
        return {
            'total_cost': total_cost,
            'current_value': current_value,
            'profit': profit,
            'roi': roi,
            'annualized_return': annualized_return,
            'monthly_payment': monthly_payment
        }

class ETFRegularInvestment:
    def __init__(self, initial_amount: float, monthly_amount: float, 
                 annual_return: float, years: int):
        self.initial_amount = initial_amount
        self.monthly_amount = monthly_amount
        self.annual_return = annual_return / 100
        self.years = years
    
    def calculate_fv(self) -> float:
        """計算終值 (Future Value)"""
        monthly_rate = self.annual_return / 12
        total_months = self.years * 12
        
        # 初始投資的終值
        initial_fv = self.initial_amount * (1 + self.annual_return)**self.years
        
        # 定期定額的終值 (年金終值)
        if monthly_rate == 0:
            regular_fv = self.monthly_amount * total_months
        else:
            regular_fv = self.monthly_amount * ((1 + monthly_rate)**total_months - 1) / monthly_rate
        
        return initial_fv + regular_fv
    
    def calculate_irr(self) -> float:
        """計算內部報酬率 (IRR)"""
        total_investment = self.initial_amount + (self.monthly_amount * self.years * 12)
        final_value = self.calculate_fv()
        if total_investment <= 0:
            return 0
        return ((final_value / total_investment)**(1/self.years) - 1) * 100
    
    def simulate(self) -> Dict:
        """模擬ETF定期定額投資"""
        final_value = self.calculate_fv()
        total_investment = self.initial_amount + (self.monthly_amount * self.years * 12)
        profit = final_value - total_investment
        irr = self.calculate_irr()
        cost_return_ratio = final_value / total_investment if total_investment > 0 else 0
        
        return {
            'final_value': final_value,
            'total_investment': total_investment,
            'profit': profit,
            'irr': irr,
            'annualized_return': self.annual_return * 100,
            'cost_return_ratio': cost_return_ratio
        }

class StockInvestment:
    def __init__(self, monthly_amount: float, expected_return: float, 
                 volatility: float, years: int):
        self.monthly_amount = monthly_amount
        self.expected_return = expected_return / 100
        self.volatility = volatility / 100
        self.years = years
    
    def simulate_path(self) -> List[float]:
        """模擬單一投資路徑"""
        monthly_return = self.expected_return / 12
        monthly_volatility = self.volatility / np.sqrt(12)
        total_months = self.years * 12
        
        portfolio = 0
        path = []
        
        for month in range(total_months):
            # 隨機報酬率 (正態分佈)
            random_return = np.random.normal(monthly_return, monthly_volatility)
            
            # 更新投資組合價值
            portfolio = portfolio * (1 + random_return) + self.monthly_amount
            path.append(portfolio)
        
        return path
    
    def monte_carlo_simulation(self, simulations: int = 1000) -> Dict:
        """Monte Carlo 模擬"""
        np.random.seed(42)  # 設定隨機種子以確保結果可重現
        results = []
        
        for _ in range(simulations):
            path = self.simulate_path()
            results.append(path[-1])  # 最終值
        
        results = np.array(results)
        total_investment = self.monthly_amount * self.years * 12
        
        mean = np.mean(results)
        percentile_5 = np.percentile(results, 5)
        percentile_95 = np.percentile(results, 95)
        
        return {
            'mean': mean,
            'percentile_5': percentile_5,
            'percentile_95': percentile_95,
            'total_investment': total_investment,
            'mean_return': ((mean / total_investment)**(1/self.years) - 1) * 100 if total_investment > 0 else 0,
            'worst_case': ((percentile_5 / total_investment)**(1/self.years) - 1) * 100 if total_investment > 0 else 0,
            'best_case': ((percentile_95 / total_investment)**(1/self.years) - 1) * 100 if total_investment > 0 else 0
        }

class MutualFundInvestment:
    def __init__(self, initial_amount: float, annual_return: float, years: int):
        self.initial_amount = initial_amount
        self.annual_return = annual_return / 100
        self.years = years
    
    def simulate(self) -> Dict:
        """模擬基金投資"""
        final_value = self.initial_amount * (1 + self.annual_return)**self.years
        profit = final_value - self.initial_amount
        investment_ratio = final_value / self.initial_amount if self.initial_amount > 0 else 0
        
        return {
            'final_value': final_value,
            'initial_amount': self.initial_amount,
            'profit': profit,
            'annualized_return': self.annual_return * 100,
            'investment_ratio': investment_ratio
        }

class BondDeposit:
    def __init__(self, principal: float, interest_rate: float, years: int, 
                 is_compound: bool = True, inflation_rate: float = 2):
        self.principal = principal
        self.interest_rate = interest_rate / 100
        self.years = years
        self.is_compound = is_compound
        self.inflation_rate = inflation_rate / 100
    
    def calculate_return(self) -> float:
        """計算名目報酬"""
        if self.is_compound:
            # 複利
            return self.principal * (1 + self.interest_rate)**self.years
        else:
            # 單利
            return self.principal * (1 + self.interest_rate * self.years)
    
    def calculate_real_return(self) -> float:
        """計算實質報酬 (扣除通膨)"""
        nominal_value = self.calculate_return()
        real_value = nominal_value / (1 + self.inflation_rate)**self.years
        return real_value
    
    def simulate(self) -> Dict:
        """模擬債券/定存投資"""
        final_value = self.calculate_return()
        real_value = self.calculate_real_return()
        nominal_return = ((final_value / self.principal)**(1/self.years) - 1) * 100 if self.principal > 0 else 0
        real_return = ((real_value / self.principal)**(1/self.years) - 1) * 100 if self.principal > 0 else 0
        
        return {
            'final_value': final_value,
            'real_value': real_value,
            'nominal_return': nominal_return,
            'real_return': real_return,
            'inflation_impact': final_value - real_value
        }

# =================================
# Helper Functions
# =================================

def run_simulation(investment_type: InvestmentType, params: Dict) -> Dict:
    """執行投資模擬"""
    if investment_type == InvestmentType.REAL_ESTATE:
        simulator = RealEstateSimulation(
            house_price=params["house_price"],
            down_payment=params["down_payment"],
            loan_rate=params["loan_rate"],
            loan_years=params["loan_years"],
            appreciation_rate=params["appreciation_rate"],
            annual_cost=params["annual_cost"]
        )
        return simulator.simulate(params["simulation_years"])
        
    elif investment_type == InvestmentType.ETF_REGULAR:
        simulator = ETFRegularInvestment(
            initial_amount=params["initial_amount"],
            monthly_amount=params["monthly_amount"],
            annual_return=params["annual_return"],
            years=params["years"]
        )
        return simulator.simulate()
        
    elif investment_type == InvestmentType.STOCK:
        simulator = StockInvestment(
            monthly_amount=params["monthly_amount"],
            expected_return=params["expected_return"],
            volatility=params["volatility"],
            years=params["years"]
        )
        return simulator.monte_carlo_simulation(params.get("simulations", 1000))
        
    elif investment_type == InvestmentType.MUTUAL_FUND:
        simulator = MutualFundInvestment(
            initial_amount=params["initial_amount"],
            annual_return=params["annual_return"],
            years=params["years"]
        )
        return simulator.simulate()
        
    elif investment_type == InvestmentType.BOND_DEPOSIT:
        simulator = BondDeposit(
            principal=params["principal"],
            interest_rate=params["interest_rate"],
            years=params["years"],
            is_compound=params.get("is_compound", True),
            inflation_rate=params.get("inflation_rate", 2.0)
        )
        return simulator.simulate()
        
    else:
        raise ValueError("Invalid investment type")

# =================================
# API Endpoints
# =================================

@app.get("/")
async def root():
    return {"message": "Investment Simulation API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/simulate")
async def simulate_investment(request: SimulationRequest):
    """
    統一的投資模擬端點
    """
    try:
        investment_type = request.investment_type
        params = request.parameters.model_dump()
        
        # 執行模擬
        result = run_simulation(investment_type, params)
        
        # 生成唯一 ID
        simulation_id = str(uuid.uuid4())
        
        # 儲存到資料庫（如果需要）
        if request.save_to_db:
            save_simulation_to_db(simulation_id, investment_type.value, params, result)
        
        return {
            "id": simulation_id,
            "investment_type": investment_type,
            "parameters": params,
            "result": result,
            "success": True,
            "saved_to_db": request.save_to_db
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")

# =================================
# New Database API Endpoints
# =================================

@app.get("/simulations", response_model=List[SimulationRecord])
async def get_all_simulations():
    """
    取得所有模擬記錄
    """
    try:
        simulations = get_all_simulations_from_db()
        return simulations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/simulations/{simulation_id}", response_model=SimulationRecord)
async def get_simulation(simulation_id: str):
    """
    取得特定模擬記錄
    """
    try:
        simulation = get_simulation_from_db(simulation_id)
        if not simulation:
            raise HTTPException(status_code=404, detail="Simulation not found")
        return simulation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.put("/simulations/{simulation_id}")
async def update_simulation(simulation_id: str, request: UpdateSimulationRequest):
    """
    更新模擬記錄
    """
    try:
        # 先檢查記錄是否存在
        existing_simulation = get_simulation_from_db(simulation_id)
        if not existing_simulation:
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        # 取得投資類型
        investment_type = InvestmentType(existing_simulation["investment_type"])
        
        # 使用新參數重新執行模擬
        new_params = request.parameters.model_dump()
        new_result = run_simulation(investment_type, new_params)
        
        # 更新資料庫
        success = update_simulation_in_db(simulation_id, new_params, new_result)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update simulation")
        
        return {
            "id": simulation_id,
            "investment_type": investment_type,
            "parameters": new_params,
            "result": new_result,
            "success": True,
            "updated": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update error: {str(e)}")

@app.delete("/simulations/{simulation_id}")
async def delete_simulation(simulation_id: str):
    """
    刪除模擬記錄
    """
    try:
        success = delete_simulation_from_db(simulation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        return {
            "id": simulation_id,
            "success": True,
            "deleted": True,
            "message": "Simulation deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete error: {str(e)}")

# =================================
# Individual endpoints for each investment type (from original code)
# =================================

@app.post("/simulate/real_estate")
async def simulate_real_estate(request: RealEstateRequest):
    """房地產投資模擬"""
    try:
        simulator = RealEstateSimulation(
            house_price=request.house_price,
            down_payment=request.down_payment,
            loan_rate=request.loan_rate,
            loan_years=request.loan_years,
            appreciation_rate=request.appreciation_rate,
            annual_cost=request.annual_cost
        )
        result = simulator.simulate(request.simulation_years)
        return {"result": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/simulate/etf_regular")
async def simulate_etf_regular(request: ETFRegularRequest):
    """ETF定期定額投資模擬"""
    try:
        simulator = ETFRegularInvestment(
            initial_amount=request.initial_amount,
            monthly_amount=request.monthly_amount,
            annual_return=request.annual_return,
            years=request.years
        )
        result = simulator.simulate()
        return {"result": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/simulate/stock")
async def simulate_stock(request: StockRequest):
    """股票投資模擬（Monte Carlo）"""
    try:
        simulator = StockInvestment(
            monthly_amount=request.monthly_amount,
            expected_return=request.expected_return,
            volatility=request.volatility,
            years=request.years
        )
        result = simulator.monte_carlo_simulation(request.simulations)
        return {"result": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/simulate/mutual_fund")
async def simulate_mutual_fund(request: MutualFundRequest):
    """基金投資模擬"""
    try:
        simulator = MutualFundInvestment(
            initial_amount=request.initial_amount,
            annual_return=request.annual_return,
            years=request.years
        )
        result = simulator.simulate()
        return {"result": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/simulate/bond_deposit")
async def simulate_bond_deposit(request: BondDepositRequest):
    """債券/定存投資模擬"""
    try:
        simulator = BondDeposit(
            principal=request.principal,
            interest_rate=request.interest_rate,
            years=request.years,
            is_compound=request.is_compound,
            inflation_rate=request.inflation_rate
        )
        result = simulator.simulate()
        return {"result": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =================================
# Run the application
# =================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)