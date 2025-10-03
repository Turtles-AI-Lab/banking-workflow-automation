"""
Business Rules Engine
Evaluates configurable business rules for workflow routing and validation
"""
from typing import List, Dict, Any, Tuple
from models import Application, BusinessRule, RiskLevel, AccountType
import re
from datetime import datetime, timedelta


class RulesEngine:
    """Business rules processor"""

    def __init__(self):
        self.rules = self._load_default_rules()

    def _load_default_rules(self) -> List[BusinessRule]:
        """Load default business rules"""
        return [
            BusinessRule(
                rule_id="AGE_VERIFICATION",
                rule_name="Age Verification for Account Type",
                condition="age < 18 and account_type != 'minor_account'",
                action="require_cosigner",
                priority=100
            ),
            BusinessRule(
                rule_id="HIGH_RISK_SSN",
                rule_name="High Risk SSN Pattern Detection",
                condition="ssn_sequential or ssn_repetitive",
                action="flag_manual_review",
                priority=90
            ),
            BusinessRule(
                rule_id="HIGH_INCOME_VERIFICATION",
                rule_name="High Income Requires Additional Verification",
                condition="annual_income > 250000",
                action="require_income_documentation",
                priority=80
            ),
            BusinessRule(
                rule_id="BUSINESS_ACCOUNT_EIN",
                rule_name="Business Account Requires EIN",
                condition="account_type.startswith('business') and not ein_provided",
                action="require_ein",
                priority=95
            ),
            BusinessRule(
                rule_id="FOREIGN_ADDRESS",
                rule_name="Foreign Address Enhanced Due Diligence",
                condition="citizenship != 'US' or foreign_address",
                action="enhanced_kyc",
                priority=85
            ),
            BusinessRule(
                rule_id="CREDIT_CHECK_THRESHOLD",
                rule_name="Credit Check for Overdraft Protection",
                condition="overdraft_requested",
                action="require_credit_check",
                priority=70
            ),
            BusinessRule(
                rule_id="AUTO_APPROVE_LOW_RISK",
                rule_name="Auto-Approve Low Risk Applications",
                condition="risk_score < 20 and all_verifications_passed",
                action="auto_approve",
                priority=50
            ),
            BusinessRule(
                rule_id="SUSPICIOUS_PATTERN",
                rule_name="Suspicious Pattern Detection",
                condition="ai_fraud_score > 0.7",
                action="flag_fraud_review",
                priority=100
            ),
        ]

    def calculate_age(self, date_of_birth: str) -> int:
        """Calculate age from date of birth"""
        try:
            dob = datetime.strptime(date_of_birth, "%Y-%m-%d")
            today = datetime.now()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            return age
        except (ValueError, TypeError, AttributeError) as e:
            # Log the error for debugging but return safe default
            print(f"Error calculating age from DOB '{date_of_birth}': {type(e).__name__}")
            return 0

    def is_ssn_suspicious(self, ssn: str) -> Tuple[bool, bool]:
        """Check for suspicious SSN patterns"""
        # Remove dashes
        ssn_clean = ssn.replace("-", "").replace(" ", "")

        # Check for sequential numbers
        sequential = False
        if len(ssn_clean) == 9:
            digits = [int(d) for d in ssn_clean]
            sequential_count = 0
            for i in range(len(digits) - 1):
                if digits[i+1] == digits[i] + 1:
                    sequential_count += 1
            sequential = sequential_count >= 5

        # Check for repetitive patterns
        repetitive = bool(re.match(r'^(\d)\1{8}$', ssn_clean)) or \
                    bool(re.match(r'^(\d{3})\1{2}$', ssn_clean))

        return sequential, repetitive

    def evaluate_application(self, application: Application) -> Dict[str, Any]:
        """Evaluate all rules against an application"""

        # Calculate derived fields
        age = self.calculate_age(application.personal_info.date_of_birth)
        ssn_sequential, ssn_repetitive = self.is_ssn_suspicious(application.personal_info.ssn)

        annual_income = application.employment_info.annual_income if application.employment_info else 0
        citizenship = application.personal_info.citizenship
        account_type = application.account_type.value

        # Build context
        context = {
            "age": age,
            "ssn_sequential": ssn_sequential,
            "ssn_repetitive": ssn_repetitive,
            "annual_income": annual_income,
            "citizenship": citizenship,
            "account_type": account_type,
            "foreign_address": citizenship != "US",
            "ein_provided": False,  # Would check documents
            "overdraft_requested": False,  # Would be in form data
            "ai_fraud_score": application.ai_fraud_score,
            "risk_score": self._calculate_risk_score(application),
            "all_verifications_passed": len(application.integrations) > 0
        }

        # Evaluate rules
        triggered_rules = []
        actions_required = []

        for rule in sorted(self.rules, key=lambda r: r.priority, reverse=True):
            if not rule.enabled:
                continue

            if self._evaluate_condition(rule.condition, context):
                triggered_rules.append(rule.rule_id)
                actions_required.append(rule.action)

        # Determine risk level
        risk_level = self._determine_risk_level(context, triggered_rules)

        # Determine next action
        next_action = self._determine_next_action(actions_required, application)

        return {
            "triggered_rules": triggered_rules,
            "actions_required": actions_required,
            "risk_level": risk_level,
            "next_action": next_action,
            "context": context,
            "can_auto_approve": "auto_approve" in actions_required and len(actions_required) == 1
        }

    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Safely evaluate a condition string using allowlist-based parser"""
        try:
            # Sanitize condition string to prevent injection
            if len(condition) > 500:
                print(f"Condition too long: {len(condition)} chars")
                return False

            # Remove any potentially dangerous characters
            dangerous_chars = [';', '(', ')', '[', ']', '{', '}', '\\', '`', '$']
            if any(char in condition for char in dangerous_chars):
                print(f"Dangerous characters in condition: {condition}")
                return False

            # Handle simple comparisons with strict parsing
            if "<" in condition and ">" not in condition:
                parts = condition.split("<")
                if len(parts) == 2:
                    left = parts[0].strip()
                    right = parts[1].strip()

                    # Validate left side is in context
                    if left not in context:
                        return False

                    left_val = context.get(left, 0)
                    try:
                        right_val = float(right)
                        return float(left_val) < right_val
                    except (ValueError, TypeError) as e:
                        print(f"Error parsing comparison: {type(e).__name__}")
                        return False

            if ">" in condition and "<" not in condition:
                parts = condition.split(">")
                if len(parts) == 2:
                    left = parts[0].strip()
                    right = parts[1].strip()

                    # Validate left side is in context
                    if left not in context:
                        return False

                    left_val = context.get(left, 0)
                    try:
                        right_val = float(right)
                        return float(left_val) > right_val
                    except (ValueError, TypeError) as e:
                        print(f"Error parsing comparison: {type(e).__name__}")
                        return False

            # Handle boolean conditions
            if " and " in condition:
                conditions = condition.split(" and ")
                return all(self._evaluate_condition(c.strip(), context) for c in conditions)

            if " or " in condition:
                conditions = condition.split(" or ")
                return any(self._evaluate_condition(c.strip(), context) for c in conditions)

            # Handle string comparisons with allowlist
            if "!=" in condition:
                parts = condition.split("!=")
                if len(parts) == 2:
                    left = parts[0].strip()
                    right = parts[1].strip().strip("'\"")
                    if left in context:
                        return str(context.get(left)) != right
                    return False

            if "==" in condition or ".startswith(" in condition:
                # These require more complex parsing - just return False for safety
                # In production, use a proper expression parser library
                return False

            # Handle direct boolean lookup with validation
            var_name = condition.strip()
            if var_name in context:
                return bool(context.get(var_name, False))

            return False

        except (KeyError, ValueError, TypeError, AttributeError) as e:
            print(f"Error evaluating condition '{condition}': {type(e).__name__}")
            return False
        except Exception as e:
            # Catch any unexpected errors
            print(f"Unexpected error evaluating condition '{condition}': {type(e).__name__}")
            return False

    def _calculate_risk_score(self, application: Application) -> float:
        """Calculate overall risk score (0-100)"""
        score = 0.0

        # AI fraud score contribution
        score += application.ai_fraud_score * 40

        # Age factor
        age = self.calculate_age(application.personal_info.date_of_birth)
        if age < 21:
            score += 10
        elif age > 75:
            score += 15

        # Citizenship
        if application.personal_info.citizenship != "US":
            score += 20

        # Income verification
        if application.employment_info and application.employment_info.annual_income:
            if application.employment_info.annual_income > 500000:
                score += 10
            elif application.employment_info.annual_income < 15000:
                score += 15

        # SSN patterns
        ssn_sequential, ssn_repetitive = self.is_ssn_suspicious(application.personal_info.ssn)
        if ssn_sequential or ssn_repetitive:
            score += 30

        return min(score, 100.0)

    def _determine_risk_level(self, context: Dict[str, Any], triggered_rules: List[str]) -> RiskLevel:
        """Determine risk level based on context and rules"""
        risk_score = context.get("risk_score", 0)

        if risk_score >= 70 or "SUSPICIOUS_PATTERN" in triggered_rules:
            return RiskLevel.CRITICAL
        elif risk_score >= 50 or "HIGH_RISK_SSN" in triggered_rules:
            return RiskLevel.HIGH
        elif risk_score >= 30 or len(triggered_rules) >= 3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _determine_next_action(self, actions: List[str], application: Application) -> str:
        """Determine next workflow action"""
        if not actions:
            return "proceed_to_next_step"

        # Priority-based action determination
        if "flag_fraud_review" in actions:
            return "manual_fraud_review"
        elif "flag_manual_review" in actions:
            return "manual_review"
        elif "enhanced_kyc" in actions:
            return "enhanced_kyc_check"
        elif "require_credit_check" in actions:
            return "credit_check"
        elif "require_cosigner" in actions:
            return "require_cosigner_info"
        elif "auto_approve" in actions:
            return "auto_approve"
        else:
            return "proceed_to_next_step"

    def add_rule(self, rule: BusinessRule):
        """Add a new business rule"""
        self.rules.append(rule)

    def remove_rule(self, rule_id: str):
        """Remove a business rule"""
        self.rules = [r for r in self.rules if r.rule_id != rule_id]

    def get_all_rules(self) -> List[BusinessRule]:
        """Get all configured rules"""
        return self.rules
