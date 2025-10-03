"""
Banking Workflow Automation - Main API
FastAPI application providing workflow automation endpoints
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from typing import List, Dict, Any, Optional
import uvicorn
import json
import os
from datetime import datetime
import uuid
import secrets
import hashlib
import asyncio
import logging
from contextlib import asynccontextmanager

from models import (
    Application, ApplicationStatus, RiskLevel, AccountType,
    PersonalInfo, EmploymentInfo, ValidationResult, DashboardMetrics,
    BusinessRule, WorkflowConfig, WorkflowStep
)
from rules_engine import RulesEngine
from ai_validator import AIValidator
from integrations import IntegrationOrchestrator

# Configure secure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security configuration
ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "https://app.yourdomain.com",
    # Add specific origins in production
]

# In production, load from secure environment variables
API_KEYS = {
    os.getenv("API_KEY_1", "dev-key-1"): "admin",
    os.getenv("API_KEY_2", "dev-key-2"): "user"
}

# Initialize FastAPI app
app = FastAPI(
    title="Banking Workflow Automation API",
    description="AI-Powered Account Opening & Workflow Orchestration Platform",
    version="1.0.0"
)

# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response

# Add CORS middleware with secure configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Only allow specific origins
    allow_credentials=False,  # Disable credentials with wildcard origins
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
    max_age=3600,
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "yourdomain.com", "*.yourdomain.com"]
)

# Initialize engines
rules_engine = RulesEngine()
ai_validator = AIValidator()
integration_orchestrator = IntegrationOrchestrator()

# In-memory storage (in production, use a real database)
applications_db: Dict[str, Application] = {}
workflows_db: Dict[str, WorkflowConfig] = {}

# Thread-safe lock for application processing
application_locks: Dict[str, asyncio.Lock] = {}
db_lock = asyncio.Lock()

# Rate limiting storage
rate_limit_storage: Dict[str, List[float]] = {}

# Authentication and Authorization
async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """Verify API key for authentication"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")

    if x_api_key not in API_KEYS:
        logger.warning(f"Invalid API key attempted: {x_api_key[:8]}...")
        raise HTTPException(status_code=401, detail="Invalid API key")

    return API_KEYS[x_api_key]

async def rate_limit_check(request: Request, user: str = Depends(verify_api_key)):
    """Simple rate limiting - 100 requests per minute per user"""
    current_time = datetime.now().timestamp()
    window = 60  # 60 seconds
    max_requests = 100

    if user not in rate_limit_storage:
        rate_limit_storage[user] = []

    # Clean old entries
    rate_limit_storage[user] = [
        ts for ts in rate_limit_storage[user]
        if current_time - ts < window
    ]

    if len(rate_limit_storage[user]) >= max_requests:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    rate_limit_storage[user].append(current_time)
    return user

def redact_pii(data: Dict[str, Any]) -> Dict[str, Any]:
    """Redact PII from data for logging"""
    redacted = data.copy()
    sensitive_fields = ['ssn', 'password', 'api_key', 'token', 'credit_card']

    for key in redacted:
        if any(field in key.lower() for field in sensitive_fields):
            redacted[key] = "***REDACTED***"

    return redacted

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input to prevent injection attacks"""
    if not text:
        return ""

    # Limit length
    text = text[:max_length]

    # Remove null bytes
    text = text.replace('\x00', '')

    # Basic HTML/script tag removal
    text = text.replace('<', '&lt;').replace('>', '&gt;')

    return text.strip()

def validate_application_id(app_id: str) -> bool:
    """Validate application ID format to prevent injection"""
    import re
    # Must match APP-[12 hex chars]
    pattern = r'^APP-[A-F0-9]{12}$'
    return bool(re.match(pattern, app_id))


# Utility Functions
def generate_application_id() -> str:
    """Generate unique application ID"""
    return f"APP-{uuid.uuid4().hex[:12].upper()}"


def load_default_workflows():
    """Load default workflow configurations"""
    workflows = {
        "personal_checking": WorkflowConfig(
            workflow_id="wf_personal_checking",
            workflow_name="Personal Checking Account",
            account_type=AccountType.PERSONAL_CHECKING,
            steps=[
                WorkflowStep(
                    step_id="personal_info",
                    step_name="Personal Information",
                    step_order=1,
                    required_fields=["first_name", "last_name", "email", "phone", "date_of_birth", "ssn", "address"],
                    validation_rules=["age_verification", "ssn_format"]
                ),
                WorkflowStep(
                    step_id="identity_verification",
                    step_name="Identity Verification",
                    step_order=2,
                    required_fields=[],
                    integrations_required=["identity_verification", "fraud_database"],
                    auto_advance=True
                ),
                WorkflowStep(
                    step_id="kyc_aml",
                    step_name="KYC/AML Screening",
                    step_order=3,
                    required_fields=[],
                    integrations_required=["kyc_aml_screening"],
                    auto_advance=True
                ),
                WorkflowStep(
                    step_id="review",
                    step_name="Final Review",
                    step_order=4,
                    required_fields=[],
                    auto_advance=False
                )
            ],
            business_rules=rules_engine.get_all_rules()
        )
    }
    return workflows


# Load default workflows on startup
workflows_db = load_default_workflows()


# API Endpoints

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - redirect to documentation"""
    return """
    <html>
        <head><title>Banking Workflow Automation API</title></head>
        <body style="font-family: Arial; padding: 40px;">
            <h1>Banking Workflow Automation API</h1>
            <p>AI-Powered Account Opening & Workflow Orchestration Platform</p>
            <h2>Available Endpoints:</h2>
            <ul>
                <li><a href="/docs">API Documentation (Swagger)</a></li>
                <li><a href="/applications">List Applications</a></li>
                <li><a href="/dashboard/metrics">Dashboard Metrics</a></li>
                <li><a href="/workflows">Available Workflows</a></li>
                <li><a href="/rules">Business Rules</a></li>
            </ul>
            <h2>Quick Start:</h2>
            <p>1. POST /applications/create - Create a new application</p>
            <p>2. POST /applications/{id}/validate - Validate application data</p>
            <p>3. POST /applications/{id}/submit - Submit for processing</p>
            <p>4. GET /applications/{id}/status - Check status</p>
        </body>
    </html>
    """


