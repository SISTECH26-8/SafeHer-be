from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.api.dependencies import get_db
from app.system import services
from app.system.models import APIRequestLog, MLPredictionLog
import io
import csv
import json
from datetime import datetime

router = APIRouter(tags=["System"])

@router.get("/monitoring", response_class=HTMLResponse)
def get_monitoring_dashboard(db: Session = Depends(get_db)):
    """
    Menampilkan dashboard monitoring MLOps sederhana dalam format HTML.
    """
    metrics = services.get_monitoring_metrics(db)
    
    # Extract data for charts
    model_labels = list(metrics['model_usage'].keys())
    model_data = list(metrics['model_usage'].values())
    
    # We will generate a rich dark theme similar to Grafana
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SafeHer - MLOps Monitoring Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            :root {{
                --bg-main: #000000;
                --bg-card: #0f0f0f;
                --text-main: #d8d9da;
                --text-muted: #8e8e8e;
                --accent-blue: #FF65A0;
                --accent-green: #EA71F7;
                --accent-red: #FFCCE9;
                --border-color: #2c3235;
            }}
            body {{
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                background-color: var(--bg-main);
                color: var(--text-main);
                margin: 0;
                padding: 0;
            }}
            .topbar {{
                background-color: var(--bg-card);
                border-bottom: 1px solid var(--border-color);
                padding: 15px 30px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .topbar h1 {{
                margin: 0;
                font-size: 1.4rem;
                font-weight: 600;
                color: #fff;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            .topbar h1::before {{
                content: '';
                display: inline-block;
                width: 12px;
                height: 12px;
                background-color: var(--accent-blue);
                border-radius: 50%;
                box-shadow: 0 0 10px var(--accent-blue);
            }}
            .actions {{
                display: flex;
                gap: 15px;
            }}
            .btn {{
                background-color: var(--bg-main);
                color: var(--text-main);
                border: 1px solid var(--border-color);
                padding: 8px 16px;
                border-radius: 4px;
                text-decoration: none;
                font-size: 0.9rem;
                cursor: pointer;
                transition: all 0.2s ease;
                display: flex;
                align-items: center;
                gap: 8px;
            }}
            .btn:hover {{
                background-color: #22252b;
                border-color: #444a4f;
                color: #fff;
            }}
            .container {{
                padding: 30px;
                max-width: 1400px;
                margin: 0 auto;
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
                gap: 20px;
                margin-bottom: 20px;
            }}
            .stat-card {{
                background-color: var(--bg-card);
                border: 1px solid var(--border-color);
                border-radius: 4px;
                padding: 20px;
                position: relative;
                overflow: hidden;
            }}
            .stat-card::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 3px;
                background-color: var(--accent-blue);
            }}
            .stat-card.green::before {{ background-color: var(--accent-green); }}
            .stat-card.red::before {{ background-color: var(--accent-red); }}
            
            .stat-title {{
                font-size: 0.85rem;
                text-transform: uppercase;
                color: var(--text-muted);
                letter-spacing: 0.5px;
                margin-bottom: 10px;
            }}
            .stat-value {{
                font-size: 2.2rem;
                font-weight: bold;
                color: #fff;
            }}
            .stat-desc {{
                font-size: 0.8rem;
                color: var(--text-muted);
                margin-top: 5px;
            }}
            .charts-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
                gap: 20px;
            }}
            .chart-card {{
                background-color: var(--bg-card);
                border: 1px solid var(--border-color);
                border-radius: 4px;
                padding: 20px;
            }}
            .chart-title {{
                font-size: 1rem;
                color: #fff;
                margin-top: 0;
                margin-bottom: 20px;
                padding-bottom: 15px;
                border-bottom: 1px solid var(--border-color);
            }}
            .canvas-container {{
                position: relative;
                height: 250px;
                width: 100%;
            }}
        </style>
    </head>
    <body>
        <div class="topbar">
            <h1>SafeHer Monitoring</h1>
            <div class="actions">
                <a href="/api/v1/system/export-mlops" class="btn" target="_blank">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                    Download FP Output (JSON) - Prediction History
                </a>
                <a href="/api/v1/system/export-api-logs" class="btn" target="_blank">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                    Download API Logs (CSV)
                </a>
            </div>
        </div>

        <div class="container">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-title">Total Predictions</div>
                    <div class="stat-value">{metrics['prediction_distribution']['total_predictions']}</div>
                    <div class="stat-desc">Lifetime model inferences</div>
                </div>
                <div class="stat-card green">
                    <div class="stat-title">Avg Prediction Latency</div>
                    <div class="stat-value">{metrics['latency']['average_prediction_latency_ms']:.2f} <span style="font-size:1rem;color:#8e8e8e">ms</span></div>
                    <div class="stat-desc">Time taken by ML model</div>
                </div>
                <div class="stat-card red">
                    <div class="stat-title">Average Risk Score</div>
                    <div class="stat-value">{metrics['prediction_distribution']['average_risk_score']:.2f}</div>
                    <div class="stat-desc">Risk scale (0 - 100)</div>
                </div>
                <div class="stat-card">
                    <div class="stat-title">Last Prediction</div>
                    <div class="stat-value" style="font-size:1.2rem; margin-top: 15px;">{metrics['data_freshness']['latest_prediction_timestamp'] or "N/A"}</div>
                    <div class="stat-desc">Most recent inference activity</div>
                </div>
            </div>

            <div class="charts-grid">
                <div class="chart-card">
                    <h3 class="chart-title">Model Version Usage Distribution</h3>
                    <div class="canvas-container">
                        <canvas id="modelUsageChart"></canvas>
                    </div>
                </div>
                <div class="chart-card">
                    <h3 class="chart-title">Latency Comparison (API vs Model)</h3>
                    <div class="canvas-container">
                        <canvas id="latencyChart"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <script>
            // Chart.js global config for Dark Theme
            Chart.defaults.color = '#8e8e8e';
            Chart.defaults.borderColor = '#2c3235';

            // Model Usage Chart
            const modelUsageCtx = document.getElementById('modelUsageChart').getContext('2d');
            new Chart(modelUsageCtx, {{
                type: 'doughnut',
                data: {{
                    labels: {json.dumps(model_labels)},
                    datasets: [{{
                        data: {json.dumps(model_data)},
                        backgroundColor: ['#FF65A0', '#EA71F7', '#FFCCE9', '#EBD3ED'],
                        borderWidth: 0,
                        hoverOffset: 4
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{ position: 'right' }}
                    }},
                    cutout: '70%'
                }}
            }});

            // Latency Chart
            const latencyCtx = document.getElementById('latencyChart').getContext('2d');
            new Chart(latencyCtx, {{
                type: 'bar',
                data: {{
                    labels: ['Average Latency (ms)'],
                    datasets: [
                        {{
                            label: 'Model Prediction Latency',
                            data: [{metrics['latency']['average_prediction_latency_ms']}],
                            backgroundColor: '#FF65A0',
                            borderRadius: 4
                        }},
                        {{
                            label: 'Overall API Latency',
                            data: [{metrics['latency']['average_api_latency_ms']}],
                            backgroundColor: '#EA71F7',
                            borderRadius: 4
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        y: {{ beginAtZero: true, grid: {{ color: '#2c3235' }} }},
                        x: {{ grid: {{ display: false }} }}
                    }},
                    plugins: {{
                        legend: {{ position: 'top' }}
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content, status_code=200)

@router.get("/api/v1/system/export-api-logs")
def export_api_logs(db: Session = Depends(get_db)):
    """Endpoint untuk mendownload API Request Logs sebagai CSV."""
    logs = db.query(APIRequestLog).order_by(APIRequestLog.timestamp.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Request ID", "Created At", "Method", 
        "Path", "Status Code", "Latency (ms)", "Message", 
        "Query Params", "User ID"
    ])
    
    for log in logs:
        writer.writerow([
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
        
    output.seek(0)
    filename = f"API_Logs_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/api/v1/system/export-mlops")
def export_mlops_output(db: Session = Depends(get_db)):
    """Endpoint untuk mendownload MLOps Prediction output JSON."""
    total_preds = db.query(func.count(MLPredictionLog.request_id)).scalar() or 0
    latest_version_usage = db.query(func.count(MLPredictionLog.request_id))\
                             .filter(MLPredictionLog.model_version == "v1.0.0").scalar() or 0
    avg_score = db.query(func.avg(MLPredictionLog.predicted_score)).scalar() or 0.0
    avg_pred_latency = db.query(func.avg(MLPredictionLog.latency_ms)).scalar() or 0.0
    
    logs = db.query(MLPredictionLog).order_by(MLPredictionLog.timestamp.desc()).limit(100).all()
    history = []
    for log in logs:
        history.append({
            "request_id": str(log.request_id),
            "timestamp": log.timestamp.isoformat(),
            "model_version": log.model_version,
            "source": log.source,
            "inputs": log.inputs,
            "predicted_score": log.predicted_score,
            "latency_ms": log.latency_ms
        })

    output_data = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat(),
            "project": "SISTECH 2026 - MLOps SafeHer"
        },
        "metrics": {
            "total_predictions": total_preds,
            "latest_model_usage_count": latest_version_usage,
            "average_risk_score": round(avg_score, 4),
            "average_prediction_latency_ms": round(avg_pred_latency, 4)
        },
        "prediction_history": history
    }
    
    filename = f"ML_Predictions_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    json_str = json.dumps(output_data, indent=4)
    
    return Response(
        content=json_str,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
