from dataclasses import dataclass
from fnmatch import fnmatchcase
from .paths import path_error


@dataclass(frozen=True)
class MonitorResult:
    ok: bool
    reason: str = ""


class RiskMonitor:
    LEVELS = {"low": 0, "medium": 1, "high": 2, "critical": 3, "forbidden": 4}

    def __init__(self, available=True):
        self.available = available

    def evaluate(self, assessment, mandate):
        if not self.available:
            return MonitorResult(False, "risk_monitor_unavailable")
        risk = assessment.risk_level
        # Unknown values are errors, never permission.
        if risk not in self.LEVELS:
            return MonitorResult(False, "unknown_risk_level")
        if risk in {"critical", "forbidden"}:
            return MonitorResult(False, "technical_risk_rejected")
        maximum = mandate.constraints.get("max_risk_level", "high")
        if maximum not in self.LEVELS:
            return MonitorResult(False, "unknown_max_risk_level")
        if self.LEVELS[risk] > self.LEVELS[maximum]:
            return MonitorResult(False, "risk_exceeds_mandate")
        return MonitorResult(True)


class ScopeMonitor:
    def __init__(self, available=True):
        self.available = available

    def evaluate(self, action, assessment, mandate):
        if not self.available:
            return MonitorResult(False, "scope_monitor_unavailable")
        if assessment.parent_scope_expansion:
            return MonitorResult(False, "subtask_scope_expansion")
        if not mandate.allowed_tools:
            return MonitorResult(False, "no_tools_authorized")
        if not any(fnmatchcase(action.tool, rule) for rule in mandate.allowed_tools):
            return MonitorResult(False, "tool_not_authorized")
        classes = assessment.observed_data_classes
        if classes is None:
            return MonitorResult(False, "data_classification_unavailable")
        if any(not isinstance(c, str) or not c for c in classes):
            return MonitorResult(False, "invalid_data_classification")
        if classes and not mandate.allowed_data_classes:
            return MonitorResult(False, "no_data_classes_authorized")
        for cls in classes:
            if not any(fnmatchcase(cls, rule) for rule in mandate.allowed_data_classes):
                return MonitorResult(False, "data_class_not_authorized")
        if assessment.observed_target_kind is None:
            return MonitorResult(False, "target_kind_unavailable")
        if assessment.observed_target_kind != action.target_kind:
            return MonitorResult(False, "target_kind_mismatch")
        if action.target_kind == "path":
            if assessment.resolved_target is None:
                return MonitorResult(False, "target_resolution_unavailable")
            if path_error(assessment.resolved_target):
                return MonitorResult(False, "noncanonical_resolved_target")
            if assessment.resolved_target != action.target:
                return MonitorResult(False, "target_resolution_mismatch")
        return MonitorResult(True)