@app.post("/applications/create", response_model=Application)
async def create_application(
    personal_info: PersonalInfo,
    account_type: AccountType,
    employment_info: EmploymentInfo = None,
    user: str = Depends(rate_limit_check)
):
    """Create a new application"""
    # Sanitize inputs
    personal_info.first_name = sanitize_input(personal_info.first_name, 100)
    personal_info.last_name = sanitize_input(personal_info.last_name, 100)
    personal_info.email = sanitize_input(personal_info.email, 255)
    personal_info.address_line1 = sanitize_input(personal_info.address_line1, 500)

    if personal_info.middle_name:
        personal_info.middle_name = sanitize_input(personal_info.middle_name, 100)
    if personal_info.address_line2:
        personal_info.address_line2 = sanitize_input(personal_info.address_line2, 500)

    application_id = generate_application_id()

    application = Application(
        application_id=application_id,
        account_type=account_type,
        personal_info=personal_info,
        employment_info=employment_info,
        status=ApplicationStatus.DRAFT
    )

    async with db_lock:
        applications_db[application_id] = application

    logger.info(f"Application created: {application_id} by user: {user}")

    return application


@app.get("/applications", response_model=List[Application])
async def list_applications(
    status: ApplicationStatus = None,
    limit: int = 100,
    user: str = Depends(rate_limit_check)
):
    """List all applications"""
    # Validate limit parameter
    if limit < 1:
        raise HTTPException(status_code=400, detail="Limit must be at least 1")
    if limit > 1000:
        raise HTTPException(status_code=400, detail="Limit cannot exceed 1000")

    apps = list(applications_db.values())

    if status:
        apps = [app for app in apps if app.status == status]

    return apps[:limit]


@app.get("/applications/{application_id}", response_model=Application)
async def get_application(application_id: str, user: str = Depends(rate_limit_check)):
    """Get specific application"""
    # Validate application ID format
    if not validate_application_id(application_id):
        raise HTTPException(status_code=400, detail="Invalid application ID format")

    if application_id not in applications_db:
        raise HTTPException(status_code=404, detail="Application not found")

    return applications_db[application_id]


@app.post("/applications/{application_id}/validate")
async def validate_application(
    application_id: str,
    user: str = Depends(rate_limit_check)
) -> Dict[str, Any]:
    """Validate application data using AI"""
    # Validate application ID format
    if not validate_application_id(application_id):
        raise HTTPException(status_code=400, detail="Invalid application ID format")

    if application_id not in applications_db:
        raise HTTPException(status_code=404, detail="Application not found")

    application = applications_db[application_id]

    # Run AI validation
    validation_report = ai_validator.generate_validation_report(application)

    # Update application with AI scores
    async with db_lock:
        application.ai_fraud_score = validation_report["fraud_score"]
        application.ai_confidence = validation_report["average_confidence"]

    logger.info(f"Application validated: {application_id} by user: {user}")

    return validation_report


