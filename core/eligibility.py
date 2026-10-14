import json

class DeterministicEligibilityEngine:
    @staticmethod
    def evaluate(profile, requirements):
        steps = []
        final_status = "eligible"
        
        for req in requirements:
            profile_val = getattr(profile, req.field_name, None)
            status = "unknown"
            
            if profile_val is None or str(profile_val).strip() == "":
                if final_status != "not_eligible": final_status = "cannot_verify"
                status = "cannot_verify"
            else:
                passed = False
                try:
                    if req.operator == '==': passed = str(profile_val).lower() == str(req.target_value).lower()
                    elif req.operator == '<=': passed = float(profile_val) <= float(req.target_value)
                    elif req.operator == '>=': passed = float(profile_val) >= float(req.target_value)
                    elif req.operator == 'IN': passed = str(profile_val) in json.loads(req.target_value)
                except ValueError:
                    if final_status != "not_eligible": final_status = "cannot_verify"
                    status = "cannot_verify"
                else:
                    status = "pass" if passed else "fail"
                    if not passed: final_status = "not_eligible"
            
            steps.append({
                "field": req.field_name.replace("_", " ").title(),
                "requirement_text": req.requirement_text,
                "rule": f"{req.field_name} {req.operator} {req.target_value}",
                "profile_val": profile_val if profile_val else "Not provided",
                "status": status
            })
            
        return final_status, steps
