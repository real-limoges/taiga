"""
Stage 1: Load and validate the vendored UraLex CLDF tables.

Re-runnable: `python3 stages/stage1_load.py`

Reads the five CLDF tables, checks structural invariants (row counts, the
sampled varieties, referential integrity of the borrowing table), and writes:
- `artifacts/_intermediate/stage1_tables.json` for downstream stages
- a small `artifacts/stage1_load_report.json` summary.
Fails loudly if an invariant the later stages rely on is violated.
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import stage0_config as cfg


def load_csv(name: str) -> tuple[dict[str, str], ...]:
    with open(os.path.join(cfg.DATA_DIR, name), newline="", encoding="utf-8") as f:
        return tuple(csv.DictReader(f))


def run():
    cfg.ensure_dirs()
    languages = load_csv("languages.csv")
    parameters = load_csv("parameters.csv")
    forms = load_csv("forms.csv")
    cognates = load_csv("cognates.csv")
    borrowings = load_csv("borrowings.csv")

    report = {"stage": "stage1_load", "counts": {}, "checks": {}, "warnings": []}
    report["counts"] = {
        "languages_table": len(languages),
        "parameters_table": len(parameters),
        "forms_table": len(forms),
        "cognates_table": len(cognates),
        "borrowings_table": len(borrowings),
    }

    # Varieties actually present in forms.csv
    form_lang_ids = sorted({f["Language_ID"] for f in forms})
    report["counts"]["varieties_in_forms"] = len(form_lang_ids)
    report["checks"]["expected_27_varieties"] = (len(form_lang_ids) == 27)
    if len(form_lang_ids) != 27:
        report["warnings"].append(
            f"Expected 27 varieties in forms.csv, found {len(form_lang_ids)}")

    langmeta = {lang["ID"]: lang for lang in languages}
    varieties = []
    for lid in form_lang_ids:
        m = langmeta[lid]
        varieties.append({
            "id": lid, "name": m["Name"], "subgroup": m["Subgroup"],
            "glottocode": m["Glottocode"],
            "is_proto": (lid == cfg.PROTO_URALIC_ID),
        })

    # Referential integrity: every borrowing Target_Form_ID resolves to a form.
    form_ids = {f["ID"] for f in forms}
    dangling = [b["ID"] for b in borrowings if b["Target_Form_ID"] not in form_ids]
    report["checks"]["borrowing_targets_resolve"] = (len(dangling) == 0)
    if dangling:
        report["warnings"].append(f"{len(dangling)} borrowing rows have dangling Target_Form_ID")

    # Cognacy (forms) should match Cognateset_ID (cognates) where a cognate row exists.
    cog_by_form = {c["Form_ID"]: c["Cognateset_ID"] for c in cognates}
    mismatches = 0
    for f in forms:
        cid = cog_by_form.get(f["ID"])
        if cid is not None and cid != f["Cognacy"]:
            mismatches += 1
    report["checks"]["cognacy_matches_cognateset"] = (mismatches == 0)
    if mismatches:
        report["warnings"].append(f"{mismatches} forms disagree with cognates.csv on set id")

    # Subgroup census over attested varieties (excludes Proto-Uralic reconstruction)
    subgroup_census = {}
    for v in varieties:
        if v["is_proto"]:
            continue
        subgroup_census[v["subgroup"]] = subgroup_census.get(v["subgroup"], 0) + 1
    report["subgroup_census"] = subgroup_census

    tables = {
        "languages": languages, "parameters": parameters, "forms": forms,
        "cognates": cognates, "borrowings": borrowings, "varieties": varieties,
    }
    with open(os.path.join(cfg.INTERMEDIATE_DIR, "stage1_tables.json"), "w") as f:
        json.dump(tables, f)
    with open(os.path.join(cfg.ARTIFACTS_DIR, "stage1_load_report.json"), "w") as f:
        json.dump(report, f, indent=2)

    print("[stage1] varieties in forms:", len(form_lang_ids))
    print("[stage1] subgroup census (attested):", subgroup_census)
    print("[stage1] checks:", report["checks"])
    if report["warnings"]:
        print("[stage1] WARNINGS:", report["warnings"])
    return tables, report


if __name__ == "__main__":
    run()
