"""
Stage 2 — Classify marked gaps and build the per-(language, meaning) status map.

Re-runnable: `python3 stages/stage2_gaps.py`

UraLex marks three kinds of gap in `forms.csv::Value`:

  [No equivalent]      the concept is genuinely not lexicalised in the language
                       -> STRUCTURAL ABSENCE. Coded 0 for every character of
                       that meaning: the language really lacks any root here.
  [Form not found]     the compilers could not locate a form (data gap)
                       -> MISSING DATA. Coded ? : we do not know the state.
  [Not reconstructable] a Proto-Uralic meaning that cannot be reconstructed
                       -> MISSING DATA. Coded ? on the Proto-Uralic row.

Treating [No equivalent] as absence but the other two as missing is a
deliberate, documented choice: conflating a true lexical gap with a data gap
would silently invent either false absences or false uncertainty.

One data quirk is handled explicitly: the single row `0-62-1`
(Proto-Uralic, meaning 62) carries Value "[Not reconstructable]" yet was also
assigned the real cognate code `62-a`. We honour the gap marker (treat it as
missing) and do NOT let it contribute a presence, and we record the quirk.

Writes `artifacts/_intermediate/stage2_status.json`
(status per (language_id, parameter_id)) and `artifacts/gap_report.json` /
`artifacts/gap_report.csv`.
"""
import csv, json, os, sys, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stage0_config as cfg


def run():
    cfg.ensure_dirs()
    with open(os.path.join(cfg.INTERMEDIATE_DIR, "stage1_tables.json")) as f:
        tables = json.load(f)
    forms = tables["forms"]
    langmeta = {l["ID"]: l for l in tables["languages"]}

    # Group form rows by (language, parameter/meaning).
    by_lm = collections.defaultdict(list)
    for f in forms:
        by_lm[(f["Language_ID"], f["Parameter_ID"])].append(f)

    # Per (language, meaning) status:
    #   "present" -> has >=1 real lexeme (contributes presences)
    #   "absent"  -> [No equivalent] only : structural absence, 0 across meaning
    #   "missing" -> [Form not found]/[Not reconstructable] only : ? across meaning
    #   "no_row"  -> no row at all : ? across meaning (implicit missing)
    status = {}
    quirks = []
    gap_counter = collections.Counter()
    per_marker_examples = collections.defaultdict(list)

    for (lid, pid), rows in by_lm.items():
        has_lexeme = any(not cfg.is_gap(r["Value"]) for r in rows)
        gap_values = [r["Value"] for r in rows if cfg.is_gap(r["Value"])]
        for r in rows:
            if cfg.is_gap(r["Value"]):
                gap_counter[r["Value"]] += 1
                if len(per_marker_examples[r["Value"]]) < 5:
                    per_marker_examples[r["Value"]].append(
                        {"form_id": r["ID"], "language": langmeta[lid]["Name"],
                         "parameter": pid, "cognacy": r["Cognacy"]})
                # Quirk: gap marker but assigned a REAL cognate code.
                if cfg.cognacy_is_real(r["Cognacy"]):
                    quirks.append({"form_id": r["ID"], "value": r["Value"],
                                   "cognacy": r["Cognacy"], "language": langmeta[lid]["Name"],
                                   "parameter": pid,
                                   "handling": "gap marker honoured; presence NOT counted"})
        if has_lexeme:
            status[f"{lid}|{pid}"] = "present"
        elif gap_values:
            # If any [No equivalent] -> structural absence; else missing.
            if cfg.GAP_NO_EQUIVALENT in gap_values:
                status[f"{lid}|{pid}"] = "absent"
            else:
                status[f"{lid}|{pid}"] = "missing"
        else:
            status[f"{lid}|{pid}"] = "no_row"

    # Also record, for every (language, meaning) with NO row at all, that it is
    # implicit-missing. We enumerate the full grid so Stage 4 can code ? cells.
    all_langs = [v["id"] for v in tables["varieties"]]
    all_params = [p["ID"] for p in tables["parameters"]]
    implicit_missing = 0
    for lid in all_langs:
        for pid in all_params:
            key = f"{lid}|{pid}"
            if key not in status:
                status[key] = "no_row"
                implicit_missing += 1

    status_census = collections.Counter(status.values())

    report = {
        "stage": "stage2_gaps",
        "gap_marker_counts": dict(gap_counter),
        "gap_marker_total": sum(gap_counter.values()),
        "gap_coding_policy": {k: cfg.GAP_CODING[k] for k in cfg.GAP_MARKERS},
        "status_census_per_language_meaning": dict(status_census),
        "implicit_missing_cells_no_row": implicit_missing,
        "examples_per_marker": {k: v for k, v in per_marker_examples.items()},
        "quirks": quirks,
        "notes": [
            "[No equivalent] -> structural ABSENCE (0); the other two markers -> MISSING (?).",
            "no_row = (language, meaning) with no form row at all -> treated as MISSING (?).",
        ],
    }

    with open(os.path.join(cfg.INTERMEDIATE_DIR, "stage2_status.json"), "w") as f:
        json.dump(status, f)
    with open(os.path.join(cfg.ARTIFACTS_DIR, "gap_report.json"), "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Flat CSV of every gap row, for human inspection.
    with open(os.path.join(cfg.ARTIFACTS_DIR, "gap_report.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["form_id", "language", "parameter", "gap_marker", "cognacy",
                    "coding", "note"])
        for r in forms:
            if cfg.is_gap(r["Value"]):
                note = "REAL cognate code on gap row (quirk)" if cfg.cognacy_is_real(r["Cognacy"]) else ""
                w.writerow([r["ID"], langmeta[r["Language_ID"]]["Name"], r["Parameter_ID"],
                            r["Value"], r["Cognacy"], cfg.GAP_CODING[r["Value"]], note])

    print("[stage2] gap marker counts:", dict(gap_counter), "total:", sum(gap_counter.values()))
    print("[stage2] status census:", dict(status_census))
    print("[stage2] quirks:", len(quirks), quirks)
    return status, report


if __name__ == "__main__":
    run()
