"""
SQS monitoring and observability dashboard
Provides comprehensive monitoring for SQS queues and message processing
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, HTMLResponse, Response
from typing import Dict, Any, Optional, List
import time
import json
from datetime import datetime, timedelta

from app.services.sqs_service import sqs_service, QueueType
from app.core.logging import logger

router = APIRouter(prefix="/monitoring", tags=["SQS Monitoring"])

@router.get("/dashboard")
async def monitoring_dashboard():
    """
    HTML dashboard for SQS monitoring
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SQS Monitoring Dashboard</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 20px; }
            .metric-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .metric-title { font-size: 18px; font-weight: bold; margin-bottom: 10px; color: #2c3e50; }
            .metric-value { font-size: 24px; font-weight: bold; }
            .healthy { color: #27ae60; }
            .warning { color: #f39c12; }
            .error { color: #e74c3c; }
            .queue-status { margin-bottom: 20px; }
            .queue-item { background: white; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #3498db; }
            .refresh-btn { background: #3498db; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin-bottom: 20px; }
            .refresh-btn:hover { background: #2980b9; }
            table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background-color: #f8f9fa; font-weight: bold; }
            .timestamp { color: #666; font-size: 12px; }
        </style>
        <script>
            async function refreshData() {
                try {
                    const response = await fetch('/monitoring/summary');
                    const data = await response.json();
                    
                    document.getElementById('overall-status').textContent = data.overall_status;
                    document.getElementById('overall-status').className = `metric-value ${data.overall_status}`;
                    
                    document.getElementById('total-messages').textContent = data.total_messages_pending;
                    document.getElementById('active-queues').textContent = data.active_queues;
                    document.getElementById('workers-status').textContent = data.workers.status;
                    document.getElementById('workers-status').className = `metric-value ${data.workers.status === 'running' ? 'healthy' : 'error'}`;
                    
                    const queuesList = document.getElementById('queues-list');
                    queuesList.innerHTML = '';
                    
                    Object.entries(data.queues).forEach(([queueName, queueData]) => {
                        const queueDiv = document.createElement('div');
                        queueDiv.className = 'queue-item';
                        queueDiv.innerHTML = `
                            <strong>${queueName}</strong>
                            <div>Status: <span class="${queueData.status}">${queueData.status}</span></div>
                            <div>Messages: ${queueData.approximate_messages || 0}</div>
                            <div>In Flight: ${queueData.approximate_messages_not_visible || 0}</div>
                            <div>Delayed: ${queueData.approximate_messages_delayed || 0}</div>
                        `;
                        queuesList.appendChild(queueDiv);
                    });
                    
                    document.getElementById('last-update').textContent = new Date().toLocaleString();
                } catch (error) {
                    console.error('Failed to refresh data:', error);
                }
            }
            
            function startAutoRefresh() {
                refreshData();
                setInterval(refreshData, 30000); // Refresh every 30 seconds
            }
            
            window.onload = startAutoRefresh;
        </script>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>SQS Monitoring Dashboard</h1>
                <p>Real-time monitoring of WhatsApp message queues and processing workers</p>
            </div>
            
            <button class="refresh-btn" onclick="refreshData()">🔄 Refresh Now</button>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-title">Overall Status</div>
                    <div id="overall-status" class="metric-value">Loading...</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Total Messages Pending</div>
                    <div id="total-messages" class="metric-value">-</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Active Queues</div>
                    <div id="active-queues" class="metric-value">-</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Workers Status</div>
                    <div id="workers-status" class="metric-value">-</div>
                </div>
            </div>
            
            <div class="queue-status">
                <h2>Queue Details</h2>
                <div id="queues-list">
                    Loading queue information...
                </div>
            </div>
            
            <div style="background: white; padding: 20px; border-radius: 8px;">
                <h2>Quick Actions</h2>
                <p><a href="/monitoring/summary" target="_blank">📊 Raw JSON Summary</a></p>
                <p><a href="/health/sqs" target="_blank">❤️ SQS Health Check</a></p>
                <p><a href="/health/workers" target="_blank">⚙️ Workers Health Check</a></p>
                <p><a href="/messaging/queue/status" target="_blank">📈 Detailed Queue Status</a></p>
                <p><a href="/docs" target="_blank">📖 API Documentation</a></p>
                
                <div class="timestamp">
                    Last updated: <span id="last-update">Never</span>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)

@router.get("/summary")
async def monitoring_summary():
    """
    Get comprehensive monitoring summary
    """
    try:
        # Get SQS health
        sqs_health = await sqs_service.health_check()
        
        # Get queue details
        queue_details = {}
        total_messages = 0
        active_queues = 0
        
        for queue_type in QueueType:
            try:
                attributes = await sqs_service.get_queue_attributes(queue_type)
                if attributes:
                    queue_details[queue_type.value] = {
                        "status": "healthy",
                        "approximate_messages": int(attributes.get('ApproximateNumberOfMessages', 0)),
                        "approximate_messages_not_visible": int(attributes.get('ApproximateNumberOfMessagesNotVisible', 0)),
                        "approximate_messages_delayed": int(attributes.get('ApproximateNumberOfMessagesDelayed', 0)),
                        "last_modified": attributes.get('LastModifiedTimestamp', 'unknown')
                    }
                    total_messages += queue_details[queue_type.value]["approximate_messages"]
                    active_queues += 1
                else:
                    queue_details[queue_type.value] = {
                        "status": "unhealthy",
                        "error": "Cannot retrieve attributes"
                    }
            except Exception as e:
                queue_details[queue_type.value] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Get worker status
        worker_status = {"status": "unknown", "details": {}}
        try:
            from app.workers.message_processor import message_processor
            worker_stats = message_processor.get_stats()
            worker_status = {
                "status": "running" if worker_stats["running"] else "stopped",
                "details": worker_stats
            }
        except Exception as e:
            worker_status = {
                "status": "error",
                "error": str(e)
            }
        
        # Determine overall status
        overall_status = "healthy"
        if sqs_health["sqs_service"] != "healthy":
            overall_status = "degraded"
        if worker_status["status"] not in ["running", "stopped"]:
            overall_status = "error"
        if any(q.get("status") == "error" for q in queue_details.values()):
            overall_status = "degraded" if overall_status == "healthy" else "error"
        
        return {
            "overall_status": overall_status,
            "total_messages_pending": total_messages,
            "active_queues": active_queues,
            "sqs_service": sqs_health,
            "workers": worker_status,
            "queues": queue_details,
            "timestamp": int(time.time()),
            "formatted_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error generating monitoring summary: {e}")
        return JSONResponse(
            content={
                "overall_status": "error",
                "error": str(e),
                "timestamp": int(time.time())
            },
            status_code=500
        )

@router.get("/metrics")
async def get_metrics():
    """
    Get detailed metrics for monitoring systems (Prometheus format)
    """
    try:
        metrics = []
        
        # SQS metrics
        for queue_type in QueueType:
            try:
                attributes = await sqs_service.get_queue_attributes(queue_type)
                if attributes:
                    queue_name = queue_type.value
                    messages = int(attributes.get('ApproximateNumberOfMessages', 0))
                    in_flight = int(attributes.get('ApproximateNumberOfMessagesNotVisible', 0))
                    delayed = int(attributes.get('ApproximateNumberOfMessagesDelayed', 0))
                    
                    metrics.extend([
                        f'sqs_messages_available{{queue="{queue_name}"}} {messages}',
                        f'sqs_messages_in_flight{{queue="{queue_name}"}} {in_flight}',
                        f'sqs_messages_delayed{{queue="{queue_name}"}} {delayed}',
                        f'sqs_queue_healthy{{queue="{queue_name}"}} 1'
                    ])
                else:
                    metrics.append(f'sqs_queue_healthy{{queue="{queue_type.value}"}} 0')
            except Exception:
                metrics.append(f'sqs_queue_healthy{{queue="{queue_type.value}"}} 0')
        
        # Worker metrics
        try:
            from app.workers.message_processor import message_processor
            worker_stats = message_processor.get_stats()
            
            metrics.extend([
                f'workers_running {1 if worker_stats["running"] else 0}',
                f'workers_total_processed {worker_stats.get("total_processed", 0)}',
                f'workers_total_errors {worker_stats.get("total_errors", 0)}',
                f'workers_uptime_seconds {worker_stats.get("uptime_seconds", 0)}'
            ])
            
            # Individual worker metrics
            for worker_name, worker_data in worker_stats.get("workers", {}).items():
                metrics.extend([
                    f'worker_processed{{worker="{worker_name}"}} {worker_data.get("processed", 0)}',
                    f'worker_errors{{worker="{worker_name}"}} {worker_data.get("errors", 0)}',
                    f'worker_running{{worker="{worker_name}"}} {1 if worker_data.get("running", False) else 0}'
                ])
                
        except Exception:
            metrics.append('workers_running 0')
        
        # Add timestamp
        metrics.append(f'monitoring_timestamp {int(time.time())}')
        
        return Response(
            content='\n'.join(metrics) + '\n',
            media_type="text/plain"
        )
        
    except Exception as e:
        logger.error(f"❌ Error generating metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/queues/{queue_type}/history")
async def get_queue_history(
    queue_type: str,
    hours: int = Query(default=24, description="Hours of history to fetch"),
    resolution: int = Query(default=60, description="Resolution in seconds")
):
    """
    Get historical queue metrics (simulated - in production, integrate with CloudWatch)
    """
    try:
        # Validate queue type
        try:
            queue_enum = QueueType(queue_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid queue type: {queue_type}"
            )
        
        # Get current metrics
        attributes = await sqs_service.get_queue_attributes(queue_enum)
        current_messages = int(attributes.get('ApproximateNumberOfMessages', 0)) if attributes else 0
        
        # Generate simulated historical data
        # In production, this would query CloudWatch or your metrics store
        now = datetime.now()
        history = []
        
        for i in range(hours * 3600 // resolution):
            timestamp = now - timedelta(seconds=i * resolution)
            # Simulate some variance around current value
            import random
            simulated_value = max(0, current_messages + random.randint(-5, 5))
            
            history.append({
                "timestamp": timestamp.isoformat(),
                "unix_timestamp": int(timestamp.timestamp()),
                "messages": simulated_value,
                "messages_in_flight": random.randint(0, 3),
                "messages_delayed": random.randint(0, 1)
            })
        
        history.reverse()  # Chronological order
        
        return {
            "queue_type": queue_type,
            "period_hours": hours,
            "resolution_seconds": resolution,
            "data_points": len(history),
            "current_messages": current_messages,
            "history": history
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting queue history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts")
async def get_alerts():
    """
    Get current system alerts and warnings
    """
    alerts = []
    
    try:
        # Check for high message counts
        for queue_type in QueueType:
            try:
                attributes = await sqs_service.get_queue_attributes(queue_type)
                if attributes:
                    messages = int(attributes.get('ApproximateNumberOfMessages', 0))
                    if messages > 100:  # Threshold for high message count
                        alerts.append({
                            "level": "warning" if messages < 500 else "critical",
                            "component": f"queue_{queue_type.value}",
                            "message": f"High message count in {queue_type.value} queue: {messages} messages",
                            "timestamp": int(time.time()),
                            "value": messages,
                            "threshold": 100
                        })
            except Exception:
                alerts.append({
                    "level": "critical",
                    "component": f"queue_{queue_type.value}",
                    "message": f"Cannot access {queue_type.value} queue",
                    "timestamp": int(time.time())
                })
        
        # Check worker status
        try:
            from app.workers.message_processor import message_processor
            worker_stats = message_processor.get_stats()
            
            if not worker_stats["running"]:
                alerts.append({
                    "level": "critical",
                    "component": "workers",
                    "message": "Message processing workers are not running",
                    "timestamp": int(time.time())
                })
            
            # Check for high error rates
            total_processed = worker_stats.get("total_processed", 0)
            total_errors = worker_stats.get("total_errors", 0)
            
            if total_processed > 0:
                error_rate = total_errors / total_processed
                if error_rate > 0.1:  # 10% error rate threshold
                    alerts.append({
                        "level": "warning" if error_rate < 0.2 else "critical",
                        "component": "workers",
                        "message": f"High error rate in message processing: {error_rate:.1%}",
                        "timestamp": int(time.time()),
                        "value": error_rate,
                        "threshold": 0.1
                    })
                    
        except Exception:
            alerts.append({
                "level": "warning",
                "component": "workers",
                "message": "Cannot access worker statistics",
                "timestamp": int(time.time())
            })
        
        return {
            "total_alerts": len(alerts),
            "critical_count": len([a for a in alerts if a["level"] == "critical"]),
            "warning_count": len([a for a in alerts if a["level"] == "warning"]),
            "alerts": alerts,
            "timestamp": int(time.time())
        }
        
    except Exception as e:
        logger.error(f"❌ Error generating alerts: {e}")
        return JSONResponse(
            content={
                "error": str(e),
                "timestamp": int(time.time())
            },
            status_code=500
        )