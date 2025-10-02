"""
Admin API endpoints for Lambda archival management
"""
import boto3
import json
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional
from datetime import datetime
from botocore.exceptions import ClientError

from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])

class LambdaArchivalService:
    def __init__(self):
        settings = get_settings()
        self.lambda_client = boto3.client('lambda', region_name=settings.aws_region)
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=settings.aws_region)
        self.events_client = boto3.client('events', region_name=settings.aws_region)
        self.environment = getattr(settings, 'environment', 'production')
        
    def get_function_name(self, function_type: str) -> str:
        return f"{self.environment}-whatsapp-{function_type}-archival"

@router.post("/archival/trigger")
async def trigger_manual_archival(
    job_type: str = "both",
    dry_run: bool = False
) -> Dict[str, Any]:
    """Manually trigger archival Lambda functions"""
    try:
        service = LambdaArchivalService()
        results = {}
        
        payload = {
            'manual_trigger': True,
            'triggered_by': 'admin_api',
            'triggered_at': datetime.now().isoformat(),
            'dry_run': dry_run
        }
        
        if job_type in ["messages", "both"]:
            try:
                response = service.lambda_client.invoke(
                    FunctionName=service.get_function_name('message'),
                    InvocationType='Event',  # Async
                    Payload=json.dumps(payload)
                )
                
                results['message_archival'] = {
                    'status': 'triggered',
                    'request_id': response['ResponseMetadata']['RequestId'],
                    'function_name': service.get_function_name('message')
                }
            except ClientError as e:
                results['message_archival'] = {
                    'status': 'failed',
                    'error': str(e)
                }
        
        if job_type in ["media", "both"]:
            try:
                response = service.lambda_client.invoke(
                    FunctionName=service.get_function_name('media'),
                    InvocationType='Event',
                    Payload=json.dumps(payload)
                )
                
                results['media_archival'] = {
                    'status': 'triggered',
                    'request_id': response['ResponseMetadata']['RequestId'],
                    'function_name': service.get_function_name('media')
                }
            except ClientError as e:
                results['media_archival'] = {
                    'status': 'failed',
                    'error': str(e)
                }
        
        return {
            'success': True,
            'message': f'Archival functions triggered for: {job_type}',
            'dry_run': dry_run,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to trigger archival: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to trigger archival: {str(e)}"
        )

