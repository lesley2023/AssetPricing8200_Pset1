---
name: tp
description: "Traceable Prompt (TP) skill for BUSFIN 8200 problem sets. Invoke @TP at the start of every substantive AI request (checking/critiquing math or economic reasoning, empirical coding, debugging, formatting/translation) to comply with the course AI policy. Creates git commits before/after the interaction and appends an auditable entry to AI_INTERACTIONS.md."
---

# TP (Traceable Prompt)

This skill creates an auditable, contemporaneous record of substantive AI assistance on a
BUSFIN 8200 problem set, per the course AI Policy. It does not loosen any requirement of
that policy (e.g., AI still may not generate/rewrite math derivations or economic reasoning,
and may not silently make substantive empirical design decisions).

When the user invokes `@TP`, follow these steps in order:

1. **Identify the problem set item.** Determine which question/sub-part (e.g., "Q1(b)") the
   request concerns from the user's message or recent conversation. If it is not clear, ask
   the user to specify it before doing any substantive work.

2. **Commit "before" snapshot.** Run `git add -A` and `git commit -m "TP: before <item> — <short description>"`.
   If there is nothing to commit, use `git commit --allow-empty -m "TP: before <item> — <short description>"`
   so the pre-interaction state is still recorded. Capture the resulting commit hash
   (`git rev-parse HEAD`).

3. **Do the substantive work**, subject to the course AI policy:
   - Math questions: only check/critique the user's own derivation; do not derive for them.
   - Economic reasoning questions: only critique the user's own written reasoning; do not
     write the argument for them.
   - Data analysis questions: implement/debug/optimize code strictly from the user's own
     written specification (e.g., a `.txt`/`.md` file or their initial code). If the request
     requires a substantive empirical/econometric decision not specified by the user
     (sample restriction, timing convention, missing-data treatment, variable definition,
     winsorization, regression spec, SE choice, etc.), STOP and ask the user to decide rather
     than resolving it yourself.
   - Formatting/translation requests (LaTeX, grammar, exposition) may be done freely, but
     must not alter substantive math/economic/empirical content.

4. **Append an entry to `AI_INTERACTIONS.md`** at the repository root. Never edit, delete,
   reorder, or combine prior entries — only append. Use the template already in that file,
   filling in: problem set item; the user's substantive prompt; purpose; commit hash before;
   files inspected; files modified (if any); any errors/omissions/ambiguities identified; any
   substantive math/economic/empirical suggestions made (clearly separated from purely
   mechanical programming/formatting choices); the type(s) of AI use; and whether any minor
   follow-up debugging/formatting requests were grouped into this same entry (only group
   when the user explicitly asks to, and only if they concern the same item and session).

5. **Commit "after" snapshot.** Run `git add -A` and `git commit -m "TP: after <item> — <short description>"`.
   If there are no file changes, use `git commit --allow-empty -m "TP: after <item> — <short description>"`.
   Capture this commit hash too, and use it in the `AI_INTERACTIONS.md` entry (append the
   entry, then make this final commit so the entry itself is captured in the "after" snapshot).

6. **Grouping follow-ups.** If the user explicitly says a subsequent minor request (e.g., a
   quick debugging fix or formatting tweak) belongs with the current interaction, and it
   concerns the same item and work session, update the same `AI_INTERACTIONS.md` entry
   instead of creating a new one, then re-commit the "after" state.

If any step fails (e.g., git commit fails, or the `AI_INTERACTIONS.md` entry cannot be
written), stop and report the failure to the user before proceeding with further substantive
work — do not silently skip the record-keeping.
