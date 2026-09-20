import unittest

from universal_alignment.contextual_safety import (
    ContextualSafetyFilter, EstablishedSafetyContext, NoticeDisposition, SafetyNotice,
)


class ContextualSafetyTests(unittest.TestCase):
    def setUp(self):
        self.filter = ContextualSafetyFilter()
        self.notice = SafetyNotice(
            notice_id="correlation_not_causation",
            scope="evidence_interpretation",
            provenance="chronology:A/B/C/D",
        )
        self.context = EstablishedSafetyContext(
            context_revision="rev-7",
            established_notice_ids=frozenset({"correlation_not_causation"}),
        )

    def test_established_informational_notice_is_suppressed_in_same_context(self):
        self.assertEqual(
            self.filter.decide(self.notice, self.context, current_context_revision="rev-7"),
            NoticeDisposition.SUPPRESS_REPEAT,
        )

    def test_material_context_change_refreshes_notice(self):
        self.assertEqual(
            self.filter.decide(self.notice, self.context, current_context_revision="rev-8"),
            NoticeDisposition.REFRESH,
        )

    def test_unknown_notice_is_emitted(self):
        notice = SafetyNotice("new_constraint", "authorization", "policy:42")
        self.assertEqual(
            self.filter.decide(notice, self.context, current_context_revision="rev-7"),
            NoticeDisposition.EMIT,
        )

    def test_missing_context_emits_fail_safe(self):
        self.assertEqual(self.filter.decide(self.notice), NoticeDisposition.EMIT)

    def test_missing_current_revision_emits_fail_safe(self):
        self.assertEqual(self.filter.decide(self.notice, self.context), NoticeDisposition.EMIT)

    def test_blocking_notice_is_never_suppressed(self):
        notice = SafetyNotice(
            "correlation_not_causation", "evidence_interpretation",
            "policy:blocking", blocking=True,
        )
        self.assertEqual(
            self.filter.decide(notice, self.context, current_context_revision="rev-7"),
            NoticeDisposition.EMIT,
        )

    def test_action_required_notice_is_never_suppressed(self):
        notice = SafetyNotice(
            "correlation_not_causation", "evidence_interpretation",
            "policy:action", action_required=True,
        )
        self.assertEqual(
            self.filter.decide(notice, self.context, current_context_revision="rev-7"),
            NoticeDisposition.EMIT,
        )

    def test_provenance_is_required(self):
        notice = SafetyNotice("known", "scope", "")
        ctx = EstablishedSafetyContext("r", frozenset({"known"}))
        self.assertEqual(
            self.filter.decide(notice, ctx, current_context_revision="r"),
            NoticeDisposition.EMIT,
        )

    def test_context_ids_are_strictly_typed(self):
        with self.assertRaises(ValueError):
            EstablishedSafetyContext("r", ["known"])

    def test_filter_does_not_touch_action_gate_decisions(self):
        # Architectural regression: this helper has no UniversalGate dependency
        # and returns only notice dispositions, never ALLOW/DENY/ASK/PAUSE.
        result = self.filter.decide(self.notice, self.context, current_context_revision="rev-7")
        self.assertNotIn(result.value, {"ALLOW", "DENY", "ASK", "PAUSE"})


if __name__ == "__main__":
    unittest.main()