@app.post("/applications/{application_id}/submit")
async def submit_application(
    application_id: str,
    background_tasks: BackgroundTasks,
    user: str = Depends(rate_limit_check)
):
    """Submit application for processing"""
    # Validate application ID format
    if not validate_application_id(application_id):
        raise HTTPException(status_code=400, detail="Invalid application ID format")

    if application_id not in applications_db:
        raise HTTPException(status_code=404, detail="Application not found")

    application = applications_db[application_id]

    if application.status != ApplicationStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Application already submitted")

    # Validate first
    validation_report = ai_validator.generate_validation_report(application)

    if not validation_report["overall_valid"]:
        # Don't expose internal validation details
        raise HTTPException(
            status_code=400,
            detail="Application validation failed. Please review and correct the application data."
        )

    # Update status with lock
    async with db_lock:
        application.status = ApplicationStatus.SUBMITTED
        application.submitted_at = datetime.now()

    logger.info(f"Application submitted: {application_id} by user: {user}")

    # Process application in background
    background_tasks.add_task(process_application, application_id)

    return {
        "application_id": application_id,
        "status": "submitted",
        "message": "Application submitted successfully and is being processed"
    }


async def process_application(application_id: str):
    """Background task to process application"""
    # Get or create lock for this application
    if application_id not in application_locks:
        async with db_lock:
            if application_id not in application_locks:
                application_locks[application_id] = asyncio.Lock()

    # Ensure only one process handles this application at a time
    async with application_locks[application_id]:
        try:
            application = applications_db.get(application_id)
            if not application:
                logger.error(f"Application not found in processing: {application_id}")
                return

            # Step 1: Run integrations
            async with db_lock:
                application.status = ApplicationStatus.IDENTITY_VERIFICATION

            # Create app_data WITHOUT sensitive SSN information in logs
            personal_info_dict = application.personal_info.dict()
            # Redact SSN for logging/processing
            personal_info_safe = {k: v for k, v in personal_info_dict.items() if k != 'ssn'}
            personal_info_safe['ssn_last_4'] = personal_info_dict['ssn'][-4:] if 'ssn' in personal_info_dict else 'XXXX'

            app_data = {
                "personal_info": personal_info_dict,  # Full data for integrations
                "employment_info": application.employment_info.dict() if application.employment_info else None
            }

            # Run standard checks
            integration_results = await integration_orchestrator.run_standard_checks(app_data)

            # Add integrations to application
            async with db_lock:
                for key, integration in integration_results.items():
                    application.integrations.append(integration)

            # Step 2: Run business rules
            async with db_lock:
                application.status = ApplicationStatus.COMPLIANCE_REVIEW

            rules_result = rules_engine.evaluate_application(application)

            # Update application with rules results
            async with db_lock:
                application.risk_level = rules_result["risk_level"]
                application.rules_applied = rules_result["triggered_rules"]

            # Step 3: Determine outcome
            if rules_result["can_auto_approve"]:
                async with db_lock:
                    application.status = ApplicationStatus.APPROVED
                    application.approval_decision = "approved"
                    application.decision_reason = "Auto-approved - low risk, all verifications passed"
            elif "manual_review" in rules_result["next_action"] or "fraud_review" in rules_result["next_action"]:
                async with db_lock:
                    application.status = ApplicationStatus.MANUAL_REVIEW
                    application.assigned_to = "fraud_team" if "fraud" in rules_result["next_action"] else "review_team"
            elif application.risk_level == RiskLevel.HIGH or application.risk_level == RiskLevel.CRITICAL:
                async with db_lock:
                    application.status = ApplicationStatus.MANUAL_REVIEW
                    application.assigned_to = "senior_reviewer"
            else:
                # Run credit check for medium risk
                credit_result = await integration_orchestrator.integration_service.check_credit(app_data["personal_info"])
                async with db_lock:
                    application.integrations.append(credit_result)

                if credit_result.response_data.get("credit_score", 0) >= 650:
                    async with db_lock:
                        application.status = ApplicationStatus.APPROVED
                        application.approval_decision = "approved"
                        application.decision_reason = "Approved after credit check"
                else:
                    async with db_lock:
                        application.status = ApplicationStatus.MANUAL_REVIEW
                        application.decision_reason = "Credit score below threshold"

            async with db_lock:
                application.completed_at = datetime.now()
                application.updated_at = datetime.now()

            logger.info(f"Application processing completed: {application_id}, status: {application.status}")

        except ValueError as e:
            logger.error(f"Validation error processing application {application_id}: {str(e)}")
            async with db_lock:
                application.status = ApplicationStatus.MANUAL_REVIEW
                application.ai_notes.append("Processing error - requires manual review")
        except KeyError as e:
            logger.error(f"Data error processing application {application_id}: missing key {str(e)}")
            async with db_lock:
                application.status = ApplicationStatus.MANUAL_REVIEW
                application.ai_notes.append("Data error - requires manual review")
        except Exception as e:
            logger.error(f"Unexpected error processing application {application_id}: {type(e).__name__}")
            async with db_lock:
                application.status = ApplicationStatus.MANUAL_REVIEW
                application.ai_notes.append("System error - requires manual review")
        finally:
            # Clean up lock after processing
            if application_id in application_locks:
                async with db_lock:
                    if application_id in application_locks:
                        del application_locks[application_id]