@router.get("/archival/status")
async def get_archival_status() -> Dict[str, Any]:
    """Get comprehensive status of archival Lambda functions"""
    try:
        service = LambdaArchivalService()
        
        # Get function configurations
        functions_status = {}
        for func_type in ['message', 'media']:
            try:
                func_name = service.get_function_name(func_type)
                func_config = service.lambda_client.get_function(FunctionName=func_name)
                
                # Get recent invocation metrics
                end_time = datetime.now()
                start_time = datetime.fromordinal(end_time.toordinal() - 7)  # Last 7 days
                
                metrics = service.cloudwatch_client.get_metric_statistics(
                    Namespace='AWS/Lambda',
                    MetricName='Invocations',
                    Dimensions=[
                        {
                            'Name': 'FunctionName',
                            'Value': func_name
                        }
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=86400,  # Daily
                    Statistics=['Sum']
                )
                
                functions_status[f'{func_type}_archival'] = {
                    'function_name': func_name,
                    'state': func_config['Configuration']['State'],
                    'last_modified': func_config['Configuration']['LastModified'],
                    'timeout': func_config['Configuration']['Timeout'],
                    'memory_size': func_config['Configuration']['MemorySize'],
                    'runtime': func_config['Configuration']['Runtime'],
                    'recent_invocations': len(metrics['Datapoints']),
                    'code_size': func_config['Configuration']['CodeSize']
                }
            except ClientError as e:
                functions_status[f'{func_type}_archival'] = {
                    'error': str(e),
                    'status': 'not_found'
                }
        
        # Get schedule status
        schedules_status = {}
        for func_type in ['message', 'media']:
            try:
                rule_name = f"{service.environment}-whatsapp-{func_type}-archival-schedule"
                rule = service.events_client.describe_rule(Name=rule_name)
                
                schedules_status[f'{func_type}_archival'] = {
                    'rule_name': rule_name,
                    'schedule': rule['ScheduleExpression'],
                    'state': rule['State'],
                    'description': rule['Description']
                }
            except ClientError as e:
                schedules_status[f'{func_type}_archival'] = {
                    'error': str(e),
                    'status': 'not_found'
                }
        
        return {
            'environment': service.environment,
            'functions': functions_status,
            'schedules': schedules_status,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get archival status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get archival status: {str(e)}"
        )

@router.get("/archival/logs/{function_type}")
async def get_archival_logs(
    function_type: str,
    hours_back: int = 24,
    max_events: int = 100
) -> Dict[str, Any]:
    """Get recent logs for archival functions"""
    try:
        if function_type not in ['message', 'media']:
            raise HTTPException(status_code=400, detail="function_type must be 'message' or 'media'")
        
        service = LambdaArchivalService()
        logs_client = boto3.client('logs')
        
        log_group_name = f"/aws/lambda/{service.environment}-whatsapp-{function_type}-archival"
        
        # Get log events
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now().timestamp() - (hours_back * 3600)) * 1000)
        
        response = logs_client.filter_log_events(
            logGroupName=log_group_name,
            startTime=start_time,
            endTime=end_time,
            limit=max_events
        )
        
        events = []
        for event in response.get('events', []):
            events.append({
                'timestamp': datetime.fromtimestamp(event['timestamp'] / 1000).isoformat(),
                'message': event['message'].strip(),
                'log_stream': event['logStreamName']
            })
        
        return {
            'function_type': function_type,
            'log_group': log_group_name,
            'hours_back': hours_back,
            'event_count': len(events),
            'events': events[-max_events:],  # Most recent events
            'timestamp': datetime.now().isoformat()
        }
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            raise HTTPException(status_code=404, detail="Log group not found")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get archival logs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/archival/schedule/toggle/{function_type}")
async def toggle_archival_schedule(
    function_type: str,
    enabled: bool
) -> Dict[str, Any]:
    """Enable or disable archival schedule for a function"""
    try:
        if function_type not in ['message', 'media']:
            raise HTTPException(status_code=400, detail="function_type must be 'message' or 'media'")
        
        service = LambdaArchivalService()
        rule_name = f"{service.environment}-whatsapp-{function_type}-archival-schedule"
        
        if enabled:
            service.events_client.enable_rule(Name=rule_name)
            action = "enabled"
        else:
            service.events_client.disable_rule(Name=rule_name)
            action = "disabled"
        
        return {
            'success': True,
            'message': f'Schedule {action} for {function_type} archival',
            'rule_name': rule_name,
            'enabled': enabled,
            'timestamp': datetime.now().isoformat()
        }
        
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to toggle schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/archival/metrics")
async def get_archival_metrics(days_back: int = 7) -> Dict[str, Any]:
    """Get archival performance metrics"""
    try:
        service = LambdaArchivalService()
        
        end_time = datetime.now()
        start_time = datetime.fromordinal(end_time.toordinal() - days_back)
        
        metrics = {}
        
        for func_type in ['message', 'media']:
            func_name = service.get_function_name(func_type)
            
            # Get various metrics
            metric_queries = {
                'invocations': 'Invocations',
                'errors': 'Errors',
                'duration': 'Duration',
                'throttles': 'Throttles'
            }
            
            func_metrics = {}
            for metric_key, metric_name in metric_queries.items():
                try:
                    response = service.cloudwatch_client.get_metric_statistics(
                        Namespace='AWS/Lambda',
                        MetricName=metric_name,
                        Dimensions=[{'Name': 'FunctionName', 'Value': func_name}],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=86400,  # Daily
                        Statistics=['Sum', 'Average'] if metric_name == 'Duration' else ['Sum']
                    )
                    
                    datapoints = response.get('Datapoints', [])
                    if datapoints:
                        if metric_name == 'Duration':
                            func_metrics[metric_key] = {
                                'average_ms': sum(dp['Average'] for dp in datapoints) / len(datapoints),
                                'total_datapoints': len(datapoints)
                            }
                        else:
                            func_metrics[metric_key] = {
                                'total': sum(dp['Sum'] for dp in datapoints),
                                'daily_average': sum(dp['Sum'] for dp in datapoints) / len(datapoints)
                            }
                    else:
                        func_metrics[metric_key] = {'total': 0, 'daily_average': 0}
                        
                except ClientError:
                    func_metrics[metric_key] = {'error': 'No data available'}
            
            metrics[f'{func_type}_archival'] = func_metrics
        
        return {
            'period': {
                'days_back': days_back,
                'start_date': start_time.isoformat(),
                'end_date': end_time.isoformat()
            },
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get archival metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))