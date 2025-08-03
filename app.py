from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# 導入路由
from routes import router

# 初始化資料庫
from database.models import initialize_database

# 使用新的 lifespan 事件處理器替代已棄用的 on_event
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 啟動時執行
    try:
        db_config = initialize_database()
        print("✅ 資料庫初始化完成")
    except Exception as e:
        print(f"❌ 資料庫初始化失敗: {e}")
    
    yield
    
    # 關閉時執行（如果需要清理資源）
    print("🔄 應用程式正在關閉...")

# 建立 FastAPI 應用程式
app = FastAPI(
    title="Investment Simulation API", 
    version="1.0.0",
    description="投資模擬計算 API - 支援房地產、ETF、股票、債券/定存四種投資類型",
    lifespan=lifespan
)

# 設定 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://baedea.github.io",
        "https://brainfin-flask-api-project-production.up.railway.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8001",  # 新增端口
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊路由
app.include_router(router, prefix="/api/v1", tags=["投資計算"])

# 基本路由
@app.get("/")
async def root():
    return {
        "message": "Investment Simulation API", 
        "version": "1.0.0",
        "supported_investments": [
            "real_estate", "etf_regular", "stock", "bond_deposit"
        ],
        "endpoints": {
            "統一計算": "/api/v1/calculate",
            "房地產": "/api/v1/real-estate", 
            "ETF定投": "/api/v1/etf-regular",
            "股票": "/api/v1/stock",
            "債券定存": "/api/v1/bond-deposit",
            "歷史記錄": "/api/v1/history"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected"}

# 啟動應用程式
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app", 
        host="0.0.0.0", 
        port=8001,  # 改用端口 8001
        reload=True,  # 開發模式
        log_level="info"
    )