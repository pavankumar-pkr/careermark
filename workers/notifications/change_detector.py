from typing import Dict, List, Any

class MaterialChangeDetector:
    """
    Compares historical versions of opportunity requirements to detect material changes.
    Never overwrites historical truth; triggers alerts for state flips.
    """
    @staticmethod
    def detect_material_changes(old_version: Dict[str, Any], new_version: Dict[str, Any]) -> List[str]:
        changes = []
        
        # 1. Check Deadline Changes
        if old_version.get("closing_date") != new_version.get("closing_date"):
            changes.append("CLOSING_DATE_CHANGED")
            
        # 2. Check Requirement Scope Changes
        old_reqs = {r.get('type'): r.get('value') for r in old_version.get("requirements", [])}
        new_reqs = {r.get('type'): r.get('value') for r in new_version.get("requirements", [])}
        
        if old_reqs != new_reqs:
            changes.append("ELIGIBILITY_REQUIREMENTS_CHANGED")
            
        return changes
