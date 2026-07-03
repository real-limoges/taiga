"""
Stage 0 — Configuration and shared helpers for the UraLex → BEAST2 pipeline.

This module holds all curation *policy* in one place: paths, the set of
Indo-Iranian donor labels used to define the contact layer, the source-language
classifier (external vs. Uralic-internal), and the gap-marker semantics. Every
later stage imports from here so that policy lives in exactly one auditable spot.

Nothing here reads or writes files; it is pure configuration + small helpers.
"""
import os

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data", "uralex_cldf_v2.0")
ARTIFACTS_DIR = os.path.join(REPO_ROOT, "artifacts")
INTERMEDIATE_DIR = os.path.join(ARTIFACTS_DIR, "_intermediate")

# Pinned provenance (mirrored in data/uralex_cldf_v2.0/SOURCE.md and PROVENANCE.md)
URALEX_COMMIT = "0ce4fc7ea8147c9b3175b786eccf87d3a1c7f7e1"
URALEX_VERSION = "2.0"
URALEX_DOI = "10.5281/zenodo.4777568"

# ---------------------------------------------------------------------------
# Taxa
# ---------------------------------------------------------------------------
# The reconstructed Proto-Uralic row uses Language_ID "0". It is a
# *reconstruction*, not an attested variety, and is handled specially: it is
# NOT used when classifying the loan status of a cognate set, and downstream it
# is flagged so the user can decide whether to keep it as a tip or treat it as
# an ancestral-node constraint.
PROTO_URALIC_ID = "0"

# The traditional Uralic subgroups present in the sampled data.
URALIC_SUBGROUPS = {"Saami", "Finnic", "Mordvin", "Mari", "Permic", "Ugric", "Samoyed"}

# Finno-Ugric = every subgroup except Samoyed (Samoyed is the first split in the
# standard tree). Used by the calibration stage to define the FU crown node.
FINNO_UGRIC_SUBGROUPS = URALIC_SUBGROUPS - {"Samoyed"}

# ---------------------------------------------------------------------------
# Gap markers (forms.csv `Value`)
# ---------------------------------------------------------------------------
# Three marked gaps, with DELIBERATELY DIFFERENT downstream semantics:
GAP_NO_EQUIVALENT = "[No equivalent]"      # concept genuinely not lexicalised -> structural ABSENCE (0)
GAP_FORM_NOT_FOUND = "[Form not found]"    # compilers found no form -> MISSING data (?)
GAP_NOT_RECONSTRUCTABLE = "[Not reconstructable]"  # (Proto-Uralic) not reconstructable -> MISSING data (?)
GAP_MARKERS = {GAP_NO_EQUIVALENT, GAP_FORM_NOT_FOUND, GAP_NOT_RECONSTRUCTABLE}

# How each gap maps to a binary cell value for the meaning-block it belongs to.
#   "absent"  -> code 0 for every character of that meaning for that language
#   "missing" -> code ? for every character of that meaning for that language
GAP_CODING = {
    GAP_NO_EQUIVALENT: "absent",
    GAP_FORM_NOT_FOUND: "missing",
    GAP_NOT_RECONSTRUCTABLE: "missing",
}

# ---------------------------------------------------------------------------
# Borrowing source classification
# ---------------------------------------------------------------------------
# UraLex `SourceLanguoid` labels donor languages. For horizontal-transfer
# exclusion we only need to know whether a donor is OUTSIDE Uralic (external) or
# a Uralic language (intra-family borrowing). A few labels are disjunctions that
# straddle the boundary (e.g. "Germanic_or_Finnic"); those are treated as
# EXTERNAL for exclusion purposes (conservative: if it *might* be a non-Uralic
# loan we do not let it count as inherited signal).

# Substrings that identify a NON-Uralic (external) donor.
_EXTERNAL_TOKENS = [
    "indo", "iran", "german", "baltic", "russian", "slav", "turk", "chuvash",
    "tatar", "tocharian", "yeniseian", "tungusic", "latvian", "lithuan",
    "khazar", "bulgar", "cumanian", "swedish", "norv", "european", "unknown",
]
# Substrings that identify a Uralic-internal donor.
_URALIC_TOKENS = [
    "finnic", "finnish", "karelian", "ingrian", "izhorian", "estonian", "veps",
    "komi", "permic", "udmurt", "khanty", "ob-ugric", "ob_ugric", "mansi",
    "mordvin", "saami", "western uralic", "uralic",
]

# The Indo-Iranian contact layer — labels used to anchor the calibration.
# CORE = Proto-Indo-Iranian ("Aryan") era, the ~4000 BP layer.
II_CORE_LABELS = {
    "Indo-Iranian", "Indo-Iranian_or_Iranian", "Indo_Iranian_or_Iranian",
}
# "Iranian" alone is (mostly) a LATER, post-split Iranian layer (e.g. Alanic
# into Hungarian, ~1st millennium CE); tracked separately, NOT used to date the
# deep node.
II_IRANIAN_LATER_LABELS = {"Iranian", "West Old Turkic_or_Iranian"}
# Disjunctions that include Indo-Iranian but reach up into wider IE.
II_AMBIGUOUS_LABELS = {"Indo-Iranian_or_Indo-European"}
# The full contact layer (everything that could be the II layer).
II_ALL_LABELS = II_CORE_LABELS | II_IRANIAN_LATER_LABELS | II_AMBIGUOUS_LABELS


def classify_source(src):
    """Classify a SourceLanguoid string as 'external', 'uralic', or 'ambiguous'.

    'ambiguous' means the label names both an external and a Uralic donor
    (a disjunction across the family boundary). For exclusion we fold
    'ambiguous' in with 'external'."""
    s = src.lower()
    has_ext = any(t in s for t in _EXTERNAL_TOKENS)
    has_ura = any(t in s for t in _URALIC_TOKENS)
    if has_ext and has_ura:
        return "ambiguous"
    if has_ext:
        return "external"
    if has_ura:
        return "uralic"
    return "unknown"


def is_gap(value):
    return value in GAP_MARKERS


def cognacy_is_real(cognacy):
    """True if a Cognacy code names a real root-meaning set (not a ?/0 placeholder)."""
    return not (cognacy.endswith("-?") or cognacy.endswith("-0"))


def ensure_dirs():
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    os.makedirs(INTERMEDIATE_DIR, exist_ok=True)
