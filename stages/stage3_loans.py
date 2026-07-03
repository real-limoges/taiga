"""
Stage 3 — Loanword classification and horizontal-transfer exclusion.

Re-runnable: `python3 stages/stage3_loans.py`

UraLex root-meaning sets (`Cognacy` / `Cognateset_ID`, e.g. `40-a`) already
group forms by *inheritance*: a form borrowed from another family is placed in
its own root-meaning set, not merged with the inherited material. What we still
must do for phylogenetics is stop known borrowings from injecting *horizontal*
signal — i.e. two languages sharing a cognate state because of contact, not
common descent.

We use the BorrowingTable (`borrowings.csv`) to flag, per member language of
each cognate set, whether its form is a loan and whether the donor is external
(non-Uralic) or Uralic-internal. Then:

  EXCLUDE a cognate set from the matrix when its *cross-language* sharing is
  loan-driven:
     E1:  >= 2 member languages carry an external loan flag
          (the borrowing is why >=2 languages share the trait -> false group), OR
     E2:  the set is "fully loan" (every attested member language is loan-flagged,
          with >= 1 external flag) and spans >= 2 languages
          (the whole root entered by borrowing).

  For KEPT sets, RECODE individual loan-flagged cells to '?' (both a lone
  external loan sitting in an otherwise-inherited set, and any intra-Uralic
  loan) so the borrowed cell neither supports nor denies grouping.

Singleton external loans (present in a single language) are KEPT by default:
being in one taxon they cannot create a false grouping (they are branch-specific
autapomorphies). They are counted and also listed so an aggressive alternative
(`aggressive_exclude_singletons`) can drop them.

Emits `artifacts/loanword_exclusions.csv` (every excluded set, with reason),
`artifacts/_intermediate/stage3_loans.json` (machine-readable decisions used by
Stage 4), and `artifacts/loan_exclusion_report.json` (summary).
"""
import csv, json, os, sys, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stage0_config as cfg


