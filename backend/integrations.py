"""
Mock Integration Layer
Simulates external API calls for identity verification, credit checks, and KYC/AML
"""
from typing import Dict, Any
from models import Integration
import random
import time
from datetime import datetime
import hashlib


class MockIntegrationService:
    """Mock integration service for external APIs"""

    def __init__(self, mock_mode: bool = True):
        self.mock_mode = mock_mode

    async def verify_identity(self, personal_info: Dict[str, Any]) -> Integration:
        """Mock identity verification service (e.g., ID.me, Socure)"""
        start_time = time.time()

        # Simulate processing delay
        await self._simulate_delay(1.0, 2.5)

        # Generate mock response
        request_id = self._generate_request_id("IDV")

        # Simulate verification logic
        verification_score = random.uniform(0.7, 1.0)
        is_verified = verification_score > 0.85

        response_data = {
            "status": "verified" if is_verified else "failed",
            "verification_score": round(verification_score, 2),
            "verification_method": "document_and_selfie",
            "identity_match": is_verified,
            "document_authentic": random.choice([True, False]) if not is_verified else True,
            "liveness_check": random.choice([True, False]) if not is_verified else True,
            "address_verified": is_verified,
            "ssn_verified": is_verified,
            "warnings": [] if is_verified else ["Document quality low", "Address mismatch"],
            "timestamp": datetime.now().isoformat()
        }

        processing_time = int((time.time() - start_time) * 1000)

        return Integration(
            integration_name="identity_verification",
            request_id=request_id,
            status="success" if is_verified else "failed",
            response_data=response_data,
            processing_time_ms=processing_time
        )

    async def check_credit(self, personal_info: Dict[str, Any]) -> Integration:
        """Mock credit check service (e.g., Experian, TransUnion)"""
        start_time = time.time()

        await self._simulate_delay(1.5, 3.0)

        request_id = self._generate_request_id("CRD")

        # Generate mock credit score
        credit_score = random.randint(550, 850)

        # Determine credit tier
        if credit_score >= 740:
            tier = "excellent"
        elif credit_score >= 670:
            tier = "good"
        elif credit_score >= 580:
            tier = "fair"
        else:
            tier = "poor"

        response_data = {
            "credit_score": credit_score,
            "credit_tier": tier,
            "credit_report_available": True,
            "delinquent_accounts": random.randint(0, 3) if credit_score < 650 else 0,
            "total_accounts": random.randint(3, 15),
            "credit_utilization": round(random.uniform(0.1, 0.9), 2),
            "bankruptcies": random.choice([0, 1]) if credit_score < 600 else 0,
            "foreclosures": 0,
            "inquiries_last_6_months": random.randint(0, 5),
            "oldest_account_years": random.randint(1, 20),
            "approved_for_overdraft": credit_score >= 650,
            "recommended_credit_limit": credit_score * 10 if credit_score >= 650 else 0,
            "timestamp": datetime.now().isoformat()
        }

        processing_time = int((time.time() - start_time) * 1000)

        return Integration(
            integration_name="credit_check",
            request_id=request_id,
            status="success",
            response_data=response_data,
            processing_time_ms=processing_time
        )

    async def kyc_aml_check(self, personal_info: Dict[str, Any]) -> Integration:
        """Mock KYC/AML screening (e.g., ComplyAdvantage, Refinitiv)"""
        start_time = time.time()

        await self._simulate_delay(2.0, 4.0)

        request_id = self._generate_request_id("KYC")

        # Simulate screening
        risk_score = random.uniform(0.0, 0.5)  # Most people are low risk
        is_clear = risk_score < 0.3

        matches = []
        if not is_clear:
            matches = [
                {
                    "type": "name_similarity",
                    "match_score": round(risk_score, 2),
                    "list": "OFAC" if risk_score > 0.4 else "PEP",
                    "details": "Partial name match requiring review"
                }
            ]

        response_data = {
            "status": "clear" if is_clear else "review_required",
            "risk_score": round(risk_score, 2),
            "watchlist_matches": matches,
            "sanctions_check": "pass" if is_clear else "review",
            "pep_check": "pass",
            "adverse_media": "none_found" if is_clear else "potential_match",
            "politically_exposed": False,
            "countries_associated": ["US"],
            "requires_enhanced_due_diligence": not is_clear,
            "screening_date": datetime.now().isoformat(),
            "timestamp": datetime.now().isoformat()
        }

        processing_time = int((time.time() - start_time) * 1000)

        return Integration(
            integration_name="kyc_aml_screening",
            request_id=request_id,
            status="success",
            response_data=response_data,
            processing_time_ms=processing_time
        )

    async def verify_document(self, document_data: Dict[str, Any]) -> Integration:
        """Mock document verification/OCR service"""
        start_time = time.time()

        await self._simulate_delay(1.0, 2.0)

        request_id = self._generate_request_id("DOC")

        # Simulate document processing
        confidence = random.uniform(0.85, 0.99)
        is_valid = confidence > 0.90

        response_data = {
            "document_type": document_data.get("type", "drivers_license"),
            "extracted_data": {
                "name": document_data.get("name", "John Doe"),
                "date_of_birth": document_data.get("dob", "1990-01-01"),
                "document_number": self._generate_request_id("DL"),
                "expiration_date": "2028-12-31",
                "address": document_data.get("address", "123 Main St")
            },
            "validation": {
                "is_valid": is_valid,
                "is_expired": False,
                "is_authentic": is_valid,
                "confidence_score": round(confidence, 2),
                "tampering_detected": not is_valid,
                "quality_score": round(random.uniform(0.8, 1.0), 2)
            },
            "warnings": [] if is_valid else ["Low image quality", "Potential tampering detected"],
            "timestamp": datetime.now().isoformat()
        }

        processing_time = int((time.time() - start_time) * 1000)

        return Integration(
            integration_name="document_verification",
            request_id=request_id,
            status="success" if is_valid else "review_required",
            response_data=response_data,
            processing_time_ms=processing_time
        )

    async def check_fraud_database(self, personal_info: Dict[str, Any]) -> Integration:
        """Mock fraud database check"""
        start_time = time.time()

        await self._simulate_delay(0.5, 1.5)

        request_id = self._generate_request_id("FRD")

        # Simulate fraud check
        fraud_indicators = random.randint(0, 3)
        is_clean = fraud_indicators == 0

        indicators = []
        if fraud_indicators > 0:
            possible_indicators = [
                "Multiple applications from same IP",
                "Phone number associated with fraud",
                "Email appears on blacklist",
                "Address linked to suspicious activity"
            ]
            indicators = random.sample(possible_indicators, fraud_indicators)

        response_data = {
            "status": "clear" if is_clean else "flagged",
            "fraud_score": fraud_indicators * 0.3,
            "indicators_found": fraud_indicators,
            "fraud_indicators": indicators,
            "previous_fraud_reports": fraud_indicators,
            "velocity_checks": {
                "applications_same_ip_24h": random.randint(0, 2),
                "applications_same_device_7d": random.randint(0, 3),
                "applications_same_email_30d": 1
            },
            "device_reputation": "trusted" if is_clean else "suspicious",
            "ip_reputation": "clean" if is_clean else "moderate_risk",
            "recommendation": "approve" if is_clean else "review",
            "timestamp": datetime.now().isoformat()
        }

        processing_time = int((time.time() - start_time) * 1000)

        return Integration(
            integration_name="fraud_database",
            request_id=request_id,
            status="success",
            response_data=response_data,
            processing_time_ms=processing_time
        )

    async def verify_employment(self, employment_info: Dict[str, Any]) -> Integration:
        """Mock employment verification service"""
        start_time = time.time()

        await self._simulate_delay(2.0, 3.5)

        request_id = self._generate_request_id("EMP")

        # Simulate employment verification
        verification_successful = random.choice([True, True, True, False])  # 75% success rate

        response_data = {
            "employment_verified": verification_successful,
            "employer_name": employment_info.get("employer", "Unknown"),
            "employment_status": "active" if verification_successful else "unable_to_verify",
            "position_verified": verification_successful,
            "income_verified": verification_successful,
            "length_of_employment_months": random.randint(6, 120) if verification_successful else None,
            "verification_method": "payroll_records" if verification_successful else "not_verified",
            "confidence": random.uniform(0.85, 0.99) if verification_successful else 0.0,
            "notes": "" if verification_successful else "Employer not found in database",
            "timestamp": datetime.now().isoformat()
        }

        processing_time = int((time.time() - start_time) * 1000)

        return Integration(
            integration_name="employment_verification",
            request_id=request_id,
            status="success" if verification_successful else "partial",
            response_data=response_data,
            processing_time_ms=processing_time
        )

    async def _simulate_delay(self, min_seconds: float, max_seconds: float):
        """Simulate API processing time"""
        import asyncio
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)

    def _generate_request_id(self, prefix: str) -> str:
        """Generate a unique request ID"""
        timestamp = str(int(time.time() * 1000))
        random_str = str(random.randint(1000, 9999))
        hash_input = f"{prefix}{timestamp}{random_str}"
        hash_output = hashlib.md5(hash_input.encode()).hexdigest()[:8]
        return f"{prefix}-{hash_output.upper()}"


