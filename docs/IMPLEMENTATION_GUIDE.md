# Implementation Guide

## Banking Workflow Automation Platform

This guide provides step-by-step instructions for implementing and customizing the Banking Workflow Automation platform for your organization.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Customizing Workflows](#customizing-workflows)
5. [Business Rules Configuration](#business-rules-configuration)
6. [Integration Setup](#integration-setup)
7. [Deployment](#deployment)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git
- Basic understanding of REST APIs

### 5-Minute Setup

```bash
# 1. Clone the repository
git clone https://github.com/Turtles-AI-Lab/banking-workflow-automation.git
cd banking-workflow-automation

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the server
python backend/app.py

# 4. Open dashboard
# Navigate to http://localhost:8000 in your browser
```

That's it! The platform is now running with default configuration.

---

## Installation

### Development Environment

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import fastapi; print('FastAPI version:', fastapi.__version__)"
```

### Production Environment

```bash
# Install production dependencies
pip install -r requirements.txt

# Set environment variables
export ENVIRONMENT=production
export LOG_LEVEL=info

# Use production ASGI server
gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.app:app
```

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Application Settings
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=info

# API Settings
API_HOST=0.0.0.0
API_PORT=8000

# Database (for production)
DATABASE_URL=postgresql://user:pass@localhost:5432/banking_workflow

# Integration Settings
MOCK_INTEGRATIONS=true
INTEGRATION_TIMEOUT=30

# AI Settings
AI_FRAUD_THRESHOLD=0.6
AI_CONFIDENCE_THRESHOLD=0.85
```

### Application Configuration

Edit `backend/config.py` (create if needed):

```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Banking Workflow Automation"
    environment: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Integration settings
    mock_integrations: bool = True
    integration_timeout: int = 30

    # AI settings
    ai_fraud_threshold: float = 0.6
    ai_confidence_threshold: float = 0.85

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## Customizing Workflows

### Creating a New Workflow

1. **Define Workflow Steps**

```python
from models import WorkflowConfig, WorkflowStep, AccountType

custom_workflow = WorkflowConfig(
    workflow_id="wf_custom_business",
    workflow_name="Custom Business Account Workflow",
    account_type=AccountType.BUSINESS_CHECKING,
    steps=[
        WorkflowStep(
            step_id="business_info",
            step_name="Business Information",
            step_order=1,
            required_fields=["business_name", "ein", "business_type"],
            validation_rules=["ein_format", "business_verification"]
        ),
        WorkflowStep(
            step_id="owner_verification",
            step_name="Owner Verification",
            step_order=2,
            required_fields=["owner_ssn", "ownership_percentage"],
            integrations_required=["identity_verification", "background_check"]
        ),
        WorkflowStep(
            step_id="business_verification",
            step_name="Business Verification",
            step_order=3,
            integrations_required=["business_registry", "tax_verification"],
            auto_advance=True
        ),
        WorkflowStep(
            step_id="approval",
            step_name="Final Approval",
            step_order=4,
            auto_advance=False
        )
    ],
    business_rules=[]  # Add custom rules
)
```

2. **Register Workflow**

```python
# In app.py
workflows_db["custom_business"] = custom_workflow
```

### Modifying Existing Workflows

To modify the standard personal checking workflow:

```python
# Get existing workflow
workflow = workflows_db["wf_personal_checking"]

# Add a new step
new_step = WorkflowStep(
    step_id="additional_verification",
    step_name="Additional Verification",
    step_order=3,
    integrations_required=["enhanced_verification"],
    auto_advance=True
)

# Insert at position
workflow.steps.insert(2, new_step)

# Update step order
for i, step in enumerate(workflow.steps):
    step.step_order = i + 1
```

---

## Business Rules Configuration

### Understanding Rule Structure

Each business rule consists of:
- **Rule ID**: Unique identifier
- **Rule Name**: Human-readable name
- **Condition**: Boolean expression to evaluate
- **Action**: What to do when condition is true
- **Priority**: Execution order (higher = first)

### Creating Custom Rules

```python
from models import BusinessRule

# Example: High-value transaction rule
high_value_rule = BusinessRule(
    rule_id="HIGH_INITIAL_DEPOSIT",
    rule_name="High Initial Deposit Verification",
    condition="initial_deposit > 10000",
    action="require_source_of_funds",
    priority=85,
    enabled=True
)

# Add via API
POST /rules
{
    "rule_id": "HIGH_INITIAL_DEPOSIT",
    "rule_name": "High Initial Deposit Verification",
    "condition": "initial_deposit > 10000",
    "action": "require_source_of_funds",
    "priority": 85,
    "enabled": true
}
```

### Common Rule Examples

**1. Age-Based Routing**
```python
BusinessRule(
    rule_id="SENIOR_CITIZEN_REVIEW",
    rule_name="Senior Citizen Enhanced Review",
    condition="age > 80",
    action="assign_senior_specialist",
    priority=75
)
```

**2. Geographic Risk**
```python
BusinessRule(
    rule_id="HIGH_RISK_STATE",
    rule_name="High Risk State Verification",
    condition="state in ['NY', 'FL', 'CA']",
    action="enhanced_verification",
    priority=70
)
```

**3. Product-Specific Rules**
```python
BusinessRule(
    rule_id="BUSINESS_ACCOUNT_EIN",
    rule_name="Business Account Requires EIN",
    condition="account_type.startswith('business')",
    action="require_ein_verification",
    priority=95
)
```

### Rule Condition Syntax

Supported operators:
- Comparison: `<`, `>`, `<=`, `>=`, `==`, `!=`
- Logical: `and`, `or`, `not`
- Membership: `in`, `not in`
- String: `startswith`, `endswith`, `contains`

Variables available:
- `age` - Calculated age
- `account_type` - Account type string
- `annual_income` - Income amount
- `citizenship` - Citizenship status
- `ai_fraud_score` - AI fraud score (0-1)
- `risk_score` - Calculated risk score (0-100)

---

## Integration Setup

### Mock Mode (Default)

Mock mode simulates external APIs with realistic responses.

```python
from integrations import MockIntegrationService

# Initialize with mock mode
integration_service = MockIntegrationService(mock_mode=True)

# Use mock integrations
result = await integration_service.verify_identity(personal_info)
```

### Production Integration Setup

1. **Create Integration Configuration**

```python
from models import IntegrationConfig

identity_config = IntegrationConfig(
    integration_id="identity_verification_prod",
    integration_name="ID.me Production",
    endpoint_url="https://api.id.me/v1/verify",
    api_key_required=True,
    timeout_seconds=30,
    retry_count=3,
    enabled=True,
    mock_mode=False
)
```

2. **Implement Real Integration**

```python
async def verify_identity_production(self, personal_info: Dict[str, Any]) -> Integration:
    """Real identity verification integration"""

    headers = {
        "Authorization": f"Bearer {self.api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "first_name": personal_info["first_name"],
        "last_name": personal_info["last_name"],
        "ssn": personal_info["ssn"],
        "date_of_birth": personal_info["date_of_birth"]
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            self.config.endpoint_url,
            headers=headers,
            json=payload,
            timeout=self.config.timeout_seconds
        )

    # Process response
    return self._process_identity_response(response.json())
```

3. **Configure API Credentials**

```env
# .env file
IDENTITY_VERIFICATION_API_KEY=your_api_key_here
CREDIT_BUREAU_API_KEY=your_api_key_here
KYC_AML_API_KEY=your_api_key_here
```

### Supported Integration Providers

| Service Type | Recommended Providers | API Documentation |
|--------------|----------------------|-------------------|
| Identity Verification | ID.me, Socure, Jumio | Provider-specific |
| Credit Bureau | Experian, TransUnion, Equifax | https://developer.experian.com |
| KYC/AML | ComplyAdvantage, Refinitiv | https://www.complyadvantage.com/developers |
| Document OCR | AWS Textract, Google Vision | https://aws.amazon.com/textract |
| Fraud Detection | Sift, Forter, Kount | https://developers.sift.com |

---

## Deployment

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY docs/ ./docs/

EXPOSE 8000

CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build image
docker build -t banking-workflow-automation .

# Run container
docker run -p 8000:8000 banking-workflow-automation
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://postgres:password@db:5432/banking_workflow
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:14
    environment:
      POSTGRES_DB: banking_workflow
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

### Cloud Deployment (AWS)

**Using AWS ECS:**

```bash
# 1. Build and push Docker image to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker tag banking-workflow-automation:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/banking-workflow:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/banking-workflow:latest

# 2. Create ECS task definition
# 3. Create ECS service
# 4. Configure load balancer
```

---

## Troubleshooting

### Common Issues

**1. Import Errors**

```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
```bash
pip install -r requirements.txt
```

**2. Port Already in Use**

```
ERROR: Address already in use
```

**Solution:**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <pid> /F

# Mac/Linux
lsof -i :8000
kill -9 <pid>

# Or use different port
python backend/app.py --port 8001
```

**3. CORS Errors**

```
Access to fetch at 'http://localhost:8000' has been blocked by CORS policy
```

**Solution:** Already configured in `app.py`, but verify:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**4. Integration Timeouts**

```
TimeoutException: Integration request exceeded timeout
```

**Solution:** Increase timeout in config:
```python
integration_config.timeout_seconds = 60
```

### Debug Mode

Enable detailed logging:

```python
# In app.py
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Health Check

Test if the API is running:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "applications_count": 0,
  "workflows_count": 1,
  "rules_count": 8
}
```

---

## Next Steps

1. ✅ Review [ARCHITECTURE.md](./ARCHITECTURE.md) for system design
2. ✅ Check [API_REFERENCE.md](./API_REFERENCE.md) for endpoint details
3. ✅ Customize workflows for your use case
4. ✅ Configure business rules
5. ✅ Set up production integrations
6. ✅ Deploy to staging environment
7. ✅ Conduct user acceptance testing
8. ✅ Deploy to production

---

## Support

For questions or issues:
- GitHub Issues: https://github.com/Turtles-AI-Lab/banking-workflow-automation/issues
- Email: jgreenia@jandraisolutions.com
- LinkedIn: https://linkedin.com/in/james-greenia-535799149

---

**Document Version:** 1.0
**Last Updated:** 2025-10-02
**Author:** James Greenia
