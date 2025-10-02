"""
Banking Workflow Automation - Main API
FastAPI application providing workflow automation endpoints
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from typing import List, Dict, Any
import uvicorn
import json
import os
from datetime import datetime
import uuid

from models import (
    Application, ApplicationStatus, RiskLevel, AccountType,
    PersonalInfo, EmploymentInfo, ValidationResult, DashboardMetrics,
    BusinessRule, WorkflowConfig, WorkflowStep
)
from rules_engine import RulesEngine
from ai_validator import AIValidator
from integrations import IntegrationOrchestrator

# Initialize FastAPI app
app = FastAPI(
    title="Banking Workflow Automation API",
    description="AI-Powered Account Opening & Workflow Orchestration Platform",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines
rules_engine = RulesEngine()
ai_validator = AIValidator()
integration_orchestrator = IntegrationOrchestrator()

# In-memory storage (in production, use a real database)
applications_db: Dict[str, Application] = {}
workflows_db: Dict[str, WorkflowConfig] = {}


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
    employment_info: EmploymentInfo = None
):
    """Create a new application"""
    application_id = generate_application_id()

    application = Application(
        application_id=application_id,
        account_type=account_type,
        personal_info=personal_info,
        employment_info=employment_info,
        status=ApplicationStatus.DRAFT
    )

    applications_db[application_id] = application

    return application


@app.get("/applications", response_model=List[Application])
async def list_applications(
    status: ApplicationStatus = None,
    limit: int = 100
):
    """List all applications"""
    apps = list(applications_db.values())

    if status:
        apps = [app for app in apps if app.status == status]

    return apps[:limit]


@app.get("/applications/{application_id}", response_model=Application)
async def get_application(application_id: str):
    """Get specific application"""
    if application_id not in applications_db:
        raise HTTPException(status_code=404, detail="Application not found")

    return applications_db[application_id]


@app.post("/applications/{application_id}/validate")
async def validate_application(application_id: str) -> Dict[str, Any]:
    """Validate application data using AI"""
    if application_id not in applications_db:
        raise HTTPException(status_code=404, detail="Application not found")

    application = applications_db[application_id]

    # Run AI validation
    validation_report = ai_validator.generate_validation_report(application)

    # Update application with AI scores
    application.ai_fraud_score = validation_report["fraud_score"]
    application.ai_confidence = validation_report["average_confidence"]

    return validation_report


@app.post("/applications/{application_id}/submit")
async def submit_application(application_id: str, background_tasks: BackgroundTasks):
    """Submit application for processing"""
    if application_id not in applications_db:
        raise HTTPException(status_code=404, detail="Application not found")

    application = applications_db[application_id]

    if application.status != ApplicationStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Application already submitted")

    # Validate first
    validation_report = ai_validator.generate_validation_report(application)

    if not validation_report["overall_valid"]:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Validation failed",
                "failures": [v.dict() for v in validation_report["validation_results"] if not v.is_valid]
            }
        )

    # Update status
    application.status = ApplicationStatus.SUBMITTED
    application.submitted_at = datetime.now()

    # Process application in background
    background_tasks.add_task(process_application, application_id)

    return {
        "application_id": application_id,
        "status": "submitted",
        "message": "Application submitted successfully and is being processed"
    }


async def process_application(application_id: str):
    """Background task to process application"""
    application = applications_db[application_id]

    try:
        # Step 1: Run integrations
        application.status = ApplicationStatus.IDENTITY_VERIFICATION

        app_data = {
            "personal_info": application.personal_info.dict(),
            "employment_info": application.employment_info.dict() if application.employment_info else None
        }

        # Run standard checks
        integration_results = await integration_orchestrator.run_standard_checks(app_data)

        # Add integrations to application
        for key, integration in integration_results.items():
            application.integrations.append(integration)

        # Step 2: Run business rules
        application.status = ApplicationStatus.COMPLIANCE_REVIEW
        rules_result = rules_engine.evaluate_application(application)

        # Update application with rules results
        application.risk_level = rules_result["risk_level"]
        application.rules_applied = rules_result["triggered_rules"]

        # Step 3: Determine outcome
        if rules_result["can_auto_approve"]:
            application.status = ApplicationStatus.APPROVED
            application.approval_decision = "approved"
            application.decision_reason = "Auto-approved - low risk, all verifications passed"
        elif "manual_review" in rules_result["next_action"] or "fraud_review" in rules_result["next_action"]:
            application.status = ApplicationStatus.MANUAL_REVIEW
            application.assigned_to = "fraud_team" if "fraud" in rules_result["next_action"] else "review_team"
        elif application.risk_level == RiskLevel.HIGH or application.risk_level == RiskLevel.CRITICAL:
            application.status = ApplicationStatus.MANUAL_REVIEW
            application.assigned_to = "senior_reviewer"
        else:
            # Run credit check for medium risk
            credit_result = await integration_orchestrator.integration_service.check_credit(app_data["personal_info"])
            application.integrations.append(credit_result)

            if credit_result.response_data["credit_score"] >= 650:
                application.status = ApplicationStatus.APPROVED
                application.approval_decision = "approved"
                application.decision_reason = "Approved after credit check"
            else:
                application.status = ApplicationStatus.MANUAL_REVIEW
                application.decision_reason = "Credit score below threshold"

        application.completed_at = datetime.now()
        application.updated_at = datetime.now()

    except Exception as e:
        application.status = ApplicationStatus.MANUAL_REVIEW
        application.ai_notes.append(f"Processing error: {str(e)}")


@app.get("/applications/{application_id}/status")
async def get_application_status(application_id: str):
    """Get application status"""
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
async def get_dashboard_metrics():
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
async def list_workflows():
    """List available workflows"""
    return list(workflows_db.values())


@app.get("/rules", response_model=List[BusinessRule])
async def list_business_rules():
    """List all business rules"""
    return rules_engine.get_all_rules()


@app.post("/rules", response_model=BusinessRule)
async def create_business_rule(rule: BusinessRule):
    """Create a new business rule"""
    rules_engine.add_rule(rule)
    return rule


@app.delete("/rules/{rule_id}")
async def delete_business_rule(rule_id: str):
    """Delete a business rule"""
    rules_engine.remove_rule(rule_id)
    return {"message": f"Rule {rule_id} deleted"}


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
