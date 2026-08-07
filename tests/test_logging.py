import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.system.models import APIRequestLog

client = TestClient(app)

def test_logging_middleware():
    print("Testing Logging Middleware...")
    
    db = SessionLocal()
    initial_count = db.query(APIRequestLog).count()
    
    # Request to a non-skipped path
    response = client.get("/")
    print(f"GET / -> Status Code: {response.status_code}")
    
    import time
    time.sleep(1) # wait for async logging task to finish
    
    final_count = db.query(APIRequestLog).count()
    
    if final_count > initial_count:
        print("✅ SUCCESS: Logging middleware correctly saved a request to the database!")
        log = db.query(APIRequestLog).order_by(APIRequestLog.timestamp.desc()).first()
        print(f"Latest Log -> Path: {log.path}, Method: {log.method}, Status: {log.status_code}, Latency: {log.latency_ms}ms")
    else:
        print("❌ FAILED: No log was saved to the database.")
        
    db.close()

if __name__ == "__main__":
    test_logging_middleware()
