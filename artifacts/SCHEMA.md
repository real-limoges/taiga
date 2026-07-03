# SCHEMA — artifacts and the calibration argument

This document describes every file in `artifacts/` and lays out the
Indo-Iranian calibration reasoning in enough detail to **evaluate the node call
without re-deriving it**. It is the companion to `PROVENANCE.md` (inputs and
pipeline) and `NOTES.md` (working log).

Nothing here runs BEAST2. The matrix and the calibration scheme are *inputs* to a
separate, later inference phase.

---

## Part A — Artifact catalogue

### A.1 Cognate matrices

| File | What |
| --- | --- |
| `cognate_matrix.nex` | **DEFAULT deliverable.** Loan-excluded binary matrix, Nexus. |
| `cognate_matrix.csv` | Same matrix, human-readable (rows = taxa, cols = cognate sets). |
| `cognate_matrix_baseline_noexclusion.nex` / `.csv` | Every real cognate set, no loan handling. For comparison only. |

**Coding.** One binary character per retained root-meaning set. For language *L*
and character *C* (of meaning *M*):

- `1` — *L* has a (non-loan-recoded) form in set *C*.
- `0` — *L* has a lexeme for *M* but in a different set (real absence of this
  root), **or** *L* is `[No equivalent]` for *M* (structural absence).
- `?` — *L* is a loan-recoded cell (Stage 3), **or** *L* is `[Form not found]` /
  `[Not reconstructable]` / has no row for *M* (missing data).

**Dimensions (default matrix):** 27 taxa × **3,448 characters**
(983 parsimony-informative, 2,465 singleton autapomorphies). 4 characters were
dropped as constant-present-in-all-taxa and logged: `14-a` 'I', `84-a` 'eye',
`196-a` 'two', `201-a` 'we'. Baseline matrix: 3,787 characters (1,350
informative) — i.e. loan exclusion removes ~367 informative characters, which
*is* the horizontal-transfer signal we are stripping out.

The Nexus file uses `DATATYPE=Standard SYMBOLS="01" MISSING=?` and includes a
`SETS` block with one `CHARSET meaning_<n>` per meaning, for optional
partitioning.

**Ascertainment.** Only variable characters are present (constant-in-all
characters were removed). When you model this in BEAST2, use the binary
(`BinaryCovarion` / `Binary`) substitution model **with ascertainment-bias
correction** (condition on characters being variable), otherwise branch lengths
and rates are biased.

**Proto-Uralic\*.** `Proto-Uralic_proto` is included as a tip but is a *partial
reconstruction*, not a contemporaneous language. Recommended: treat it as an
ancestral/root constraint, or drop it from tip-dating. Do not date it as an
ordinary leaf. Its row is heavily `?` (only 280 forms; ~2,375 of 3,448 cells
missing) by construction.

### A.2 Gaps

- `gap_report.json` — counts and policy for the three gap markers, examples,
  the `0-62-1` quirk, and the full per-(language,meaning) status census.
- `gap_report.csv` — every one of the 481 gap rows, with its marker, cognacy
  code, chosen coding (`absent`/`missing`), and a note flagging the quirk.

Gap policy (see Part C): `[No equivalent]` → `absent` (0);
`[Form not found]` and `[Not reconstructable]` → `missing` (?).

### A.3 Loan exclusion

- `loanword_exclusions.csv` — **every excluded cognate set** (340 rows) with:
  set id, meaning, exclusion rule (E1/E2/E3), language/loan counts, external
  donor labels, and the member languages. This is the "document what was
  excluded and why, not silently" artifact.
- `loan_exclusion_report.json` — policy statement and summary counts.

### A.4 Calibration

- `calibration_scheme.json` — **the calibration deliverable** (machine-readable):
  calibrated node + taxon set, conservative alternative node, constraint type and
  direction with reasoning, recommended BEAST2 priors, the empirical
  Indo-Iranian distribution measured this run, branch-specific-reflex evidence,
  and a caveats/sensitivity block.
