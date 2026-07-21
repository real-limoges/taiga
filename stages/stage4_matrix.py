"""
Stage 4 — Build the BEAST2-ready binary presence/absence cognate matrix.

Re-runnable: `python3 stages/stage4_matrix.py`

Coding scheme (standard meaning-partitioned binary "root-meaning" matrix):
each retained cognate set is ONE binary character. For language L and character
C (belonging to meaning M):

  '1'  L has a (non-loan-recoded) form in set C
  '0'  L has a lexeme for M but in a different set (real absence of this root),
       OR L is marked [No equivalent] for M (structural absence of any root)
  '?'  L is a loan-recoded cell for C (Stage 3), OR L is [Form not found] /
       [Not reconstructable] / has no row for M (missing data)

Two matrices are emitted:
  * DEFAULT  — loan-excluded (Stage 3 decisions applied). This is the deliverable.
  * BASELINE — every real cognate set, no loan handling, for comparison.

After coding we drop characters that are non-variable *or* carry no observed
presence (e.g. a set all of whose cells were loan-recoded to '?'), logging each
dropped character and why. Outputs: Nexus (`.nex`, MrBayes/BEAST2 restriction
`datatype=standard`/binary) and a human-readable CSV, for both matrices, plus a
`matrix_report.json`. Proto-Uralic* is included but flagged.
"""
import csv, json, os, sys, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stage0_config as cfg


def _safe_taxon(name):
    # Nexus-safe taxon label: no spaces/parens.
    out = name.replace("(", "").replace(")", "").replace("*", "_proto")
    out = "_".join(out.split())
    return out


def build_matrix(tables, status, decisions, recode_set, pre_exclude):
    """Return (taxa, char_meta, matrix rows dict lid->list, dropped) for one variant.

    pre_exclude : if True, drop whole cognate sets flagged excluded by Stage 3
                  (DEFAULT policy). If False, keep every real set and let cell
                  recoding + the empty-character filter remove loan material
                  (BASELINE uses an empty recode_set; AGGRESSIVE uses the full
                  loan-cell set).
    recode_set  : set of (cogset, language_id) cells forced to '?'.
    """
    forms = tables["forms"]
    params = {p["ID"]: p for p in tables["parameters"]}
    varieties = tables["varieties"]
    lang_ids = [v["id"] for v in varieties]

    # Membership: cogset -> set of (language_id) that have a real (non-gap) form.
    set_langs = collections.defaultdict(set)
    for f in forms:
        cog = f["Cognacy"]
        if not cfg.cognacy_is_real(cog):
            continue
        if cfg.is_gap(f["Value"]):
            continue
        set_langs[cog].add(f["Language_ID"])

    # Which cognate sets are characters in this variant?
    all_sets = sorted(set_langs, key=lambda c: (int(c.split("-")[0]), c))
    if pre_exclude:
        char_sets = [c for c in all_sets if not decisions[c]["excluded"]]
    else:
        char_sets = list(all_sets)

    # Code cells
    matrix = {lid: [] for lid in lang_ids}
    char_meta = []
    dropped = []
    for cog in char_sets:
        meaning_pid = cog.split("-")[0]
        meaning = params[meaning_pid]["Name"]
        col = {}
        for lid in lang_ids:
            key = f"{lid}|{meaning_pid}"
            s = status.get(key, "no_row")
            member = lid in set_langs[cog]
            recoded = (cog, lid) in recode_set
            if member and not recoded:
                col[lid] = "1"
            elif recoded:
                col[lid] = "?"
            else:
                # not a member of this set
                if s == "present":
                    col[lid] = "0"          # has a lexeme for M, different root
                elif s == "absent":
                    col[lid] = "0"          # [No equivalent] -> structural absence
                else:                        # missing / no_row
                    col[lid] = "?"
        # Drop characters with no observed presence or that are invariant.
        vals = list(col.values())
        n_present = vals.count("1")
        n_absent = vals.count("0")
        if n_present == 0:
            dropped.append({"cogset": cog, "meaning": meaning,
                            "reason": "no observed presence after coding (all 0/?)"})
            continue
        if n_absent == 0 and vals.count("?") == 0 and n_present == len(vals):
            dropped.append({"cogset": cog, "meaning": meaning,
                            "reason": "constant present in all taxa (uninformative)"})
            continue
        for lid in lang_ids:
            matrix[lid].append(col[lid])
        char_meta.append({"cogset": cog, "meaning": meaning,
                          "n_present": n_present, "n_absent": n_absent})
    return lang_ids, char_meta, matrix, dropped


