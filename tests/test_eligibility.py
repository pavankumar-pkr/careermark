import pytest
from packages.rules.engine import DeterministicEligibilityEngine, EligibilityState

def test_eligible_condition():
    profile = {"education": "Computer Science and Engineering", "graduation_year": 2026, "age_max": 22}
    reqs = [
        {"type": "education", "operator": "in", "value": ["Computer Science and Engineering"], "human_readable": "CSE Degree"},
        {"type": "age_max", "operator": "<=", "value": 27, "human_readable": "Age <= 27"}
    ]
    engine = DeterministicEligibilityEngine(profile, reqs)
    res = engine.evaluate_all()
    assert res["final_state"] == EligibilityState.ELIGIBLE.value

def test_not_eligible_condition():
    profile = {"education": "Mechanical Engineering", "graduation_year": 2026, "age_max": 22}
    reqs = [
        {"type": "education", "operator": "in", "value": ["Computer Science and Engineering"], "human_readable": "CSE Degree"}
    ]
    engine = DeterministicEligibilityEngine(profile, reqs)
    res = engine.evaluate_all()
    assert res["final_state"] == EligibilityState.NOT_ELIGIBLE.value

def test_cannot_verify_condition():
    profile = {"graduation_year": 2026} # Missing education field
    reqs = [
        {"type": "education", "operator": "in", "value": ["Computer Science and Engineering"], "human_readable": "CSE Degree"}
    ]
    engine = DeterministicEligibilityEngine(profile, reqs)
    res = engine.evaluate_all()
    assert res["final_state"] == EligibilityState.CANNOT_VERIFY.value
