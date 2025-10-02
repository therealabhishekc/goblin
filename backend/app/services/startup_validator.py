"""
Startup validation service for WhatsApp Business API
Validates critical dependencies before accepting webhook traffic
"""
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass

from app.config import get_settings
from app.core.database import SessionLocal, engine
from app.core.logging import logger
from sqlalchemy import text

# Import SQS service conditionally
try:
    from app.services.sqs_service import sqs_service
    SQS_AVAILABLE = True
except ImportError:
    sqs_service = None
    SQS_AVAILABLE = False

@dataclass
class ValidationResult:
    """Result of a validation check"""
    name: str
    passed: bool
    critical: bool
    message: str
    details: Optional[Dict] = None

class StartupValidator:
    """Validates application dependencies on startup"""
    
    def __init__(self):
        self.settings = get_settings()
        self.validation_results: List[ValidationResult] = []
    
    async def validate_all(self) -> bool:
        """
        Run all validation checks
        
        Returns:
            True if all critical checks pass, False otherwise
        """
        self.validation_results.clear()
        
        logger.info("🔍 Starting application dependency validation...")
        
        # Run all validation checks
        await self._validate_database()
        await self._validate_sqs_queues()
        self._validate_whatsapp_config()
        await self._validate_secrets_access()
        
        # Analyze results
        critical_failures = [r for r in self.validation_results if not r.passed and r.critical]
        warnings = [r for r in self.validation_results if not r.passed and not r.critical]
        passed = [r for r in self.validation_results if r.passed]
        
        # Log summary
        logger.info(f"✅ Validation passed: {len(passed)}")
        if warnings:
            logger.warning(f"⚠️  Non-critical warnings: {len(warnings)}")
            for warning in warnings:
                logger.warning(f"   - {warning.name}: {warning.message}")
        
        if critical_failures:
            logger.error(f"❌ Critical validation failures: {len(critical_failures)}")
            for failure in critical_failures:
                logger.error(f"   - {failure.name}: {failure.message}")
            return False
        
        logger.info("🎉 All critical validations passed - application ready!")
        return True
    
    async def _validate_database(self):
        """Validate database connectivity"""
        try:
            db = SessionLocal()
            try:
                # Test basic connectivity
                db.execute(text("SELECT 1"))
                
                # Test table exists (basic schema check)
                try:
                    db.execute(text("SELECT COUNT(*) FROM user_profiles LIMIT 1"))
                    schema_check = True
                except Exception:
                    schema_check = False
                
                self.validation_results.append(ValidationResult(
                    name="Database Connectivity",
                    passed=True,
                    critical=True,
                    message="Database connection successful",
                    details={"schema_validated": schema_check}
                ))
                
                if not schema_check:
                    self.validation_results.append(ValidationResult(
                        name="Database Schema",
                        passed=False,
                        critical=False,
                        message="Database tables may not be initialized - run migrations"
                    ))
                    
            finally:
                db.close()
                
        except Exception as e:
            self.validation_results.append(ValidationResult(
                name="Database Connectivity",
                passed=False,
                critical=True,
                message=f"Database connection failed: {str(e)}"
            ))
    
    async def _validate_sqs_queues(self):
        """Validate SQS queue configuration and accessibility"""
        if not SQS_AVAILABLE or not sqs_service:
            self.validation_results.append(ValidationResult(
                name="SQS Service",
                passed=False,
                critical=True,
                message="SQS service not available - message queuing disabled"
            ))
            return
        
        try:
            # Get queue health status
            health_result = await sqs_service.health_check()
            
            # Check critical queues
            critical_queues = ["incoming"]
            optional_queues = ["outgoing", "analytics"]
            
            critical_failures = []
            optional_failures = []
            
            for queue_name in critical_queues:
                if queue_name not in health_result["queues"]:
                    critical_failures.append(f"{queue_name} queue not configured")
                elif health_result["queues"][queue_name]["status"] != "healthy":
                    critical_failures.append(f"{queue_name} queue unhealthy")
            
            for queue_name in optional_queues:
                if queue_name not in health_result["queues"]:
                    optional_failures.append(f"{queue_name} queue not configured")
                elif health_result["queues"][queue_name]["status"] != "healthy":
                    optional_failures.append(f"{queue_name} queue unhealthy")
            
            # Critical queue validation
            if critical_failures:
                self.validation_results.append(ValidationResult(
                    name="Critical SQS Queues",
                    passed=False,
                    critical=True,
                    message=f"Critical queue issues: {', '.join(critical_failures)}",
                    details=health_result["queues"]
                ))
            else:
                self.validation_results.append(ValidationResult(
                    name="Critical SQS Queues",
                    passed=True,
                    critical=True,
                    message="All critical queues are healthy",
                    details={k: v for k, v in health_result["queues"].items() if k in critical_queues}
                ))
            
            # Optional queue validation
            if optional_failures:
                self.validation_results.append(ValidationResult(
                    name="Optional SQS Queues",
                    passed=False,
                    critical=False,
                    message=f"Optional queue issues: {', '.join(optional_failures)}",
                    details={k: v for k, v in health_result["queues"].items() if k in optional_queues}
                ))
            else:
                configured_optional = [q for q in optional_queues if q in health_result["queues"]]
                if configured_optional:
                    self.validation_results.append(ValidationResult(
                        name="Optional SQS Queues",
                        passed=True,
                        critical=False,
                        message=f"Optional queues healthy: {', '.join(configured_optional)}",
                        details={k: v for k, v in health_result["queues"].items() if k in optional_queues}
                    ))
                    
        except Exception as e:
            self.validation_results.append(ValidationResult(
                name="SQS Queue Validation",
                passed=False,
                critical=True,
                message=f"SQS validation failed: {str(e)}"
            ))
    
    def _validate_whatsapp_config(self):
        """Validate WhatsApp API configuration"""
        issues = []
        
        if not self.settings.whatsapp_token:
            issues.append("WhatsApp token not configured")
        if not self.settings.verify_token:
            issues.append("Verify token not configured")
        if not self.settings.whatsapp_phone_number_id and not self.settings.phone_number_id:
            issues.append("Phone number ID not configured")
        
        if issues:
            self.validation_results.append(ValidationResult(
                name="WhatsApp Configuration",
                passed=False,
                critical=True,
                message=f"WhatsApp config incomplete: {', '.join(issues)}"
            ))
        else:
            self.validation_results.append(ValidationResult(
                name="WhatsApp Configuration",
                passed=True,
                critical=True,
                message="WhatsApp API configuration complete"
            ))
    
    async def _validate_secrets_access(self):
        """Validate AWS Secrets Manager access (if configured)"""
        secrets_name = getattr(self.settings, 'whatsapp_secrets_name', None)
        
        if not secrets_name:
            self.validation_results.append(ValidationResult(
                name="Secrets Manager",
                passed=True,
                critical=False,
                message="Secrets Manager not configured - using environment variables"
            ))
            return
        
        try:
            # Try to import and test secrets access
            from app.utils.secrets import secrets_manager
            
            # Test access without actually retrieving secrets
            credentials = secrets_manager.get_whatsapp_credentials()
            
            if credentials and any(credentials.values()):
                self.validation_results.append(ValidationResult(
                    name="Secrets Manager",
                    passed=True,
                    critical=False,
                    message="AWS Secrets Manager access successful"
                ))
            else:
                self.validation_results.append(ValidationResult(
                    name="Secrets Manager", 
                    passed=False,
                    critical=False,
                    message="Secrets Manager configured but no credentials retrieved"
                ))
                
        except Exception as e:
            self.validation_results.append(ValidationResult(
                name="Secrets Manager",
                passed=False,
                critical=False,
                message=f"Secrets Manager validation failed: {str(e)}"
            ))
    
    def get_validation_summary(self) -> Dict:
        """Get validation summary for reporting"""
        critical_failures = [r for r in self.validation_results if not r.passed and r.critical]
        warnings = [r for r in self.validation_results if not r.passed and not r.critical]
        passed = [r for r in self.validation_results if r.passed]
        
        return {
            "ready": len(critical_failures) == 0,
            "summary": {
                "passed": len(passed),
                "warnings": len(warnings),
                "critical_failures": len(critical_failures)
            },
            "results": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "critical": r.critical,
                    "message": r.message,
                    "details": r.details
                } for r in self.validation_results
            ]
        }

# Global validator instance
startup_validator = StartupValidator()

async def validate_startup() -> bool:
    """
    Convenience function to run startup validation
    
    Returns:
        True if application is ready to accept traffic
    """
    return await startup_validator.validate_all()

def is_application_ready() -> bool:
    """
    Quick check if application passed startup validation
    Use this to gate webhook processing
    """
    if not startup_validator.validation_results:
        # No validation has been run yet
        return False
    
    critical_failures = [
        r for r in startup_validator.validation_results 
        if not r.passed and r.critical
    ]
    
    return len(critical_failures) == 0