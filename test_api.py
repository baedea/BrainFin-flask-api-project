import pytest
import httpx
from fastapi.testclient import TestClient
from app import app, init_database
import json
import sqlite3
import os

# 測試用的資料庫路徑
TEST_DATABASE_PATH = "test_investment_simulations.db"

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_test_database():
    """設定測試資料庫"""
    # 使用測試資料庫
    import app
    app.DATABASE_PATH = TEST_DATABASE_PATH
    
    # 初始化測試資料庫
    init_database()
    
    yield
    
    # 清理測試資料庫
    if os.path.exists(TEST_DATABASE_PATH):
        os.remove(TEST_DATABASE_PATH)

class TestInvestmentAPI:
    """投資 API 測試類"""
    
    def test_root_endpoint(self):
        """測試根端點"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["message"] == "Investment Simulation API"
    
    def test_health_check(self):
        """測試健康檢查"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_etf_simulation(self):
        """測試 ETF 模擬"""
        data = {
            "investment_type": "etf_regular",
            "parameters": {
                "initial_amount": 100000,
                "monthly_amount": 10000,
                "annual_return": 8,
                "years": 10
            },
            "save_to_db": True
        }
        
        response = client.post("/simulate", json=data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["success"] == True
        assert "id" in result
        assert result["investment_type"] == "etf_regular"
        assert "result" in result
        
        # 檢查結果數據
        sim_result = result["result"]
        assert "final_value" in sim_result
        assert "total_investment" in sim_result
        assert "profit" in sim_result
        assert sim_result["final_value"] > 0
    
    def test_real_estate_simulation(self):
        """測試房地產模擬"""
        data = {
            "investment_type": "real_estate",
            "parameters": {
                "house_price": 10000000,
                "down_payment": 2000000,
                "loan_rate": 2.5,
                "loan_years": 20,
                "appreciation_rate": 3,
                "annual_cost": 50000,
                "simulation_years": 10
            },
            "save_to_db": True
        }
        
        response = client.post("/simulate", json=data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["success"] == True
        assert "monthly_payment" in result["result"]
    
    def test_stock_simulation(self):
        """測試股票模擬"""
        data = {
            "investment_type": "stock",
            "parameters": {
                "monthly_amount": 50000,
                "expected_return": 10,
                "volatility": 20,
                "years": 5,
                "simulations": 100
            },
            "save_to_db": True
        }
        
        response = client.post("/simulate", json=data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["success"] == True
        assert "mean" in result["result"]
        assert "percentile_5" in result["result"]
        assert "percentile_95" in result["result"]
    
    def test_get_all_simulations(self):
        """測試取得所有模擬記錄"""
        # 先創建幾個模擬記錄
        for i in range(3):
            data = {
                "investment_type": "etf_regular",
                "parameters": {
                    "initial_amount": 100000 + i * 10000,
                    "monthly_amount": 10000,
                    "annual_return": 8,
                    "years": 10
                },
                "save_to_db": True
            }
            client.post("/simulate", json=data)
        
        response = client.get("/simulations")
        assert response.status_code == 200
        
        simulations = response.json()
        assert len(simulations) >= 3
        
        # 檢查記錄結構
        for sim in simulations:
            assert "id" in sim
            assert "investment_type" in sim
            assert "parameters" in sim
            assert "result" in sim
            assert "created_at" in sim
    
    def test_get_specific_simulation(self):
        """測試取得特定模擬記錄"""
        # 先創建一個模擬記錄
        data = {
            "investment_type": "mutual_fund",
            "parameters": {
                "initial_amount": 500000,
                "annual_return": 6,
                "years": 15
            },
            "save_to_db": True
        }
        
        create_response = client.post("/simulate", json=data)
        simulation_id = create_response.json()["id"]
        
        # 取得該記錄
        response = client.get(f"/simulations/{simulation_id}")
        assert response.status_code == 200
        
        simulation = response.json()
        assert simulation["id"] == simulation_id
        assert simulation["investment_type"] == "mutual_fund"
    
    def test_update_simulation(self):
        """測試更新模擬記錄"""
        # 先創建一個模擬記錄
        data = {
            "investment_type": "bond_deposit",
            "parameters": {
                "principal": 1000000,
                "interest_rate": 3,
                "years": 5,
                "is_compound": True,
                "inflation_rate": 2
            },
            "save_to_db": True
        }
        
        create_response = client.post("/simulate", json=data)
        simulation_id = create_response.json()["id"]
        
        # 更新參數
        update_data = {
            "parameters": {
                "principal": 1500000,
                "interest_rate": 4,
                "years": 8,
                "is_compound": True,
                "inflation_rate": 2.5
            }
        }
        
        response = client.put(f"/simulations/{simulation_id}", json=update_data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["success"] == True
        assert result["updated"] == True
        assert result["parameters"]["principal"] == 1500000
    
    def test_delete_simulation(self):
        """測試刪除模擬記錄"""
        # 先創建一個模擬記錄
        data = {
            "investment_type": "etf_regular",
            "parameters": {
                "initial_amount": 200000,
                "monthly_amount": 15000,
                "annual_return": 7,
                "years": 12
            },
            "save_to_db": True
        }
        
        create_response = client.post("/simulate", json=data)
        simulation_id = create_response.json()["id"]
        
        # 刪除記錄
        response = client.delete(f"/simulations/{simulation_id}")
        assert response.status_code == 200
        
        result = response.json()
        assert result["success"] == True
        assert result["deleted"] == True
        
        # 確認記錄已被刪除
        get_response = client.get(f"/simulations/{simulation_id}")
        assert get_response.status_code == 404
    
    def test_invalid_simulation_type(self):
        """測試無效的投資類型"""
        data = {
            "investment_type": "invalid_type",
            "parameters": {
                "initial_amount": 100000,
                "annual_return": 8,
                "years": 10
            }
        }
        
        response = client.post("/simulate", json=data)
        assert response.status_code == 422  # Validation error
    
    def test_missing_parameters(self):
        """測試缺少必要參數"""
        data = {
            "investment_type": "etf_regular",
            "parameters": {
                "initial_amount": 100000
                # 缺少其他必要參數
            }
        }
        
        response = client.post("/simulate", json=data)
        assert response.status_code == 422  # Validation error

if __name__ == "__main__":
    pytest.main([__file__, "-v"])