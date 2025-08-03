# routes.py
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
import uuid
from datetime import datetime
from typing import List, Optional

# 導入你的計算函數
from calculators.bond_deposit import bond_deposit
from calculators.etf_regular import ETFRegularInvestment
from calculators.real_estate import house_investment_analysis
from calculators.stock import stock_investment_simulation

# 導入資料庫相關
from database.models import DatabaseConfig, SimulationRepository, HistoricalDataRepository

# 導入 Pydantic 模型
from calculators.models import (
    InvestmentType, SimulationRequest, UpdateSimulationRequest,
    RealEstateRequest, ETFRegularRequest, StockRequest, BondDepositRequest,
    SimulationRecord
)

# 創建路由器
router = APIRouter()

# 初始化資料庫配置
db_config = DatabaseConfig()

# 依賴注入：獲取資料庫會話
def get_db():
    db = db_config.get_session()
    try:
        yield db
    finally:
        db.close()

# =================================
# 投資計算 API 路由
# =================================

@router.post("/calculate", response_model=SimulationRecord)
async def calculate_investment(request: SimulationRequest, db: Session = Depends(get_db)):
    """
    統一投資計算端點
    支援4種投資類型：real_estate, etf_regular, stock, bond_deposit
    """
    try:
        # 生成唯一ID
        simulation_id = str(uuid.uuid4())
        
        # 根據投資類型調用對應的計算函數
        if request.investment_type == InvestmentType.REAL_ESTATE:
            params = request.parameters
            result = house_investment_analysis(
                house_price=params.house_price,
                down_payment=params.down_payment,
                loan_rate=params.loan_rate,
                loan_years=params.loan_years,
                appreciation_rate_a=params.appreciation_rate_a,
                appreciation_rate_b=params.appreciation_rate_b,
                annual_cost=params.annual_cost,
                simulation_years=params.simulation_years,
                scenario=params.scenario
            )
            
        elif request.investment_type == InvestmentType.ETF_REGULAR:
            params = request.parameters
            result = ETFRegularInvestment(
                initial_amount=params.initial_amount,
                monthly_amount=params.monthly_amount,
                dividend_yield=params.dividend_yield,
                price_growth=params.price_growth,
                years=params.years
            )
            
        elif request.investment_type == InvestmentType.STOCK:
            params = request.parameters
            result = stock_investment_simulation(
                initial_amount=params.initial_amount,
                monthly_amount=params.monthly_amount,
                expected_return=params.expected_return,
                volatility=params.volatility,
                years=params.years,
                simulations=params.simulations
            )
            
        elif request.investment_type == InvestmentType.BOND_DEPOSIT:
            params = request.parameters
            result = bond_deposit(
                principal=params.principal,
                interest_rate=params.interest_rate,
                years=params.years,
                is_compound=params.is_compound,
                inflation_rate=params.inflation_rate
            )
            
        else:
            raise HTTPException(status_code=400, detail="不支援的投資類型")
        
        # 如果需要，儲存到資料庫
        if request.save_to_db:
            repo = SimulationRepository(db)
            record = repo.save_simulation(
                simulation_id=simulation_id,
                investment_type=request.investment_type.value,
                parameters=request.parameters.dict(),
                result=result
            )
            
            return SimulationRecord(
                id=record.id,
                investment_type=record.investment_type,
                parameters=record.parameters,
                result=record.result,
                created_at=record.created_at.isoformat(),
                updated_at=record.updated_at.isoformat()
            )
        else:
            # 不儲存到資料庫，直接回傳結果
            return SimulationRecord(
                id=simulation_id,
                investment_type=request.investment_type.value,
                parameters=request.parameters.dict(),
                result=result,
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat()
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"計算失敗: {str(e)}")

# =================================
# 個別投資類型的專用端點 (向後相容)
# =================================

@router.post("/real-estate")
async def calculate_real_estate(request: RealEstateRequest, db: Session = Depends(get_db)):
    """房地產投資計算"""
    simulation_request = SimulationRequest(
        investment_type=InvestmentType.REAL_ESTATE,
        parameters=request
    )
    return await calculate_investment(simulation_request, db)

@router.post("/etf-regular")
async def calculate_etf_regular(request: ETFRegularRequest, db: Session = Depends(get_db)):
    """ETF定期定額投資計算"""
    simulation_request = SimulationRequest(
        investment_type=InvestmentType.ETF_REGULAR,
        parameters=request
    )
    return await calculate_investment(simulation_request, db)

@router.post("/stock")
async def calculate_stock(request: StockRequest, db: Session = Depends(get_db)):
    """股票投資蒙地卡羅模擬"""
    simulation_request = SimulationRequest(
        investment_type=InvestmentType.STOCK,
        parameters=request
    )
    return await calculate_investment(simulation_request, db)

@router.post("/bond-deposit")
async def calculate_bond_deposit(request: BondDepositRequest, db: Session = Depends(get_db)):
    """債券/定存投資計算"""
    simulation_request = SimulationRequest(
        investment_type=InvestmentType.BOND_DEPOSIT,
        parameters=request
    )
    return await calculate_investment(simulation_request, db)

# =================================
# 資料管理 API 路由
# =================================

@router.get("/simulation/{simulation_id}", response_model=SimulationRecord)
async def get_simulation(simulation_id: str, db: Session = Depends(get_db)):
    """根據ID獲取投資模擬記錄"""
    repo = SimulationRepository(db)
    record = repo.get_simulation(simulation_id)
    
    if not record:
        raise HTTPException(status_code=404, detail="找不到指定的模擬記錄")
    
    return SimulationRecord(
        id=record.id,
        investment_type=record.investment_type,
        parameters=record.parameters,
        result=record.result,
        created_at=record.created_at.isoformat(),
        updated_at=record.updated_at.isoformat()
    )

@router.get("/history", response_model=List[SimulationRecord])
async def get_user_history(
    user_session: Optional[str] = Query(None, description="用戶會話ID"),
    limit: int = Query(50, description="回傳記錄數量限制"),
    investment_type: Optional[InvestmentType] = Query(None, description="篩選投資類型"),
    db: Session = Depends(get_db)
):
    """獲取用戶投資計算歷史記錄"""
    repo = SimulationRepository(db)
    records = repo.get_user_history(user_session, limit)
    
    # 如果指定投資類型，進行篩選
    if investment_type:
        records = [r for r in records if r.investment_type == investment_type.value]
    
    return [
        SimulationRecord(
            id=record.id,
            investment_type=record.investment_type,
            parameters=record.parameters,
            result=record.result,
            created_at=record.created_at.isoformat(),
            updated_at=record.updated_at.isoformat()
        )
        for record in records
    ]