@app.get("/applications/{application_id}/status")
async def get_application_status(
    application_id: str,
    user: str = Depends(rate_limit_check)
):
    """Get application status"""
    # Validate application ID format
    if not validate_application_id(application_id):
        raise HTTPException(status_code=400, detail="Invalid application ID format")

    if application_id not in applications_db:
        raise HTTPException(status_code=404, detail="Application not found")

    application = applications_db[application_id]

    return {
        "application_id": application_id,
        "status": application.status,
        "risk_level": application.risk_level,
        "created_at": application.created_at,
        "submitted_at": application.submitted_at,
        "completed_at": application.completed_at,
        "approval_decision": application.approval_decision,
        "decision_reason": application.decision_reason,
        "integrations_completed": len(application.integrations),
        "rules_applied": len(application.rules_applied)
    }


@app.get("/dashboard/metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics(user: str = Depends(rate_limit_check)):
    """Get dashboard metrics"""
    applications = list(applications_db.values())

    if not applications:
        return DashboardMetrics(
            total_applications=0,
            applications_by_status={},
            average_processing_time_hours=0,
            automation_rate=0,
            approval_rate=0,
            fraud_detection_rate=0,
            integration_success_rate=0,
            applications_last_24h=0
        )

    # Calculate metrics
    total = len(applications)

    status_counts = {}
    for app in applications:
        status_counts[app.status.value] = status_counts.get(app.status.value, 0) + 1

    # Calculate processing times
    processing_times = []
    for app in applications:
        if app.submitted_at and app.completed_at:
            delta = (app.completed_at - app.submitted_at).total_seconds() / 3600
            processing_times.append(delta)

    avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0

    # Calculate rates
    approved = sum(1 for app in applications if app.status == ApplicationStatus.APPROVED)
    auto_approved = sum(1 for app in applications if app.approval_decision == "approved" and "Auto-approved" in (app.decision_reason or ""))
    fraud_flagged = sum(1 for app in applications if app.ai_fraud_score > 0.6)

    # Integration success rate
    total_integrations = sum(len(app.integrations) for app in applications)
    successful_integrations = sum(1 for app in applications for i in app.integrations if i.status == "success")

    # Applications last 24h
    now = datetime.now()
    last_24h = sum(1 for app in applications if (now - app.created_at).total_seconds() < 86400)

    return DashboardMetrics(
        total_applications=total,
        applications_by_status=status_counts,
        average_processing_time_hours=round(avg_processing_time, 2),
        automation_rate=round(auto_approved / total, 2) if total > 0 else 0,
        approval_rate=round(approved / total, 2) if total > 0 else 0,
        fraud_detection_rate=round(fraud_flagged / total, 2) if total > 0 else 0,
        integration_success_rate=round(successful_integrations / total_integrations, 2) if total_integrations > 0 else 0,
        applications_last_24h=last_24h
    )


@app.get("/workflows", response_model=List[WorkflowConfig])
async def list_workflows(user: str = Depends(rate_limit_check)):
    """List available workflows"""
    return list(workflows_db.values())


@app.get("/rules", response_model=List[BusinessRule])
async def list_business_rules(user: str = Depends(rate_limit_check)):
    """List all business rules"""
    return rules_engine.get_all_rules()


@app.post("/rules", response_model=BusinessRule)
async def create_business_rule(rule: BusinessRule, user: str = Depends(rate_limit_check)):
    """Create a new business rule"""
    # Sanitize rule fields
    rule.rule_name = sanitize_input(rule.rule_name, 200)
    rule.condition = sanitize_input(rule.condition, 500)
    rule.action = sanitize_input(rule.action, 200)

    rules_engine.add_rule(rule)
    logger.info(f"Business rule created: {rule.rule_id} by user: {user}")
    return rule


@app.delete("/rules/{rule_id}")
async def delete_business_rule(rule_id: str, user: str = Depends(rate_limit_check)):
    """Delete a business rule"""
    # Sanitize rule_id
    rule_id = sanitize_input(rule_id, 100)

    rules_engine.remove_rule(rule_id)
    logger.info(f"Business rule deleted: {rule_id} by user: {user}")
    return {"message": f"Rule deleted successfully"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "applications_count": len(applications_db),
        "workflows_count": len(workflows_db),
        "rules_count": len(rules_engine.get_all_rules())
    }


if __name__ == "__main__":
    print("🚀 Starting Banking Workflow Automation API...")
    print("📊 Dashboard: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("=" * 50)

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