def run():
    cfg.ensure_dirs()
    with open(os.path.join(cfg.INTERMEDIATE_DIR, "stage1_tables.json")) as f:
        tables = json.load(f)
    forms = {f["ID"]: f for f in tables["forms"]}
    langmeta = {l["ID"]: l for l in tables["languages"]}
    borrowings = tables["borrowings"]
    params = {p["ID"]: p for p in tables["parameters"]}

    # form_id -> list of loan records (source label, likelihood, class)
    loans_by_form = collections.defaultdict(list)
    for b in borrowings:
        cls = cfg.classify_source(b["SourceLanguoid"])
        loans_by_form[b["Target_Form_ID"]].append(
            {"source": b["SourceLanguoid"], "likelihood": b["Likelihood"], "class": cls})

    # Build real cognate sets (skip ?/0 placeholders and gap rows).
    set_forms = collections.defaultdict(list)
    for fid, f in forms.items():
        if not cfg.cognacy_is_real(f["Cognacy"]):
            continue
        if cfg.is_gap(f["Value"]):
            continue  # the 0-62-1 quirk: gap row, never a presence
        set_forms[f["Cognacy"]].append(f)

    ORDER = {"inherited": 0, "uralic": 1, "external": 2}

    decisions = {}          # cogset -> decision dict (consumed by Stage 4)
    exclusion_rows = []      # for loanword_exclusions.csv
    recode_cells = []        # DEFAULT policy: loan cells recoded to '?' in kept multi-lang sets
    all_loan_cells = []      # AGGRESSIVE policy: EVERY loan-flagged cell (any set, any lang incl. PU*)
    cat_counter = collections.Counter()
    singleton_external = []

    # AGGRESSIVE-policy input: every loan-flagged (cogset, language) cell, over ALL
    # sets and ALL languages including Proto-Uralic*, at any likelihood. Used by the
    # Stage 4 "aggressive_inherited_only" matrix, which lets no loan-flagged form
    # count as a presence.
    for cog, fl in set_forms.items():
        for f in fl:
            recs = loans_by_form.get(f["ID"], [])
            if not recs:
                continue
            srcs = sorted({lr["source"] for lr in recs})
            cls = "inherited"
            for lr in recs:
                c = "external" if lr["class"] in ("external", "ambiguous") else \
                    ("uralic" if lr["class"] == "uralic" else "inherited")
                if ORDER[c] > ORDER[cls]:
                    cls = c
            if cls in ("external", "uralic"):
                all_loan_cells.append({"cogset": cog, "language_id": f["Language_ID"],
                                       "status": cls, "sources": srcs})

    for cog, fl in set_forms.items():
        meaning = params[cog.split("-")[0]]["Name"]
        # Per attested language (exclude Proto-Uralic reconstruction), strongest loan status.
        per_lang = {}
        per_lang_sources = collections.defaultdict(set)
        for f in fl:
            lid = f["Language_ID"]
            if lid == cfg.PROTO_URALIC_ID:
                continue
            status = "inherited"
            for lr in loans_by_form.get(f["ID"], []):
                c = "external" if lr["class"] in ("external", "ambiguous") else \
                    ("uralic" if lr["class"] == "uralic" else "inherited")
                if ORDER[c] > ORDER[status]:
                    status = c
                per_lang_sources[lid].add(lr["source"])
            prev = per_lang.get(lid, "inherited")
            per_lang[lid] = status if ORDER[status] > ORDER[prev] else prev

        n_lang = len(per_lang)
        n_ext = sum(1 for v in per_lang.values() if v == "external")
        n_ura = sum(1 for v in per_lang.values() if v == "uralic")
        n_inh = sum(1 for v in per_lang.values() if v == "inherited")

        fully_loan_ext = (n_ext >= 1) and ((n_ext + n_ura) == n_lang) and n_lang >= 1
        fully_loan_ura = (n_ext == 0) and (n_ura == n_lang) and n_lang >= 2

        exclude = False
        reason = None
        if n_ext >= 2:
            exclude, reason = True, "E1: external loan shared by >=2 languages (horizontal grouping)"
        elif fully_loan_ext and n_lang >= 2:
            exclude, reason = True, "E2: fully-loan set spanning >=2 languages (root borrowed from outside Uralic)"
        elif fully_loan_ura:
            exclude, reason = True, "E3: fully intra-Uralic-loan set spanning >=2 languages (root spread by borrowing within Uralic)"

        # Category bookkeeping
        if n_ext == 0 and n_ura == 0:
            cat = "pure_inherited"
        elif fully_loan_ext or fully_loan_ura:
            cat = "fully_loan"
        elif n_ext >= 2:
            cat = "ext_multi_mixed"
        elif n_ext == 1:
            cat = "ext_single_mixed"
        else:
            cat = "uralic_loan_only"
        cat_counter[cat] += 1

        # Track singleton external loans (kept by default)
        if n_ext == 1 and n_lang == 1:
            lid = next(iter(per_lang))
            singleton_external.append({"cogset": cog, "meaning": meaning,
                                       "language": langmeta[lid]["Name"],
                                       "sources": sorted(per_lang_sources[lid])})

        # Cell recodes for KEPT sets: recode loan-flagged cells to '?' ONLY in
        # MULTI-language sets, where a borrowed cell would falsely group its
        # language with the inherited members. In single-language sets the loan
        # is an autapomorphy (no possible false grouping) and is kept as present.
        cell_recodes = []
        if not exclude and n_lang >= 2:
            for lid, st in per_lang.items():
                if st in ("external", "uralic"):
                    cell_recodes.append(lid)
                    recode_cells.append({"cogset": cog, "language_id": lid,
                                         "language": langmeta[lid]["Name"], "status": st,
                                         "sources": sorted(per_lang_sources[lid])})

        decisions[cog] = {
            "meaning": meaning, "n_lang": n_lang, "n_external": n_ext,
            "n_uralic_loan": n_ura, "n_inherited": n_inh, "category": cat,
            "excluded": exclude, "reason": reason,
            "recode_to_missing_langs": cell_recodes,
        }

        if exclude:
            # collect donor labels for documentation (external, or Uralic for E3)
            loan_states = ("external",) if n_ext > 0 else ("external", "uralic")
            donor_labels = sorted({s for lid, st in per_lang.items() if st in loan_states
                                   for s in per_lang_sources[lid]})
            exclusion_rows.append({
                "cogset": cog, "meaning": meaning, "reason": reason,
                "n_languages": n_lang, "n_external_loans": n_ext,
                "n_uralic_loans": n_ura, "n_inherited": n_inh,
                "external_donors": "; ".join(donor_labels),
                "languages": "; ".join(sorted(langmeta[l]["Name"] for l in per_lang)),
            })

    # Write exclusions CSV (sorted by meaning number then set)
    def sortkey(r):
        p = r["cogset"].split("-")[0]
        return (int(p), r["cogset"])
    exclusion_rows.sort(key=sortkey)
    with open(os.path.join(cfg.ARTIFACTS_DIR, "loanword_exclusions.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["cogset", "meaning", "reason", "n_languages",
                                          "n_external_loans", "n_uralic_loans", "n_inherited",
                                          "external_donors", "languages"])
        w.writeheader()
        for r in exclusion_rows:
            w.writerow(r)

    n_excluded = sum(1 for d in decisions.values() if d["excluded"])
    n_total = len(decisions)
    informative_excluded = sum(1 for d in decisions.values() if d["excluded"] and d["n_lang"] >= 2)

    report = {
        "stage": "stage3_loans",
        "policy": {
            "exclusion_E1": ">=2 member languages carry an external (non-Uralic) loan flag",
            "exclusion_E2": "fully-loan set (all attested members loan-flagged, >=1 external) spanning >=2 languages",
            "kept_set_cell_recode": "loan-flagged cells in kept sets recoded to '?'",
            "singletons": "single-language external loans KEPT (autapomorphies, no false grouping)",
            "ambiguous_sources": "cross-boundary disjunctions (e.g. Germanic_or_Finnic) treated as external",
        },
        "cognate_set_categories": dict(cat_counter),
        "total_real_cognate_sets": n_total,
        "excluded_sets": n_excluded,
        "excluded_sets_informative_ge2_langs": informative_excluded,
        "kept_sets": n_total - n_excluded,
        "cell_recodes_in_kept_sets": len(recode_cells),
        "singleton_external_loans_kept": len(singleton_external),
        "all_loan_flagged_cells_for_aggressive_variant": len(all_loan_cells),
    }
    with open(os.path.join(cfg.INTERMEDIATE_DIR, "stage3_loans.json"), "w") as f:
        json.dump({"decisions": decisions, "recode_cells": recode_cells,
                   "all_loan_cells": all_loan_cells,
                   "singleton_external": singleton_external, "report": report}, f)
    with open(os.path.join(cfg.ARTIFACTS_DIR, "loan_exclusion_report.json"), "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("[stage3] set categories:", dict(cat_counter))
    print(f"[stage3] excluded {n_excluded}/{n_total} sets "
          f"({informative_excluded} informative >=2 langs); "
          f"{len(recode_cells)} loan cells recoded to '?' in kept sets; "
          f"{len(singleton_external)} singleton external loans kept")
    return decisions, report


if __name__ == "__main__":
    run()
