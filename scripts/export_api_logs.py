import csv
import os
import sys
from datetime import datetime
import json

# Setup path so it can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import SessionLocal
from app.system.models import APIRequestLog

def export_api_logs_to_csv():
    db = SessionLocal()
    try:
        # Get all logs ordered by newest first
        logs = db.query(APIRequestLog).order_by(APIRequestLog.timestamp.desc()).all()
        
        filename = f"API_Logs_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(filename, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Write Header
            writer.writerow([
                "Request ID", 
                "Created At", 
                "Method", 
                "Path", 
                "Status Code", 
                "Latency (ms)", 
                "Message", 
                "Query Params",
                "User ID"
            ])
            
            # Write Data Rows
            for log in logs:
                writer.writerow([
                    # log.id doesn't exist, remove it, wait APIRequestLog only has request_id
                    log.request_id,
                    log.timestamp.isoformat(),
                    log.method,
                    log.path,
                    log.status_code,
                    f"{log.latency_ms:.2f}",
                    log.message,
                    json.dumps(log.query_params) if log.query_params else "",
                    log.user_id if log.user_id else "Guest"
                ])
                
        print(f"✅ Successfully exported {len(logs)} API logs to {filename}")
        
    except Exception as e:
        print(f"❌ Error exporting API logs: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    export_api_logs_to_csv()
