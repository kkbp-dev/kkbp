"""Compare two scene summaries. No bpy: runs on the host and in unit tests."""

import math

# Keys that describe the run, not the Character. They are kept in snapshots for reference only.
IGNORED_KEYS = frozenset({"run"})

DEFAULT_TOLERANCE = 1e-3


def differences(expected, actual, tolerance=DEFAULT_TOLERANCE, path="", limit=200):
    """Return human-readable differences between two summaries, at most `limit` of them. `tolerance`
    is the absolute tolerance for numbers, or a function of a value's path that returns it (the
    snapshot check's physics tolerance, physics.py)."""
    out = []
    if not callable(tolerance):
        tolerance = (lambda value: lambda _: value)(tolerance)
    _diff(expected, actual, tolerance, path, out, limit)
    return out


def _diff(expected, actual, tolerance, path, out, limit):
    if len(out) >= limit:
        return
    if isinstance(expected, dict) and isinstance(actual, dict):
        for key in sorted(set(expected) | set(actual)):
            if key in IGNORED_KEYS and not path:
                continue
            sub = f"{path}/{key}"
            if key not in actual:
                out.append(f"{sub}: missing")
            elif key not in expected:
                out.append(f"{sub}: unexpected")
            else:
                _diff(expected[key], actual[key], tolerance, sub, out, limit)
            if len(out) >= limit:
                return
    elif isinstance(expected, list) and isinstance(actual, list):
        if _is_vector(expected) and _is_vector(actual) and len(expected) == len(actual):
            if any(not math.isclose(e, a, abs_tol=tolerance(path)) for e, a in zip(expected, actual)):
                out.append(f"{path}: {expected} != {actual}")
        elif _all_strings(expected) and _all_strings(actual) and expected != actual:
            missing = [x for x in expected if x not in actual]
            extra = [x for x in actual if x not in expected]
            if missing or extra:
                out.append(f"{path}: missing {missing[:10]}, unexpected {extra[:10]}")
            else:
                out.append(f"{path}: same items, different order")
        elif len(expected) != len(actual):
            out.append(f"{path}: length {len(expected)} != {len(actual)}")
        else:
            for i, (e, a) in enumerate(zip(expected, actual)):
                _diff(e, a, tolerance, f"{path}[{i}]", out, limit)
    elif _is_number(expected) and _is_number(actual):
        if isinstance(expected, bool) or isinstance(actual, bool) or isinstance(expected, int) and isinstance(actual, int):
            if expected != actual:
                out.append(f"{path}: {expected!r} != {actual!r}")
        elif not math.isclose(expected, actual, abs_tol=tolerance(path)):
            out.append(f"{path}: {expected!r} != {actual!r}")
    elif expected != actual:
        out.append(f"{path}: {expected!r} != {actual!r}")


def _is_number(value):
    return isinstance(value, (int, float))


def _is_vector(values):
    return bool(values) and all(_is_number(v) and not isinstance(v, bool) for v in values)


def _all_strings(values):
    return all(isinstance(v, str) for v in values)
