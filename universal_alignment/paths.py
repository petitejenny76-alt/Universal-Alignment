"""Strict POSIX logical paths; OS containment still belongs to the executor."""
from fnmatch import fnmatchcase


def path_error(value, *, pattern=False):
    if not isinstance(value, str) or not value.startswith("/"):
        return "absolute_posix_path_required"
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        return "control_character_in_path"
    if "\\" in value or "%" in value:
        return "ambiguous_path_encoding"
    if "//" in value or any(p in {".", ".."} for p in value.split("/")):
        return "noncanonical_path"
    if value != "/" and value.endswith("/"):
        return "noncanonical_path"
    if not pattern and any(c in value for c in "*?[]"):
        return "wildcard_in_target"
    return None


def target_error(action):
    if action.target_kind == "path":
        return path_error(action.target)
    if action.target_kind != "resource":
        return "unknown_target_kind"
    if not isinstance(action.target, str) or not action.target:
        return "resource_target_required"
    if any(ord(c) < 32 or ord(c) == 127 for c in action.target):
        return "control_character_in_target"
    return None


def matches_permission(rule, action):
    """Case-sensitive matching on validated identifiers. Wildcards are recursive."""
    operation, separator, target = rule.partition(":")
    if not separator:
        return False
    return fnmatchcase(action.operation, operation) and fnmatchcase(action.target, target)
