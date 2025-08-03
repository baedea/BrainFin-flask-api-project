from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from datetime import datetime
from contextlib import contextmanager
import json
import uuid

class Base(DeclarativeBase):
    pass

# =================================
# 歷史數據表 (Historical Data Tables)
# =================================

class StockHistoricalData(Base):
    """股票歷史數據表"""
    __tablename__ = 'stock_historical_data'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)  # 股票代碼
    date = Column(DateTime, nullable=False, index=True)      # 日期
    close_price = Column(Float, nullable=False)             # 收盤價
    return_rate = Column(Float)                             # 日報酬率
    annual_return = Column(Float)                           # 年化報酬率
    volatility = Column(Float)                              # 波動率
    dividend_yield = Column(Float)                          # 配息率
    created_at = Column(DateTime, default=datetime.utcnow)

class RealEstateData(Base):
    """房地產歷史數據表"""
    __tablename__ = 'real_estate_data'
    
    id = Column(Integer, primary_key=True)
    region = Column(String(50), nullable=False, index=True)  # 地區
    property_type = Column(String(30), nullable=False)       # 房屋類型
    date = Column(DateTime, nullable=False, index=True)      # 日期
    avg_price_per_ping = Column(Float, nullable=False)       # 每坪均價
    price_index = Column(Float)                             # 價格指數
    yoy_change = Column(Float)                              # 年增率
    transaction_volume = Column(Integer)                     # 交易量
    created_at = Column(DateTime, default=datetime.utcnow)

class DepositRates(Base):
    """定存利率歷史數據表"""
    __tablename__ = 'deposit_rates'
    
    id = Column(Integer, primary_key=True)
    bank_name = Column(String(50), nullable=False, index=True)  # 銀行名稱
    deposit_type = Column(String(30), nullable=False)           # 定存類型 (1年期/2年期等)
    date = Column(DateTime, nullable=False, index=True)         # 日期
    interest_rate = Column(Float, nullable=False)               # 利率 (%)
    min_amount = Column(Float)                                  # 最低金額
    created_at = Column(DateTime, default=datetime.utcnow)

# =================================
# 計算記錄表 (Simulation Records)
# =================================

class SimulationRecord(Base):
    """用戶投資模擬記錄表"""
    __tablename__ = 'simulation_records'
    
    id = Column(String(36), primary_key=True)  # UUID
    investment_type = Column(String(30), nullable=False, index=True)  # 投資類型
    parameters = Column(JSON, nullable=False)                         # 輸入參數 (JSON格式)
    result = Column(JSON, nullable=False)                            # 計算結果 (JSON格式)
    user_session = Column(String(100), index=True)                   # 用戶會話ID (可選)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserFavorites(Base):
    """用戶收藏的計算記錄"""
    __tablename__ = 'user_favorites'
    
    id = Column(Integer, primary_key=True)
    simulation_id = Column(String(36), nullable=False, index=True)
    user_session = Column(String(100), nullable=False, index=True)
    name = Column(String(100))                                       # 用戶自定義名稱
    created_at = Column(DateTime, default=datetime.utcnow)

# =================================
# 市場數據快取表 (Market Data Cache)
# =================================

class MarketDataCache(Base):
    """市場數據快取表 - 用於快速查詢最新數據"""
    __tablename__ = 'market_data_cache'
    
    id = Column(Integer, primary_key=True)
    data_type = Column(String(30), nullable=False, index=True)  # 數據類型
    symbol_or_region = Column(String(50), nullable=False, index=True)  # 標的或地區
    latest_value = Column(Float)                                # 最新數值
    latest_date = Column(DateTime)                              # 最新日期
    extra_data = Column(JSON)                                   # 其他元數據 (改名避免衝突)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# =================================
# Database Configuration & Setup
# =================================

class DatabaseConfig:
    """資料庫配置類"""
    
    def __init__(self, database_url="sqlite:///investment_api.db"):
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        """創建所有資料表"""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """獲取資料庫會話"""
        return self.SessionLocal()
    
    @contextmanager
    def get_session_context(self):
        """獲取資料庫會話 (Context Manager)"""
        session = self.SessionLocal()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

# =================================
# Data Access Layer (數據存取層)
# =================================

