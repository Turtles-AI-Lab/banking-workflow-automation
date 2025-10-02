"""
AI-Powered Validation Module
Uses pattern matching and heuristics to simulate AI validation
In production, this would integrate with actual LLM APIs
"""
from typing import List, Dict, Any
from models import Application, ValidationResult, PersonalInfo
import re
from datetime import datetime


class AIValidator:
    """AI-powered validation engine"""

    def __init__(self):
        self.fraud_patterns = self._load_fraud_patterns()

    def _load_fraud_patterns(self) -> List[Dict[str, Any]]:
        """Load known fraud patterns"""
        return [
            {
                "pattern": "sequential_ssn",
                "weight": 0.3,
                "description": "SSN contains sequential digits"
            },
            {
                "pattern": "repetitive_ssn",
                "weight": 0.3,
                "description": "SSN contains repetitive patterns"
            },
            {
                "pattern": "fake_email_domain",
                "weight": 0.15,
                "description": "Temporary email domain detected"
            },
            {
                "pattern": "impossible_age",
                "weight": 0.4,
                "description": "Age outside acceptable range"
            },
            {
                "pattern": "suspicious_name",
                "weight": 0.2,
                "description": "Name contains suspicious patterns"
            },
            {
                "pattern": "invalid_phone_format",
                "weight": 0.1,
                "description": "Phone number format is invalid"
            },
            {
                "pattern": "inconsistent_address",
                "weight": 0.15,
                "description": "Address appears inconsistent"
            }
        ]

    def validate_personal_info(self, personal_info: PersonalInfo) -> List[ValidationResult]:
        """Validate personal information fields"""
        results = []

        # Validate name
        results.append(self._validate_name(personal_info.first_name, "first_name"))
        results.append(self._validate_name(personal_info.last_name, "last_name"))

        # Validate email
        results.append(self._validate_email(personal_info.email))

        # Validate phone
        results.append(self._validate_phone(personal_info.phone))

        # Validate date of birth
        results.append(self._validate_dob(personal_info.date_of_birth))

        # Validate SSN
        results.append(self._validate_ssn(personal_info.ssn))

        # Validate address
        results.append(self._validate_address(personal_info))

        # Validate zip code
        results.append(self._validate_zip(personal_info.zip_code, personal_info.state))

        return results

    def _validate_name(self, name: str, field_name: str) -> ValidationResult:
        """Validate name field"""
        if not name or len(name) < 2:
            return ValidationResult(
                field_name=field_name,
                is_valid=False,
                error_message=f"{field_name.replace('_', ' ').title()} must be at least 2 characters",
                ai_confidence=0.95
            )

        # Check for numbers in name
        if re.search(r'\d', name):
            return ValidationResult(
                field_name=field_name,
                is_valid=False,
                error_message=f"{field_name.replace('_', ' ').title()} should not contain numbers",
                ai_confidence=0.98
            )

        # Check for suspicious patterns
        suspicious_patterns = ['test', 'fake', 'xxxx', 'aaaa', 'none', 'null']
        if any(pattern in name.lower() for pattern in suspicious_patterns):
            return ValidationResult(
                field_name=field_name,
                is_valid=False,
                error_message=f"{field_name.replace('_', ' ').title()} appears to be a test value",
                suggestions=["Please provide your real name"],
                ai_confidence=0.85
            )

        return ValidationResult(
            field_name=field_name,
            is_valid=True,
            ai_confidence=0.92
        )

    def _validate_email(self, email: str) -> ValidationResult:
        """Validate email address"""
        # Check for temporary email domains
        temp_domains = ['tempmail.com', 'guerrillamail.com', 'mailinator.com',
                        '10minutemail.com', 'throwaway.email', 'fakeinbox.com']

        email_domain = email.split('@')[1] if '@' in email else ''

        if email_domain in temp_domains:
            return ValidationResult(
                field_name="email",
                is_valid=False,
                error_message="Temporary email addresses are not allowed",
                suggestions=["Please use a permanent email address"],
                ai_confidence=0.99
            )

        # Basic format validation (pydantic already does this, but adding AI confidence)
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return ValidationResult(
                field_name="email",
                is_valid=False,
                error_message="Email format is invalid",
                ai_confidence=0.97
            )

        return ValidationResult(
            field_name="email",
            is_valid=True,
            ai_confidence=0.94
        )

    def _validate_phone(self, phone: str) -> ValidationResult:
        """Validate phone number"""
        # Remove common formatting
        phone_clean = re.sub(r'[\s\-\(\)]', '', phone)

        # Check length
        if len(phone_clean) != 10:
            return ValidationResult(
                field_name="phone",
                is_valid=False,
                error_message="Phone number must be 10 digits",
                suggestions=["Format: (123) 456-7890 or 123-456-7890"],
                ai_confidence=0.96
            )

        # Check for invalid patterns
        if re.match(r'^(\d)\1{9}$', phone_clean):  # All same digit
            return ValidationResult(
                field_name="phone",
                is_valid=False,
                error_message="Phone number appears invalid (repeated digits)",
                ai_confidence=0.98
            )

        # Check area code
        invalid_area_codes = ['000', '555', '999']
        if phone_clean[:3] in invalid_area_codes:
            return ValidationResult(
                field_name="phone",
                is_valid=False,
                error_message="Invalid area code",
                ai_confidence=0.93
            )

        return ValidationResult(
            field_name="phone",
            is_valid=True,
            ai_confidence=0.91
        )

    def _validate_dob(self, dob: str) -> ValidationResult:
        """Validate date of birth"""
        try:
            dob_date = datetime.strptime(dob, "%Y-%m-%d")
            today = datetime.now()

            # Calculate age
            age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))

            # Check for impossible ages
            if age < 0:
                return ValidationResult(
                    field_name="date_of_birth",
                    is_valid=False,
                    error_message="Date of birth cannot be in the future",
                    ai_confidence=0.99
                )

            if age > 120:
                return ValidationResult(
                    field_name="date_of_birth",
                    is_valid=False,
                    error_message="Date of birth appears invalid (age > 120)",
                    ai_confidence=0.98
                )

            if age < 13:
                return ValidationResult(
                    field_name="date_of_birth",
                    is_valid=False,
                    error_message="Must be at least 13 years old",
                    suggestions=["Minor accounts require a co-signer"],
                    ai_confidence=0.95
                )

            return ValidationResult(
                field_name="date_of_birth",
                is_valid=True,
                ai_confidence=0.96
            )

        except ValueError:
            return ValidationResult(
                field_name="date_of_birth",
                is_valid=False,
                error_message="Invalid date format",
                suggestions=["Use format: YYYY-MM-DD"],
                ai_confidence=0.99
            )

    def _validate_ssn(self, ssn: str) -> ValidationResult:
        """Validate Social Security Number"""
        # Remove formatting
        ssn_clean = ssn.replace("-", "").replace(" ", "")

        # Check length
        if len(ssn_clean) != 9:
            return ValidationResult(
                field_name="ssn",
                is_valid=False,
                error_message="SSN must be 9 digits",
                suggestions=["Format: XXX-XX-XXXX"],
                ai_confidence=0.98
            )

        # Check for invalid patterns
        invalid_ssns = ['000000000', '111111111', '222222222', '333333333',
                       '444444444', '555555555', '666666666', '777777777',
                       '888888888', '999999999', '123456789']

        if ssn_clean in invalid_ssns:
            return ValidationResult(
                field_name="ssn",
                is_valid=False,
                error_message="SSN appears invalid",
                ai_confidence=0.99
            )

        # Check for area number 000 or 666
        if ssn_clean[:3] in ['000', '666']:
            return ValidationResult(
                field_name="ssn",
                is_valid=False,
                error_message="Invalid SSN area number",
                ai_confidence=0.97
            )

        return ValidationResult(
            field_name="ssn",
            is_valid=True,
            ai_confidence=0.88
        )

    def _validate_address(self, personal_info: PersonalInfo) -> ValidationResult:
        """Validate address fields"""
        # Check for PO Box (some banks don't allow)
        if re.search(r'\bP\.?O\.?\s*BOX\b', personal_info.address_line1, re.IGNORECASE):
            return ValidationResult(
                field_name="address",
                is_valid=False,
                error_message="PO Box addresses not accepted for account opening",
                suggestions=["Please provide a physical street address"],
                ai_confidence=0.90
            )

        # Check for minimum address length
        if len(personal_info.address_line1) < 5:
            return ValidationResult(
                field_name="address",
                is_valid=False,
                error_message="Address appears too short",
                ai_confidence=0.85
            )

        return ValidationResult(
            field_name="address",
            is_valid=True,
            ai_confidence=0.87
        )

    def _validate_zip(self, zip_code: str, state: str) -> ValidationResult:
        """Validate ZIP code"""
        zip_clean = zip_code.replace("-", "").replace(" ", "")

        # Basic format check
        if not re.match(r'^\d{5}$', zip_clean) and not re.match(r'^\d{9}$', zip_clean):
            return ValidationResult(
                field_name="zip_code",
                is_valid=False,
                error_message="ZIP code must be 5 or 9 digits",
                suggestions=["Format: 12345 or 12345-6789"],
                ai_confidence=0.96
            )

        # State-ZIP correlation check (simplified)
        state_zip_ranges = {
            'CA': ('90', '96'),
            'NY': ('10', '14'),
            'FL': ('32', '34'),
            'TX': ('75', '79'),
        }

        if state in state_zip_ranges:
            start, end = state_zip_ranges[state]
            if not (start <= zip_clean[:2] <= end):
                return ValidationResult(
                    field_name="zip_code",
                    is_valid=False,
                    error_message=f"ZIP code doesn't match {state} state range",
                    suggestions=["Please verify your ZIP code and state"],
                    ai_confidence=0.75
                )

        return ValidationResult(
            field_name="zip_code",
            is_valid=True,
            ai_confidence=0.89
        )

    def calculate_fraud_score(self, application: Application) -> float:
        """Calculate AI fraud detection score (0.0 - 1.0)"""
        score = 0.0
        matches = []

        # Validate all fields first
        validation_results = self.validate_personal_info(application.personal_info)

        # Count validation failures
        failed_validations = [v for v in validation_results if not v.is_valid]
        score += len(failed_validations) * 0.1

        # Check SSN patterns
        ssn_clean = application.personal_info.ssn.replace("-", "")
        if re.match(r'^(\d)\1{8}$', ssn_clean):
            score += 0.3
            matches.append("repetitive_ssn")

        # Check for sequential SSN
        if self._is_sequential(ssn_clean):
            score += 0.3
            matches.append("sequential_ssn")

        # Check email domain
        email_domain = application.personal_info.email.split('@')[1]
        temp_domains = ['tempmail.com', 'guerrillamail.com', 'mailinator.com']
        if email_domain in temp_domains:
            score += 0.15
            matches.append("fake_email_domain")

        # Check age
        age = self._calculate_age(application.personal_info.date_of_birth)
        if age < 18 or age > 100:
            score += 0.2
            matches.append("unusual_age")

        # Check for test data patterns
        test_patterns = ['test', 'fake', 'example', 'demo']
        if any(pattern in application.personal_info.first_name.lower() for pattern in test_patterns):
            score += 0.25
            matches.append("suspicious_name")

        # Normalize score
        final_score = min(score, 1.0)

        # Add to application AI notes
        if matches:
            application.ai_notes.append(f"Fraud patterns detected: {', '.join(matches)}")

        return final_score

    def _is_sequential(self, number_str: str) -> bool:
        """Check if digits are sequential"""
        if len(number_str) < 3:
            return False

        digits = [int(d) for d in number_str]
        sequential_count = 0

        for i in range(len(digits) - 1):
            if digits[i+1] == digits[i] + 1:
                sequential_count += 1

        return sequential_count >= 4

    def _calculate_age(self, dob_str: str) -> int:
        """Calculate age from date of birth"""
        try:
            dob = datetime.strptime(dob_str, "%Y-%m-%d")
            today = datetime.now()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            return age
        except:
            return 0

    def generate_validation_report(self, application: Application) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        validation_results = self.validate_personal_info(application.personal_info)
        fraud_score = self.calculate_fraud_score(application)

        passed = [v for v in validation_results if v.is_valid]
        failed = [v for v in validation_results if not v.is_valid]

        average_confidence = sum(v.ai_confidence for v in validation_results) / len(validation_results) if validation_results else 0

        return {
            "overall_valid": len(failed) == 0,
            "validation_results": validation_results,
            "passed_count": len(passed),
            "failed_count": len(failed),
            "fraud_score": fraud_score,
            "average_confidence": average_confidence,
            "risk_level": "high" if fraud_score > 0.6 else "medium" if fraud_score > 0.3 else "low",
            "recommendations": self._generate_recommendations(failed, fraud_score)
        }

    def _generate_recommendations(self, failed_validations: List[ValidationResult], fraud_score: float) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []

        if fraud_score > 0.7:
            recommendations.append("Flag for immediate fraud review")
            recommendations.append("Require additional identity verification documents")

        if fraud_score > 0.4:
            recommendations.append("Perform enhanced KYC/AML checks")

        for validation in failed_validations:
            if validation.suggestions:
                recommendations.extend(validation.suggestions)

        if not recommendations:
            recommendations.append("Application passes AI validation checks")
            recommendations.append("Proceed with standard verification workflow")

        return recommendations