- `indo_iranian_layer_sets.csv` — every core Indo-Iranian cognate set that
  spans >1 subgroup, with subgroup span, likelihood, and member languages.

### A.5 Reports

- `stage1_load_report.json`, `matrix_report.json` — per-stage summaries and
  invariant checks.

---

## Part B — Loan exclusion, in detail

UraLex root-meaning sets already separate other-family borrowings into their own
sets, so what remains to do is stop known borrowings from injecting **horizontal**
(contact) signal into the tree. Borrowing evidence comes entirely from
`borrowings.csv` (the `Loan` column is empty this release).

**Source classifier.** Each `SourceLanguoid` is external (non-Uralic), uralic
(intra-family), or ambiguous (a disjunction crossing the boundary, e.g.
`Germanic_or_Finnic`). Ambiguous is folded into external — we do not let a
maybe-loan count as inherited signal.

**Set-level exclusion rules** (a set is dropped from the matrix if any fires):

| Rule | Condition | Rationale | Count |
| --- | --- | --- | --- |
| E1 | ≥2 member languages carry an external loan flag | The borrowing is *why* ≥2 languages share the trait → false grouping | 291 |
| E2 | fully-loan set (all members loan-flagged, ≥1 external), ≥2 langs | The whole root entered Uralic by borrowing | 1 |
| E3 | fully intra-Uralic-loan set, ≥2 langs | Root spread by borrowing *within* Uralic | 48 |
| | | **Total excluded** | **340** |

**Cell-level recoding.** In *kept* multi-language sets, an individual loan-flagged
cell is recoded to `?` (76 cells) so a lone borrowed form does not falsely group
its language with the inherited members. Single-language loans are **kept** as
`1` (autapomorphies — being in one taxon they cannot create a false grouping;
392 such singleton external loans kept).

**Set census (3,792 real sets):** 2,954 pure-inherited, 705 fully-loan,
27 external-multi-mixed, 83 intra-Uralic-loan-only, 23 external-single-mixed.

Sanity checks (these are the loans you would *want* excluded): `16-a` 'name'
(Proto-Indo-European, all 26 languages) and `4-a` 'water' (PIE, 18 languages) —
the textbook deep Indo-European Wanderwörter — are both excluded. Top external
donors among excluded sets: Germanic (63), North Germanic (59), Finnic [as an
intra-Uralic donor to Saami] (47), Baltic (31), Russian (30), Indo-Iranian (23),
PIE (20), Iranian (14).

**Alternative (more aggressive) policy.** If you want to remove *every* set
touched by any external loan (including single-language ones), filter the
`loanword_exclusions.csv` logic to `n_external_loans >= 1`; the per-set counts are
all present in that file, so no re-run is needed to see the effect.

---

## Part C — Gap handling, in detail

481 marked gaps, handled by meaning rather than dropped:

| Marker | n | Meaning | Coding | Why |
| --- | --- | --- | --- | --- |
| `[No equivalent]` | 30 | concept genuinely not lexicalised | `absent` (0) | a real, informative absence of any root for this meaning |
| `[Form not found]` | 309 | compilers found no form | `missing` (?) | a data gap — we don't know the state |
| `[Not reconstructable]` | 142 | (Proto-Uralic) not reconstructable | `missing` (?) | absence of a reconstruction ≠ absence of the word |

Conflating `[No equivalent]` with the other two would silently manufacture either
false absences or false uncertainty, so they are coded differently on purpose.

Reconciliation: 27 languages × 313 meanings = 8,451 (language, meaning) cells =
7,929 present + 451 missing + 30 structural-absent + 41 no-row (a pair with no
form row at all → also missing). The 451 missing = 309 + 142. ✓

**Quirk.** Row `0-62-1` (Proto-Uralic, meaning 62) is `[Not reconstructable]` yet
was assigned a real cognate code `62-a`. We honour the gap marker (treat it as
missing) and never let it contribute a presence. It is the single reason
`cognates.csv` has 9,751 rows while non-gap forms number 9,750.

---

## Part D — The calibration argument (evaluate this without re-deriving)

