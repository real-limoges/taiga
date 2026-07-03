# Working NOTES — UraLex → BEAST2 curation

Running log of decisions, discoveries, and open questions. Newest context at the
bottom of each section. This is a lab notebook, not polished prose.

## 0. Premise correction (session start)

- The task brief said `PROVENANCE.md` and `artifacts/SCHEMA.md` "already exist as
  skeletons." **They did not** — the repo contained only `LICENSE` at session
  start (confirmed with `git ls-tree`). I created them from scratch rather than
  editing skeletons. Flagging so nobody wonders where the skeletons went.

## 1. Dataset

- Source: UraLex v2.0 CLDF, `lexibank/uralex`, pinned commit
  `0ce4fc7ea8147c9b3175b786eccf87d3a1c7f7e1`, DOI 10.5281/zenodo.4777568,
  CC-BY-4.0. Cloned fresh; vendored the 5 tables used into
  `data/uralex_cldf_v2.0/` for reproducibility in an ephemeral container.
- 43 rows in `languages.csv`, but **27 varieties actually appear in `forms.csv`**:
  1 Proto-Uralic* reconstruction (`Language_ID = 0`) + 26 attested languages
  (7 Saami, 8 Finnic, 1 Mordvin=Erzya, 1 Mari=Meadow, 3 Permic, 3 Ugric
  [Hungarian, Sosva Mansi, Vakh-Vasyugan Khanty], 3 Samoyed). That is the "27".

## 2. Key structural facts (drive the whole design)

- `forms.csv::Loan` column is **empty for all 10,231 rows**. All borrowing info
  lives in `borrowings.csv` (Target_Form_ID, SourceLanguoid, Likelihood). Do NOT
  rely on the Loan column.
- `Cognacy` / `Cognateset_ID` (e.g. `40-a`) = the **root-meaning set** (cognacy /
  inheritance based). This is the correct character for phylogenetics: UraLex
  already puts other-family borrowings in their *own* root-meaning sets.
  (`form_set`, the integer correlate set, groups by borrowing OR inheritance —
  NOT what we want.)
- Gap markers in `Value`: `[No equivalent]` (30), `[Form not found]` (309),
  `[Not reconstructable]` (142) = 481 total. Decision:
  - `[No equivalent]` → structural ABSENCE (code 0): concept truly not lexicalised.
  - `[Form not found]` / `[Not reconstructable]` → MISSING (code ?): data gap /
    unreconstructable, not evidence of absence.
- Data quirk: row `0-62-1` (PU, meaning 62) is `[Not reconstructable]` yet has a
  real cognate code `62-a`. Handled: honour the gap marker, never count a
  presence. 481 gaps reconcile: 27×313 = 8451 (lang,meaning) cells = 7929
  present + 451 missing + 30 structural-absent + 41 no-row. ✓

## 3. Loan exclusion policy (Stage 3)

- Source classifier: SourceLanguoid → external (non-Uralic) / uralic / ambiguous.
  Cross-boundary disjunctions (e.g. `Germanic_or_Finnic`) treated as EXTERNAL
  (conservative — don't let a maybe-loan count as inherited).
- Exclude a whole cognate set when cross-language sharing is loan-driven:
  - E1: ≥2 member languages carry an external loan flag.
  - E2: fully-loan set (all members loan-flagged, ≥1 external), ≥2 languages.
  - E3: fully intra-Uralic-loan set, ≥2 languages (root spread by borrowing
    within Uralic). Added E3 after noticing such sets would otherwise vanish
    silently via cell-recoding — better to log them.
- Kept sets: recode individual loan cells to `?` ONLY in multi-language sets
  (where a borrowed cell would falsely group). Single-language loans kept as
  autapomorphies (can't create false grouping). [Fixed an earlier bug where
  singletons were being masked, dropping 454 chars; correct number is 4.]
- Result: 340/3792 sets excluded, 76 loan cells recoded, 392 singleton external
  loans kept. Sanity: excluded incl. `16-a` 'name' (PIE, all 26 langs),
  `4-a` 'water' (PIE, 18 langs) — the classic deep IE Wanderwörter. Good.

## 4. Matrix (Stage 4)

- Binary meaning-partitioned root-meaning matrix. DEFAULT (loan-excluded):
  **3448 characters** (983 parsimony-informative, 2465 singletons), 4 dropped as
  constant. BASELINE (no exclusion): 3787 chars (1350 informative). So loan
  exclusion removes ~367 informative characters = the horizontal-transfer signal.
- Dropped-as-constant chars are the ultra-stable pan-Uralic roots: 'I' 14-a,
  'eye' 84-a, 'two' 196-a, 'we' 201-a (and in baseline 'name' 16-a). Reassuring.
- Emit Nexus (`datatype=Standard SYMBOLS="01"`) + CSV for both variants, with a
  per-meaning CHARSET block. Note ascertainment: only variable characters remain
  → use BEAST2 binary model with ascertainment-bias correction.

## 5. Calibration (Stage 5) — the crux

- Anchor: Proto-Indo-Iranian ("Aryan") loan layer, ~4000 BP (Sintashta
  c. 2100–1800 BCE ≈ 2000 BCE ≈ 4000 BP).
- Direction: the loans show **regular branch-specific reflexes** — one loan,
  'horn' 40-a, surfaces as Finnic *sarvi* / Saami *čoarvi* / Mari *šur* /
  Mordvin *śuro* / Permic *śur* / Hung. *szarv* (the differing reflexes of PU *ś
  and each branch's vowels). So branches had already begun diverging at contact
  → the node they descend from PRE-dates contact → 4000 BP is a **minimum**
  (lower bound), not a point age and not a maximum.
- Which node? Empirically, from UraLex's own coding:
  - CLEAR core-II loans span exactly {Finnic, Saami, Mordvin, Mari, Permic} =
    Finno-Permic descendants.
  - Ugric is reached only by 'probable' (horn 40-a) + 'possible' (house 26-b …).
  - Samoyed is reached only by the problematic 13-a 'rain' (Finnic+Samoyed only,
    skips all intermediate branches; Nganasan form not even loan-flagged;
    'probable'). → does NOT license a Samoyed-inclusive (Proto-Uralic) node.
  - PRIMARY call: **Finno-Ugric crown** (all six FU branches; Ugric in via horn).
  - CONSERVATIVE alt: **Finno-Permic** (clear-loan-only; drops Ugric). Same
    ~4000 BP minimum; node just one level shallower.
  - NOT Proto-Uralic (Samoyed out); NOT a single branch proto (shared across
    branches). Matches the brief's "deeper than any branch proto, not PU itself."
- BEAST2 prior: minimum-age / one-tailed. Recommend Exponential(offset=4000 BP)
  or Uniform[4000, ~8000]. Do NOT use a two-sided normal centred on 4000.

## 6. Open / deferred (NOT done, by instruction)

- No BEAST2 run, no root-age or topology inference (separate phase, out of scope).
- Proto-Uralic* included in the matrix as a tip but flagged: it's a partial
  reconstruction; recommend treating as ancestral/root constraint, not a dated
  leaf.

## 7. Verification

- Fresh-context subagent audit at checkpoint: see section appended below after it
  ran. Every headline number above was regenerated by `stages/run_all.py` this
  session and cross-checked against the artifact JSONs.
