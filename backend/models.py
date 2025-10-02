"""
Data models for Banking Workflow Automation
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from enum import Enum


class ApplicationStatus(str, Enum):
    """Application status enum"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    IDENTITY_VERIFICATION = "identity_verification"
    DOCUMENT_REVIEW = "document_review"
    CREDIT_CHECK = "credit_check"
    COMPLIANCE_REVIEW = "compliance_review"
    MANUAL_REVIEW = "manual_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class RiskLevel(str, Enum):
    """Risk assessment levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AccountType(str, Enum):
    """Account types"""
    PERSONAL_CHECKING = "personal_checking"
    PERSONAL_SAVINGS = "personal_savings"
    BUSINESS_CHECKING = "business_checking"
    BUSINESS_SAVINGS = "business_savings"
    MINOR_ACCOUNT = "minor_account"


class PersonalInfo(BaseModel):
    """Personal information data"""
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    email: EmailStr
    phone: str
    date_of_birth: str
    ssn: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    zip_code: str
    citizenship: str = "US"


class EmploymentInfo(BaseModel):
    """Employment information"""
    employer_name: Optional[str] = None
    occupation: Optional[str] = None
    annual_income: Optional[float] = None
    employment_status: str = "employed"


class Document(BaseModel):
    """Document information"""
    document_type: str
    document_id: str
    uploaded_at: datetime = Field(default_factory=datetime.now)
    verified: bool = False
    verification_notes: Optional[str] = None


class Integration(BaseModel):
    """Integration request/response"""
    integration_name: str
    request_id: str
    status: str
    response_data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)
    processing_time_ms: int


class BusinessRule(BaseModel):
    """Business rule definition"""
    rule_id: str
    rule_name: str
    condition: str
    action: str
    priority: int = 0
    enabled: bool = True


class ValidationResult(BaseModel):
    """Validation result"""
    field_name: str
    is_valid: bool
    error_message: Optional[str] = None
    suggestions: Optional[List[str]] = None
    ai_confidence: Optional[float] = None


class Application(BaseModel):
    """Main application model"""
    application_id: str
    account_type: AccountType
    status: ApplicationStatus = ApplicationStatus.DRAFT
    risk_level: RiskLevel = RiskLevel.LOW

    # Personal info
    personal_info: PersonalInfo
    employment_info: Optional[EmploymentInfo] = None

    # Documents
    documents: List[Document] = []

    # Workflow tracking
    current_step: int = 0
    completed_steps: List[str] = []

    # Integrations
    integrations: List[Integration] = []

    # Rules applied
    rules_applied: List[str] = []

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    submitted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # AI Analysis
    ai_fraud_score: float = 0.0
    ai_confidence: float = 0.0
    ai_notes: List[str] = []

    # Decision
    approval_decision: Optional[str] = None
    decision_reason: Optional[str] = None
    assigned_to: Optional[str] = None


class WorkflowStep(BaseModel):
    """Workflow step definition"""
    step_id: str
    step_name: str
    step_order: int
    required_fields: List[str]
    integrations_required: List[str] = []
    validation_rules: List[str] = []
    auto_advance: bool = True
    max_processing_time_seconds: int = 300


class WorkflowConfig(BaseModel):
    """Complete workflow configuration"""
    workflow_id: str
    workflow_name: str
    account_type: AccountType
    steps: List[WorkflowStep]
    business_rules: List[BusinessRule]
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: str = "system"


class DashboardMetrics(BaseModel):
    """Dashboard metrics"""
    total_applications: int
    applications_by_status: Dict[str, int]
    average_processing_time_hours: float
    automation_rate: float
    approval_rate: float
    fraud_detection_rate: float
    integration_success_rate: float
    applications_last_24h: int
    peak_hour: Optional[int] = None


class IntegrationConfig(BaseModel):
    """Integration configuration"""
    integration_id: str
    integration_name: str
    endpoint_url: str
    api_key_required: bool = True
    timeout_seconds: int = 30
    retry_count: int = 3
    enabled: bool = True
    mock_mode: bool = True