### D.1 The anchor and its date

The **Indo-Iranian ("Aryan") loanword layer** in Uralic is dated to
**~4,000 years BP** on independent grounds: Proto-Indo-Iranian is placed at
c. 2000 BCE by archaeology (the Sintashta culture, c. 2100–1800 BCE, and the
early Andronovo horizon of the Eurasian steppe) and by internal Indo-Iranian
linguistic dating. c. 2000 BCE ≈ 4,000 BP. This date is an *external* input, not
something estimated from UraLex.

We restrict the anchor to the **core** Indo-Iranian layer — UraLex
`SourceLanguoid` ∈ {`Indo-Iranian`, `Indo-Iranian_or_Iranian`,
`Indo_Iranian_or_Iranian`} — because "Iranian" alone is largely a **later**,
post-split layer (e.g. Alanic/Ossetic into Hungarian in the 1st millennium CE)
and would contaminate a deep-node date. (137+ core records; see
`calibration_scheme.json → empirical_distribution`.)

### D.2 Direction of the constraint: why a MINIMUM age

A loanword shared across branches can arise two ways:

1. **Borrowed once into a still-undivided proto-language, then inherited.** Then
   that proto-language was *undivided* at contact, so its break-up is *younger*
   than the contact → 4,000 BP would be a **maximum** on the node.
2. **Borrowed into branches that had already begun to diverge** (areal spread
   across an incipient dialect network). Then the node ancestral to those
   branches had *already split* by contact → its break-up is *older* than the
   contact → 4,000 BP is a **minimum** on the node.

The evidence points to (2). The single loan **'horn'** (set `40-a`) surfaces with
the **regular, branch-specific reflexes** of each branch, not one uniform form:

| Subgroup | Reflex |
| --- | --- |
| Finnic | *sarvi* (s-) |
| Saami | *čoarvi* (č-) |
| Mordvin | *śuro* (ś-) |
| Mari | *šur* (š-) |
| Permic | *śur* (ś-) |
| Ugric (Hung.) | *szarv* (sz-) |

These are the regular divergent outcomes of Proto-Uralic *ś (and of each
branch's vowel system). The loan therefore did not sit unchanged in a unified
proto-language; it was taken up by branches already on their own phonological
trajectories. **Hence 4,000 BP is a lower bound on the age of their common
ancestor**, not a point estimate and not an upper bound.

### D.3 Which node: the empirical distribution

Measured from UraLex's own coding this run (see
`calibration_scheme.json → empirical_distribution` and
`indo_iranian_layer_sets.csv`):

- **Core Indo-Iranian loans by likelihood → subgroups reached:**
  - `clear`   → **Finnic, Saami, Mordvin, Mari, Permic** (not Ugric, not Samoyed)
  - `probable`→ + Ugric, + Samoyed
  - `possible`→ + Ugric
- **Widest single clear cross-branch set:** `57-b` 'good'
  (Saami/Mordvin/Mari/Permic, *clear*). Also `138-a` 'green'
  (Finnic/Mari/Permic, clear), `279-a` 'sister' (Mordvin/Permic, clear).
- **Widest set overall:** `40-a` 'horn' — all six Finno-Ugric branches, but
  `probable`, and **absent from Samoyed**.
- **Samoyed** is touched by the core layer only through `13-a` 'rain', and that
  set is pathological for vertical inheritance (see D.5).

### D.4 The call

**Primary calibrated node: the Finno-Ugric crown** — the MRCA of all sampled
varieties except Samoyedic (Finnic + Saami + Mordvin + Mari + Permic + Ugric).
The core Indo-Iranian layer reaches all six Finno-Ugric branches; the branches
were already diverging at contact (D.2); Samoyedic is essentially outside the
layer (D.5). So:

> **age(Finno-Ugric crown) ≥ ~4,000 BP** (hard minimum / one-tailed).

