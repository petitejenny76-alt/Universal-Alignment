"""Context-coherence helper for conversational safety notices.

This module does not weaken, bypass, or replace UniversalGate.  It only decides
whether an informational safety notice should be emitted again in a stable
conversation context.  Blocking/action-required notices are never suppressed.
"""
from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet, Optional


class NoticeDisposition(str, Enum):
    EMIT = "EMIT"
    SUPPRESS_REPEAT = "SUPPRESS_REPEAT"
    REFRESH = "REFRESH"


@dataclass(frozen=True)
class SafetyNotice:
    notice_id: str
    scope: str
    provenance: str
    blocking: bool = False
    action_required: bool = False

    def validation_error(self) -> Optional[str]:
        for value in (self.notice_id, self.scope, self.provenance):
            if not isinstance(value, str) or not value.strip():
                return "invalid_notice"
        if type(self.blocking) is not bool or type(self.action_required) is not bool:
            return "invalid_notice"
        return None


@dataclass(frozen=True)
class EstablishedSafetyContext:
    """Host-provided record of notices already established in the conversation.

    ``context_revision`` changes when material facts, authorization, risk, or the
    applicable policy context changes.  A notice can only be suppressed when its
    recorded revision exactly matches the current revision.
    """
    context_revision: str
    established_notice_ids: FrozenSet[str] = frozenset()

    def __post_init__(self):
        if not isinstance(self.context_revision, str) or not self.context_revision.strip():
            raise ValueError("invalid_context_revision")
        if not isinstance(self.established_notice_ids, (set, frozenset)):
            raise ValueError("established_notice_ids_set_required")
        if any(not isinstance(item, str) or not item.strip() for item in self.established_notice_ids):
            raise ValueError("invalid_established_notice_id")
        object.__setattr__(self, "established_notice_ids", frozenset(self.established_notice_ids))


class ContextualSafetyFilter:
    """Fail-safe repetition filter for informational safety notices.

    Suppression is deliberately narrow: the notice must be non-blocking,
    non-action-required, explicitly recorded as established, provenance-bearing,
    and tied to the exact current context revision.  Missing/changed context emits.
    """

    def decide(self, notice, established_context=None, *, current_context_revision=None):
        if type(notice) is not SafetyNotice or notice.validation_error():
            return NoticeDisposition.EMIT
        if notice.blocking or notice.action_required:
            return NoticeDisposition.EMIT
        if type(established_context) is not EstablishedSafetyContext:
            return NoticeDisposition.EMIT
        if not isinstance(current_context_revision, str) or not current_context_revision.strip():
            return NoticeDisposition.EMIT
        if established_context.context_revision != current_context_revision:
            return NoticeDisposition.REFRESH
        if notice.notice_id not in established_context.established_notice_ids:
            return NoticeDisposition.EMIT
        return NoticeDisposition.SUPPRESS_REPEAT
