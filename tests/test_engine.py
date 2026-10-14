import pytest
from core.eligibility import DeterministicEligibilityEngine

class MockProfile:
    def __init__(self, degree, age):
        self.degree = degree
        self.age = age

class MockRequirement:
    def __init__(self, field, op, val):
        self.field_name = field
        self.operator = op
        self.target_value = val
        self.requirement_text = "Test Rule"

def test_engine_eligible():
    profile = MockProfile(degree="B.Tech", age=22)
    reqs = [MockRequirement("degree", "==", "B.Tech"), MockRequirement("age", "<=", "25")]
    status, steps = DeterministicEligibilityEngine.evaluate(profile, reqs)
    assert status == "eligible"

def test_engine_cannot_verify():
    profile = MockProfile(degree="B.Tech", age=None) # Missing Age
    reqs = [MockRequirement("degree", "==", "B.Tech"), MockRequirement("age", "<=", "25")]
    status, steps = DeterministicEligibilityEngine.evaluate(profile, reqs)
    assert status == "cannot_verify"
