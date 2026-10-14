"""
CareerMark Deterministic Eligibility Engine (Mark 1)
Evaluates profile snapshots against structured requirements.
AI is strictly forbidden from overriding this engine.
"""
from enum import Enum
from typing import Dict, Any, List

class EligibilityState(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    CANNOT_VERIFY = "CANNOT_VERIFY"

class DeterministicEligibilityEngine:
    def __init__(self, profile_snapshot: Dict[str, Any], opportunity_requirements: List[Dict[str, Any]]):
        self.profile = profile_snapshot
        self.requirements = opportunity_requirements
        self.evaluations = []

    def evaluate_all(self) -> Dict[str, Any]:
        has_hard_fail = False
        has_unknown = False

        for req in self.requirements:
            res = self._evaluate_rule(req)
            self.evaluations.append(res)
            if res["state"] == EligibilityState.NOT_ELIGIBLE.value:
                has_hard_fail = True
            elif res["state"] == EligibilityState.CANNOT_VERIFY.value:
                has_unknown = True

        if has_hard_fail:
            final_state = EligibilityState.NOT_ELIGIBLE.value
        elif has_unknown:
            final_state = EligibilityState.CANNOT_VERIFY.value
        else:
            final_state = EligibilityState.ELIGIBLE.value

        return {
            "final_state": final_state,
            "evaluations": self.evaluations,
            "engine_version": "1.0.0"
        }

    def _evaluate_rule(self, req: Dict[str, Any]) -> Dict[str, Any]:
        r_type = req.get("type")
        operator = req.get("operator")
        expected = req.get("value")
        source_ref = req.get("source_ref", "Official Notification")
        user_val = self.profile.get(r_type)

        if user_val is None:
            return {
                "requirement": req.get("human_readable"),
                "state": EligibilityState.CANNOT_VERIFY.value,
                "reason": f"Profile field '{r_type}' is missing or not provided.",
                "evidence": source_ref,
                "user_value": None
            }

        if r_type == "education" and operator == "in":
            if user_val in expected:
                return {
                    "requirement": req.get("human_readable"),
                    "state": EligibilityState.ELIGIBLE.value,
                    "reason": f"Degree/discipline '{user_val}' matches approved qualifications.",
                    "evidence": source_ref,
                    "user_value": user_val
                }
            return {
                "requirement": req.get("human_readable"),
                "state": EligibilityState.NOT_ELIGIBLE.value,
                "reason": f"Discipline '{user_val}' is not in approved list ({', '.join(expected)}).",
                "evidence": source_ref,
                "user_value": user_val
            }

        if r_type == "graduation_year" and operator == "<=":
            if int(user_val) <= int(expected):
                return {
                    "requirement": req.get("human_readable"),
                    "state": EligibilityState.ELIGIBLE.value,
                    "reason": f"Graduation year ({user_val}) meets cutoff limit ({expected}).",
                    "evidence": source_ref,
                    "user_value": user_val
                }
            return {
                "requirement": req.get("human_readable"),
                "state": EligibilityState.NOT_ELIGIBLE.value,
                "reason": f"Graduation year ({user_val}) exceeds cutoff threshold of {expected}.",
                "evidence": source_ref,
                "user_value": user_val
            }

        if r_type == "age_max" and operator == "<=":
            if int(user_val) <= int(expected):
                return {
                    "requirement": req.get("human_readable"),
                    "state": EligibilityState.ELIGIBLE.value,
                    "reason": f"Age ({user_val}) is within maximum cutoff limit of {expected}.",
                    "evidence": source_ref,
                    "user_value": user_val
                }
            return {
                "requirement": req.get("human_readable"),
                "state": EligibilityState.NOT_ELIGIBLE.value,
                "reason": f"Age ({user_val}) exceeds upper age boundary of {expected}.",
                "evidence": source_ref,
                "user_value": user_val
            }

        return {
            "requirement": req.get("human_readable"),
            "state": EligibilityState.CANNOT_VERIFY.value,
            "reason": "Unsupported or ambiguous requirement operator.",
            "evidence": source_ref,
            "user_value": user_val
        }