def write_nexus(path, varieties, char_meta, matrix, title):
    langmeta = {v["id"]: v for v in varieties}
    lang_ids = [v["id"] for v in varieties]
    taxa = [_safe_taxon(langmeta[l]["name"]) for l in lang_ids]
    nchar = len(char_meta)
    width = max(len(t) for t in taxa) + 2
    with open(path, "w") as f:
        f.write("#NEXUS\n")
        f.write(f"[ {title} ]\n")
        f.write(f"[ Generated by the UraLex->BEAST2 curation pipeline; {nchar} binary "
                f"cognate characters x {len(taxa)} varieties. ]\n")
        f.write("[ States: 1=cognate present, 0=absent, ?=missing. Proto-Uralic_proto "
                "is a RECONSTRUCTION (see SCHEMA.md). ]\n\n")
        f.write("BEGIN TAXA;\n")
        f.write(f"    DIMENSIONS NTAX={len(taxa)};\n")
        f.write("    TAXLABELS\n        " + "\n        ".join(taxa) + "\n    ;\nEND;\n\n")
        f.write("BEGIN CHARACTERS;\n")
        f.write(f"    DIMENSIONS NCHAR={nchar};\n")
        f.write('    FORMAT DATATYPE=Standard SYMBOLS="01" MISSING=? GAP=-;\n')
        f.write("    CHARSTATELABELS\n")
        labels = []
        for i, cm in enumerate(char_meta, 1):
            lab = f"{cm['cogset']}_{_safe_taxon(cm['meaning'])}"
            labels.append(f"        {i} {lab}")
        f.write(",\n".join(labels) + "\n    ;\n")
        f.write("    MATRIX\n")
        for l, t in zip(lang_ids, taxa):
            f.write(f"        {t.ljust(width)}{''.join(matrix[l])}\n")
        f.write("    ;\nEND;\n\n")
        # A charset block grouping characters by meaning (useful for partitioning)
        f.write("BEGIN SETS;\n")
        by_meaning = collections.defaultdict(list)
        for i, cm in enumerate(char_meta, 1):
            by_meaning[cm["cogset"].split("-")[0]].append(i)
        for pid, idxs in sorted(by_meaning.items(), key=lambda x: int(x[0])):
            f.write(f"    CHARSET meaning_{pid} = {min(idxs)}-{max(idxs)};\n"
                    if idxs == list(range(min(idxs), max(idxs) + 1))
                    else f"    CHARSET meaning_{pid} = {' '.join(map(str, idxs))};\n")
        f.write("END;\n")


def write_csv(path, varieties, char_meta, matrix):
    langmeta = {v["id"]: v for v in varieties}
    lang_ids = [v["id"] for v in varieties]
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["taxon", "subgroup", "is_reconstruction"] +
                   [cm["cogset"] for cm in char_meta])
        for l in lang_ids:
            w.writerow([langmeta[l]["name"], langmeta[l]["subgroup"],
                        langmeta[l]["is_proto"]] + matrix[l])


def run():
    cfg.ensure_dirs()
    with open(os.path.join(cfg.INTERMEDIATE_DIR, "stage1_tables.json")) as f:
        tables = json.load(f)
    with open(os.path.join(cfg.INTERMEDIATE_DIR, "stage2_status.json")) as f:
        status = json.load(f)
    with open(os.path.join(cfg.INTERMEDIATE_DIR, "stage3_loans.json")) as f:
        s3 = json.load(f)
    decisions = s3["decisions"]
    default_recode = {(r["cogset"], r["language_id"]) for r in s3["recode_cells"]}
    aggressive_recode = {(r["cogset"], r["language_id"]) for r in s3["all_loan_cells"]}
    varieties = tables["varieties"]

    report = {"stage": "stage4_matrix", "variants": {}}

    # (variant key, file suffix, pre_exclude, recode_set, title)
    variants = [
        ("default_loan_excluded", "", True, default_recode,
         "UraLex 2.0 Uralic cognate matrix — loan-excluded (DEFAULT)"),
        ("baseline_no_exclusion", "_baseline_noexclusion", False, set(),
         "UraLex 2.0 Uralic cognate matrix — baseline, no loan exclusion"),
        ("aggressive_inherited_only", "_aggressive_inherited_only", False, aggressive_recode,
         "UraLex 2.0 Uralic cognate matrix — aggressive, inherited-only "
         "(every loan-flagged form removed)"),
    ]
    for variant, suffix, pre_exclude, recode_set, title in variants:
        lang_ids, char_meta, matrix, dropped = build_matrix(
            tables, status, decisions, recode_set, pre_exclude)
        nex = os.path.join(cfg.ARTIFACTS_DIR, f"cognate_matrix{suffix}.nex")
        csvp = os.path.join(cfg.ARTIFACTS_DIR, f"cognate_matrix{suffix}.csv")
        write_nexus(nex, varieties, char_meta, matrix, title)
        write_csv(csvp, varieties, char_meta, matrix)

        # Informativeness census
        n_informative = sum(1 for cm in char_meta if cm["n_present"] >= 2 and cm["n_absent"] >= 1)
        n_singleton = sum(1 for cm in char_meta if cm["n_present"] == 1)
        report["variants"][variant] = {
            "n_taxa": len(lang_ids),
            "n_characters": len(char_meta),
            "n_parsimony_informative": n_informative,
            "n_singleton_autapomorphies": n_singleton,
            "n_dropped_characters": len(dropped),
            "dropped_examples": dropped[:10],
            "nexus": os.path.relpath(nex, cfg.REPO_ROOT),
            "csv": os.path.relpath(csvp, cfg.REPO_ROOT),
        }
        print(f"[stage4] {variant}: {len(char_meta)} characters "
              f"({n_informative} informative, {n_singleton} singletons), "
              f"{len(dropped)} dropped")

    with open(os.path.join(cfg.ARTIFACTS_DIR, "matrix_report.json"), "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    return report


if __name__ == "__main__":
    run()