class IntegrationOrchestrator:
    """Orchestrates multiple integration calls"""

    def __init__(self):
        self.integration_service = MockIntegrationService()

    async def run_standard_checks(self, application_data: Dict[str, Any]) -> Dict[str, Integration]:
        """Run standard verification checks"""
        results = {}

        # Run identity verification
        results["identity"] = await self.integration_service.verify_identity(
            application_data.get("personal_info", {})
        )

        # Run fraud database check
        results["fraud"] = await self.integration_service.check_fraud_database(
            application_data.get("personal_info", {})
        )

        # Run KYC/AML screening
        results["kyc_aml"] = await self.integration_service.kyc_aml_check(
            application_data.get("personal_info", {})
        )

        return results

    async def run_enhanced_checks(self, application_data: Dict[str, Any]) -> Dict[str, Integration]:
        """Run enhanced verification checks (for high-risk applications)"""
        results = await self.run_standard_checks(application_data)

        # Add credit check
        results["credit"] = await self.integration_service.check_credit(
            application_data.get("personal_info", {})
        )

        # Add employment verification if employment info provided
        if application_data.get("employment_info"):
            results["employment"] = await self.integration_service.verify_employment(
                application_data.get("employment_info", {})
            )

        return results

    def get_integration_summary(self, integrations: Dict[str, Integration]) -> Dict[str, Any]:
        """Generate summary of integration results"""
        total_integrations = len(integrations)
        successful = sum(1 for i in integrations.values() if i.status == "success")
        failed = sum(1 for i in integrations.values() if i.status == "failed")
        review_required = total_integrations - successful - failed

        avg_processing_time = sum(i.processing_time_ms for i in integrations.values()) / total_integrations if total_integrations > 0 else 0

        return {
            "total_integrations": total_integrations,
            "successful": successful,
            "failed": failed,
            "review_required": review_required,
            "success_rate": successful / total_integrations if total_integrations > 0 else 0,
            "average_processing_time_ms": int(avg_processing_time),
            "all_passed": failed == 0 and review_required == 0
        }
