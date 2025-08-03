from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union
from enum import Enum

# =================================
# Enums
# =================================

class InvestmentType(str, Enum):
    REAL_ESTATE = "real_estate"
    ETF_REGULAR = "etf_regular"
    STOCK = "stock"
    MUTUAL_FUND = "mutual_fund"
    BOND_DEPOSIT = "bond_deposit"

# =================================
# Request Models (根據你的計算函數調整)
# =================================

class RealEstateRequest(BaseModel):
    house_price: float = Field(..., description="房屋價格 (TWD)")
    down_payment: float = Field(..., description="頭期款 (TWD)")
    loan_rate: float = Field(..., description="貸款利率 (%)")
    loan_years: int = Field(..., description="貸款年限")
    appreciation_rate_a: float = Field(..., description="情境A預期房價總漲幅 (%)")
    appreciation_rate_b: float = Field(..., description="情境B預期房價總漲幅 (%)")
    annual_cost: float = Field(..., description="年度持有成本 (TWD)")
    simulation_years: int = Field(..., description="模擬年數")
    scenario: str = Field("A", description="情境選擇 (A或B)")

class ETFRegularRequest(BaseModel):
    initial_amount: float = Field(..., description="初始投入金額 (TWD)")
    monthly_amount: float = Field(..., description="每月定期投入 (TWD)")
    dividend_yield: float = Field(..., description="年配息率 (%)")
    price_growth: float = Field(..., description="年價格成長率 (%)")
    years: int = Field(..., description="投資年限")

class StockRequest(BaseModel):
    initial_amount: float = Field(..., description="初始投入金額 (TWD)")
    monthly_amount: float = Field(..., description="每年額外投入金額 (TWD)")
    expected_return: float = Field(..., description="預期年報酬率 (%)")
    volatility: float = Field(..., description="波動率 (%)")
    years: int = Field(..., description="投資年限")
    simulations: int = Field(10000, description="Monte Carlo 模擬次數")

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

# =================================
# Unified Request Models
# =================================

class SimulationRequest(BaseModel):
    investment_type: InvestmentType
    parameters: Union[RealEstateRequest, ETFRegularRequest, StockRequest, MutualFundRequest, BondDepositRequest]
    save_to_db: bool = Field(True, description="是否儲存到資料庫")

class UpdateSimulationRequest(BaseModel):
    parameters: Union[RealEstateRequest, ETFRegularRequest, StockRequest, MutualFundRequest, BondDepositRequest]

# =================================
# Response Models (回傳資料)
# =================================

class SimulationRecord(BaseModel):
    id: str
    investment_type: str
    parameters: Dict
    result: Dict
    created_at: str
    updated_at: str