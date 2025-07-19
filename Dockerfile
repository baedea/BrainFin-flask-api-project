FROM python:3.11-slim

WORKDIR /app

# 複製依賴文件
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式代碼
COPY . .

# 創建資料庫目錄
RUN mkdir -p /app/data

# 暴露端口
EXPOSE 8000

# 啟動應用程式
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]