# Contributing

This roadmap has two things that make it different from a link list, and contributions have to hold both lines. This guide is the quality gate.

**Questions and half-formed ideas go to [Discussions](https://github.com/proofstone/applied-cryptography-roadmap/discussions), not issues** — "is §4 missing something?", "what do you think about X". Issues here are for the two templates: a resource, or a milestone.

## Rule 1 — a node is a milestone, not a topic

> Every node states an artifact the reader can point to, phrased as **`You're done when …`** and ending in something *checkable*: a passing Cryptopals/CryptoHack challenge, a completed course track, a tool's pass/fail output.

In this map "checkable" is literal — a captured flag, a solved set, a scanner that catches a planted key. If the "done" condition is "you understand X" or "you've read about X," it is not a milestone.

| ✅ A milestone | ❌ Not a milestone |
|---|---|
| "You're done when Cryptopals #17 (the CBC padding oracle) passes." | "Learn how padding oracles work." |
| "You're done when the CryptoHack Elliptic Curves course is complete." | "Understand elliptic-curve cryptography." |
| "You're done when a secrets scanner catches a key you planted, and a clean run reports zero findings." | "Know not to commit keys." |

**Articulation milestones.** Exactly three nodes (M0.2, M5.2, M10.1) end in *"you can state / justify …"* instead of a flag, because the thing they check has no external binary oracle in the canon. They are **labeled inline as articulation milestones.** A new node may only be an articulation milestone if you can show, the same way, that no canonical failable check exists — and it must be labeled. Do not slip an un-checkable node into the normal `You're done when …` format; that is exactly the trap this map is built against.

## Rule 2 — every cryptographic claim is a quote from the canon, never ours

> The author is a cartographer, not a cryptographer. This map makes **no cryptographic claims of its own.** Every technical statement about cryptography is a quote from a canonical source (Cryptopals, CryptoHack, NIST, OWASP, Boneh, a named book), with a link.

This is not stylistic — cryptography is a field that is unkind to confident amateurs, and the map's usefulness depends on never pretending otherwise. Concretely:

- **No original security advice.** If you can't attribute a claim to a canonical source, it doesn't go in.
- **No hand-rolled crypto, and no "reference implementations" of cryptography.** Unlike sibling roadmaps in this series, this one ships no cryptographic code of its own. Learning implementations belong here only when the canon already provides them (e.g. Cryptopals *is* the exercise).
- **Quote precisely.** Standards status especially: NIST IR 8547 is an *Initial Public Draft*, not a final standard — say so, with the primary-source link, not a blog's paraphrase.

## Suggesting a resource

Resources are held to the project's standard: **three excellent resources beat ten mediocre ones, and no resource appears twice.** Before you propose one, it must be:

1. **Open** — readable/runnable without a paywall, an application, or a closed cohort. (Pointing *at* a canonical challenge set or a book is fine.)
2. **Live** — you opened it this week and it works.
3. **Best-in-class** — the *best* hands-on resource for that milestone, not merely *a* resource.
4. **Canonical** — for anything that carries a cryptographic claim, it must be a recognized authority, and the claim must be quotable from it.

Use the **Suggest a resource** issue template.

## Suggesting a milestone

New milestones are welcome if they fill a real gap in the "working engineer → shipping cryptography safely" path. Use the **Suggest a milestone** template and include the `You're done when …` line (the checkable artifact), where it fits in the section order, and one canonical resource that meets the bar above.

## Editing the map

The path map in the README is **generated**, never hand-drawn. Edit the `SECTIONS` / `EDGES` data at the top of [`scripts/render_map.py`](scripts/render_map.py), then regenerate:

```
python scripts/render_map.py
```

CI runs `python scripts/render_map.py --check` and fails if `assets/roadmap.svg` is out of sync with the script. Commit both.

## What gets rejected

- Keyword nodes with no checkable artifact.
- Any cryptographic claim that isn't a quote from a canonical source.
- Original crypto advice, or a hand-rolled cryptographic implementation.
- A second resource that does the same job as one already present.
- Resources behind paywalls/logins, or dead when submitted.

Facts only in review comments — no need for pleasantries.