class SimulationRepository:
    """模擬記錄數據存取類"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def save_simulation(self, simulation_id: str, investment_type: str, 
                       parameters: dict, result: dict, user_session: str = None):
        """保存模擬記錄"""
        try:
            record = SimulationRecord(
                id=simulation_id,
                investment_type=investment_type,
                parameters=parameters,
                result=result,
                user_session=user_session
            )
            self.db.add(record)
            self.db.commit()
            return record
        except Exception as e:
            self.db.rollback()
            raise e
    
    def save_or_update_simulation(self, simulation_id: str, investment_type: str, 
                                 parameters: dict, result: dict, user_session: str = None):
        """保存或更新模擬記錄 (避免重複 ID 錯誤)"""
        try:
            # 先嘗試更新現有記錄
            existing_record = self.get_simulation(simulation_id)
            if existing_record:
                existing_record.parameters = parameters
                existing_record.result = result
                existing_record.updated_at = datetime.utcnow()
                if user_session:
                    existing_record.user_session = user_session
                self.db.commit()
                return existing_record
            else:
                # 如果不存在則創建新記錄
                return self.save_simulation(simulation_id, investment_type, parameters, result, user_session)
        except Exception as e:
            self.db.rollback()
            raise e
    
    def get_simulation(self, simulation_id: str):
        """根據ID獲取模擬記錄"""
        return self.db.query(SimulationRecord).filter(
            SimulationRecord.id == simulation_id
        ).first()
    
    def update_simulation(self, simulation_id: str, parameters: dict, result: dict):
        """更新模擬記錄"""
        try:
            record = self.get_simulation(simulation_id)
            if record:
                record.parameters = parameters
                record.result = result
                record.updated_at = datetime.utcnow()
                self.db.commit()
            return record
        except Exception as e:
            self.db.rollback()
            raise e
    
    def get_user_history(self, user_session: str, limit: int = 50):
        """獲取用戶歷史記錄"""
        return self.db.query(SimulationRecord).filter(
            SimulationRecord.user_session == user_session
        ).order_by(SimulationRecord.created_at.desc()).limit(limit).all()

class HistoricalDataRepository:
    """歷史數據存取類"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def get_stock_data(self, symbol: str, start_date=None, end_date=None):
        """獲取股票歷史數據"""
        query = self.db.query(StockHistoricalData).filter(
            StockHistoricalData.symbol == symbol
        )
        if start_date:
            query = query.filter(StockHistoricalData.date >= start_date)
        if end_date:
            query = query.filter(StockHistoricalData.date <= end_date)
        return query.order_by(StockHistoricalData.date).all()
    
    def get_latest_deposit_rates(self, bank_name=None):
        """獲取最新定存利率"""
        query = self.db.query(DepositRates)
        if bank_name:
            query = query.filter(DepositRates.bank_name == bank_name)
        return query.order_by(DepositRates.date.desc()).limit(10).all()
    
    def get_real_estate_trends(self, region: str, months: int = 12):
        """獲取房地產趨勢數據"""
        from datetime import datetime, timedelta
        start_date = datetime.now() - timedelta(days=months*30)
        
        return self.db.query(RealEstateData).filter(
            RealEstateData.region == region,
            RealEstateData.date >= start_date
        ).order_by(RealEstateData.date).all()

# =================================
# Data Migration & Seed Functions
# =================================

def migrate_json_to_db(db_config: DatabaseConfig):
    """將現有 JSON 數據遷移到資料庫"""
    import os
    from datetime import datetime, timedelta
    
    with db_config.get_session_context() as session:
        try:
            # 遷移股票數據
            if os.path.exists('data/stock_data.json'):
                with open('data/stock_data.json', 'r', encoding='utf-8') as f:
                    stock_data = json.load(f)
                
                for symbol, data in stock_data.items():
                    for record in data:
                        stock_record = StockHistoricalData(
                            symbol=symbol,
                            date=datetime.strptime(record['date'], '%Y-%m-%d'),
                            close_price=record.get('close_price', 0),
                            return_rate=record.get('return_rate'),
                            annual_return=record.get('annual_return'),
                            volatility=record.get('volatility'),
                            dividend_yield=record.get('dividend_yield')
                        )
                        session.add(stock_record)
            
            # 遷移房地產數據
            if os.path.exists('data/real_estate_data.json'):
                with open('data/real_estate_data.json', 'r', encoding='utf-8') as f:
                    re_data = json.load(f)
                
                for region, data in re_data.items():
                    for record in data:
                        re_record = RealEstateData(
                            region=region,
                            property_type=record.get('property_type', '住宅'),
                            date=datetime.strptime(record['date'], '%Y-%m-%d'),
                            avg_price_per_ping=record.get('avg_price_per_ping', 0),
                            price_index=record.get('price_index'),
                            yoy_change=record.get('yoy_change'),
                            transaction_volume=record.get('transaction_volume')
                        )
                        session.add(re_record)
            
            # 遷移定存利率數據
            if os.path.exists('data/deposit_rates.json'):
                with open('data/deposit_rates.json', 'r', encoding='utf-8') as f:
                    deposit_data = json.load(f)
                
                for bank, data in deposit_data.items():
                    for record in data:
                        deposit_record = DepositRates(
                            bank_name=bank,
                            deposit_type=record.get('deposit_type', '1年期'),
                            date=datetime.strptime(record['date'], '%Y-%m-%d'),
                            interest_rate=record.get('interest_rate', 0),
                            min_amount=record.get('min_amount', 10000)
                        )
                        session.add(deposit_record)
            
            session.commit()
            print("JSON 數據遷移完成!")
            
        except Exception as e:
            print(f"數據遷移失敗: {e}")
            raise