This is **deeper than any single branch protolanguage** (Proto-Finnic,
Proto-Saami, Proto-Mordvin, Proto-Mari, Proto-Permic, Proto-Ugric — the layer is
shared *across* them, so it constrains their common ancestor) and **shallower
than Proto-Uralic** (the root, which includes Samoyedic and is older still).
That is exactly the "not Proto-Uralic itself, not one branch proto" node the
task describes.

**Conservative alternative: the Finno-Permic node** (Finno-Ugric crown *minus*
Ugric = Finnic + Saami + Mordvin + Mari + Permic). Prefer this if you anchor only
on `clear` loans and treat Ugric's participation in the *oldest* layer as
unproven (Ugric's core-II loans are all `probable`/`possible`; the strongest is
`horn`). The ~4,000 BP minimum and its direction are unchanged; only the taxon
set bounding the node contracts by one branch (drops Ugric).

Both readings are provided with taxon sets in `calibration_scheme.json`
(`calibrated_node` and `alternative_conservative_node`), so an analyst who
disagrees about Ugric can pick the other node without any re-derivation.

### D.5 Why NOT Proto-Uralic (Samoyedic), spelled out

The only core Indo-Iranian record touching Samoyedic is set `13-a` 'rain'
(Tundra Nenets, Selkup; `probable`). Three reasons it does not license a
Samoyed-inclusive (Proto-Uralic-level) calibration:

1. **Gappy distribution.** `13-a` is present in Finnic + Samoyedic **only**, and
   skips *every* intermediate Finno-Ugric branch (Saami, Mordvin, Mari, Permic,
   Ugric). A single borrowing into undivided Proto-Uralic followed by vertical
   inheritance would predict intermediate reflexes; their total absence makes
   parallel/areal borrowing or a Wanderwort far more likely.
2. **Weak coding.** It is `probable`, and the Nganasan member is not even
   loan-flagged.
3. **Later single-language noise.** The other Samoyed record, `94-d` 'salt'
   (Selkup), is a single-language, later "Iranian" loan — younger layer,
   irrelevant to the deep node.

UraLex does attach Proto-Uralic\* *reconstructions* to some Indo-Iranian etyma
(e.g. `40-a` `*śarwi̮`). That reflects the compilers' maximal etymological-depth
judgement; it is **not** independent evidence of Samoyed-inclusive inheritance,
and the attested reflex distribution (absent from Samoyed) is what we rely on.

This matches the mainstream position that securely Proto-Uralic-level
(Samoyed-inclusive) Indo-Iranian loanwords are not established, and that the
Aryan contact primarily affected Finno-Ugric after Samoyedic had separated.

### D.6 Encoding it in BEAST2 (recommended)

A one-tailed minimum on the node's `tmrca`:

- **Recommended:** `Exponential`, offset = 4000 BP, mean ≈ 1500 y above the
  offset — a hard floor at 4,000 with a decaying tail into older ages. (The mean
  is a soft modelling choice, not derived from the loans.)
- **Alternatives:** `Uniform[4000, ~8000]` (non-committal floor; upper cap
  arbitrary), or `Lognormal` offset at 4000 (most mass just above the floor,
  long right tail).
- **Do NOT** use a two-sided Normal centred on 4000 or a point age — the evidence
  gives a *floor*, not an estimate.
- Define the calibration on the MRCA **taxon set** in `calibration_scheme.json`,
  and enforce (or verify) Finno-Ugric monophyly with Samoyedic as the outgroup,
  otherwise "MRCA of those taxa" can collapse onto a different node.

### D.7 What could change the call (sensitivity)

- **Ugric's oldest-layer status** — the FU-crown vs Finno-Permic choice hinges on
  whether `horn` (probable) is accepted as a genuine Proto-Indo-Iranian loan in
  Ugric. Both nodes are provided.
- **Reading the direction as (1) not (2)** — if you judged the loans to have
  entered an undivided proto-language, 4,000 BP flips to a *maximum*. We follow
  the branch-specific-reflex evidence (D.2) for the minimum reading.
- **Absolute date of Proto-Indo-Iranian** — shift the 4,000 BP anchor and the
  bound shifts with it; the node identification is independent of the exact
  number.
