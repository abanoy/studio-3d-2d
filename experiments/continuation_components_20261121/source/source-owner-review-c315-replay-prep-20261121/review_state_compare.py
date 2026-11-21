"""Unchanged committed owner-review saved-state comparison contract."""
import math
def compare(expected, actual, at="$", mismatches=None):
    if mismatches is None:
        mismatches = []
    if len(mismatches) >= 100:
        return mismatches
    if isinstance(expected, bool) or isinstance(actual, bool):
        equal = type(expected) is type(actual) and expected == actual
    elif isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        # JSON may decode a saved integer as a Godot float. IDs remain strings.
        equal = math.isfinite(expected) and math.isfinite(actual) and (expected == actual or (abs(expected) < 2**53 and abs(actual) < 2**53 and math.isclose(expected, actual, rel_tol=0, abs_tol=1e-12)))
    elif isinstance(expected, dict) and isinstance(actual, dict):
        if set(expected) != set(actual):
            mismatches.append({"at": at, "reason": "dictionary keys", "missing": sorted(set(expected) - set(actual)), "added": sorted(set(actual) - set(expected))})
        for key in sorted(set(expected) & set(actual)):
            compare(expected[key], actual[key], at + "." + key, mismatches)
        return mismatches
    elif isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            mismatches.append({"at": at, "reason": "array length", "expected": len(expected), "actual": len(actual)})
        for index, (left, right) in enumerate(zip(expected, actual)):
            compare(left, right, f"{at}[{index}]", mismatches)
        return mismatches
    else:
        equal = type(expected) is type(actual) and expected == actual
    if not equal:
        # Keep private art-derived metadata out of console logs; exact differences
        # stay in the owned evidence JSON, whose upload is not authorized.
        mismatches.append({"at": at, "reason": "value", "expected": expected, "actual": actual})
    return mismatches