def seed_sample_data(db_config: DatabaseConfig):
    """插入範例數據"""
    from datetime import timedelta
    
    with db_config.get_session_context() as session:
        try:
            # 插入範例股票數據
            sample_stocks = ['0050', '0056', 'VTI', 'SPY']
            base_date = datetime(2020, 1, 1)
            
            for symbol in sample_stocks:
                for i in range(100):  # 100天的數據
                    date = base_date + timedelta(days=i)
                    stock_record = StockHistoricalData(
                        symbol=symbol,
                        date=date,
                        close_price=100 + (i * 0.1),
                        return_rate=0.05 + (i * 0.001),
                        annual_return=8.5,
                        volatility=15.2,
                        dividend_yield=3.5
                    )
                    session.add(stock_record)
            
            # 插入範例定存利率
            banks = ['台灣銀行', '中國信託', '國泰世華', '富邦銀行']
            for bank in banks:
                deposit_record = DepositRates(
                    bank_name=bank,
                    deposit_type='1年期',
                    date=datetime.now(),
                    interest_rate=1.35,
                    min_amount=10000
                )
                session.add(deposit_record)
            
            session.commit()
            print("範例數據插入完成!")
            
        except Exception as e:
            print(f"範例數據插入失敗: {e}")
            raise

# =================================
# Utility Functions
# =================================

def generate_unique_id(prefix: str = "") -> str:
    """生成唯一 ID"""
    unique_id = str(uuid.uuid4())
    return f"{prefix}{unique_id}" if prefix else unique_id

def generate_timestamp_id(prefix: str = "sim") -> str:
    """生成基於時間戳的 ID"""
    timestamp = int(datetime.now().timestamp() * 1000)  # 毫秒級時間戳
    return f"{prefix}-{timestamp}"

# =================================
# Usage Example & Setup
# =================================

def initialize_database():
    """初始化資料庫"""
    db_config = DatabaseConfig()
    db_config.create_tables()
    return db_config

# 使用範例
if __name__ == "__main__":
    # 初始化資料庫
    db_config = initialize_database()
    
    # 選擇性執行數據遷移或插入範例數據
    print("1. 遷移現有 JSON 數據")
    print("2. 插入範例數據") 
    print("3. 測試資料庫連接")
    
    choice = input("請選擇操作 (1-3): ")
    
    if choice == "1":
        migrate_json_to_db(db_config)
    elif choice == "2":
        seed_sample_data(db_config)
    elif choice == "3":
        # 測試資料庫連接 - 修正版本
        with db_config.get_session_context() as session:
            repo = SimulationRepository(session)
            
            # 測試參數
            test_params = {
                "house_price": 15000000,
                "down_payment": 3000000,
                "loan_rate": 2.1,
                "loan_years": 30
            }
            test_result = {
                "profit": 2500000,
                "roi": 15.5
            }
            
            # 方法1: 使用唯一 UUID
            unique_id = generate_unique_id("test-")
            record1 = repo.save_simulation(
                simulation_id=unique_id,
                investment_type="real_estate",
                parameters=test_params,
                result=test_result
            )
            print(f"已保存記錄 (UUID): {record1.id}")
            
            # 方法2: 使用時間戳 ID
            timestamp_id = generate_timestamp_id("real_estate")
            record2 = repo.save_simulation(
                simulation_id=timestamp_id,
                investment_type="real_estate",
                parameters=test_params,
                result=test_result
            )
            print(f"已保存記錄 (時間戳): {record2.id}")
            
            # 方法3: 測試 save_or_update 功能
            fixed_id = "test-fixed-id"
            record3 = repo.save_or_update_simulation(
                simulation_id=fixed_id,
                investment_type="real_estate",
                parameters=test_params,
                result=test_result
            )
            print(f"已保存記錄 (固定ID-第一次): {record3.id}")
            
            # 再次使用相同 ID (應該會更新而不是報錯)
            updated_result = {
                "profit": 3000000,
                "roi": 18.0
            }
            record4 = repo.save_or_update_simulation(
                simulation_id=fixed_id,
                investment_type="real_estate",
                parameters=test_params,
                result=updated_result
            )
            print(f"已更新記錄 (固定ID-第二次): {record4.id}, 新ROI: {record4.result['roi']}")
            
            print("資料庫連接測試完成!")
    else:
        print("無效的選擇")