import httpx

response = httpx.post("http://localhost:8000/simulate", json={
    "investment_type": "etf_regular",
    "parameters": {
        "initial_amount": 100000,
        "monthly_amount": 10000,
        "annual_return": 8,
        "years": 10
    },
    "save_to_db": True
})

print(response.status_code)
print(response.json())