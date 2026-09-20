# Contextual Safety Coherence — RC5 experimental layer

## Principle

**Safety ≠ context amnesia.** A safety constraint should change what is necessary without unnecessarily erasing context, provenance, or an already-established reservation.

This layer addresses a narrow conversational failure mode: repeating the same informational caveat after it has already been explicitly established in the same materially unchanged context.

## Non-goal

This is **not** a bypass for the action gate and does not alter `ALLOW`, `DENY`, `ASK`, or `PAUSE`. `UniversalGate` remains unchanged from RC4. Blocking notices and notices requiring user action are never suppressed.

## Suppression conditions

An informational notice may be marked `SUPPRESS_REPEAT` only when all of the following hold:

1. the notice is structurally valid and carries provenance;
2. it is neither blocking nor action-required;
3. the host explicitly records its `notice_id` as already established;
4. the recorded context revision exactly equals the current context revision.

Missing state fails safe to `EMIT`. A changed revision returns `REFRESH`, making the changed context visible rather than silently reusing an old reservation.

## Host responsibility

The host defines `context_revision`. It must change whenever facts material to the notice change, including relevant risk, authorization, consent, policy, evidence, or task scope. The helper cannot determine semantic equivalence by itself.

The provenance field records where the reservation came from; it is not itself authorization and cannot create or expand a mandate.

## Intended effect

The safety layer becomes context-sensitive without becoming permissive: repeated informational boilerplate can disappear while real changes, blocking constraints, and required interventions remain visible.
