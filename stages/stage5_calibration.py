"""
Stage 5 — Derive the Indo-Iranian contact-layer calibration node and scheme.

Re-runnable: `python3 stages/stage5_calibration.py`

This stage does NOT run BEAST2 or infer anything. It (a) measures, from UraLex's
own borrowing coding, how the Indo-Iranian loan layer is distributed across the
Uralic subgroups; (b) identifies the node whose age that distribution
constrains; and (c) writes a machine- and human-readable calibration
specification with the full chain of reasoning.

The empirical distribution is computed here so the reasoning in
`artifacts/calibration_scheme.json` is anchored to numbers this run produced,
not to memory. The prose argument lives in the JSON `reasoning` block and,
expanded, in artifacts/SCHEMA.md.
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
    params = {p["ID"]: p for p in tables["parameters"]}
    borrowings = tables["borrowings"]

    def sub(lid):
        return langmeta[lid]["Subgroup"]

    # ------------------------------------------------------------------ #
    # 1. Collect Indo-Iranian layer loan records (from UraLex coding).    #
    # ------------------------------------------------------------------ #
    layer_records = []  # dict per borrowing in the II layer
    for b in borrowings:
        src = b["SourceLanguoid"]
        if src not in cfg.II_ALL_LABELS:
            continue
        tgt = forms.get(b["Target_Form_ID"])
        if tgt is None:
            continue
        lid = tgt["Language_ID"]
        if src in cfg.II_CORE_LABELS:
            layer = "core_indo_iranian"       # Proto-Indo-Iranian era (~4000 BP)
        elif src in cfg.II_AMBIGUOUS_LABELS:
            layer = "indo_iranian_or_wider_ie"
        else:
            layer = "later_iranian"           # post-split Iranian (mostly younger)
        layer_records.append({
            "borrowing_id": b["ID"], "source": src, "layer": layer,
            "likelihood": b["Likelihood"], "language_id": lid,
            "language": langmeta[lid]["Name"], "subgroup": sub(lid),
            "parameter": tgt["Parameter_ID"], "meaning": params[tgt["Parameter_ID"]]["Name"],
            "cogset": tgt["Cognacy"], "form": tgt["Value"], "is_proto": lid == cfg.PROTO_URALIC_ID,
        })

    # ------------------------------------------------------------------ #
    # 2. Distribution of the layer over subgroups.                        #
    # ------------------------------------------------------------------ #
    by_subgroup = collections.Counter(r["subgroup"] for r in layer_records)
    core = [r for r in layer_records if r["layer"] == "core_indo_iranian"]
    core_by_subgroup = collections.Counter(r["subgroup"] for r in core)

    # Which cognate sets (core layer) span which subgroups (attested langs only)?
    cogset_subs = collections.defaultdict(set)
    cogset_langs = collections.defaultdict(set)
    cogset_liks = collections.defaultdict(set)  # a set may mix likelihoods across records
    for r in core:
        if r["is_proto"]:
            continue
        cogset_subs[r["cogset"]].add(r["subgroup"])
        cogset_langs[r["cogset"]].add(r["language"])
        cogset_liks[r["cogset"]].add(r["likelihood"])

    def lik_label(c):
        # honest per-set likelihood: single value if uniform, else "min..max"
        order = ["possible", "probable", "clear"]
        ls = sorted(cogset_liks[c], key=order.index)
        return ls[0] if len(ls) == 1 else f"{ls[0]}..{ls[-1]}"
    cross_branch = {c: sorted(s) for c, s in cogset_subs.items() if len(s) > 1}

    # The "widest" core-II sets (reach the most subgroups) = the anchor evidence.
    widest = sorted(cross_branch.items(), key=lambda x: -len(x[1]))

    # Samoyed participation (the key discriminator: Uralic root vs FU crown).
    samoyed_layer = [r for r in layer_records if r["subgroup"] == "Samoyed"]

    # ------------------------------------------------------------------ #
    # 3. Which subgroups does the CLEAR/CORE layer reach?                  #
    # ------------------------------------------------------------------ #
    clear_core = [r for r in core if r["likelihood"] == "clear" and not r["is_proto"]]
    clear_subs = sorted(set(r["subgroup"] for r in clear_core))
    core_subs = sorted(set(r["subgroup"] for r in core if not r["is_proto"]))
    subs_by_likelihood = {
        lik: sorted(set(r["subgroup"] for r in core
                        if r["likelihood"] == lik and not r["is_proto"]))
        for lik in ("clear", "probable", "possible")
    }

    empirical = {
        "ii_layer_labels_used": {
            "core_indo_iranian": sorted(cfg.II_CORE_LABELS),
            "indo_iranian_or_wider_ie": sorted(cfg.II_AMBIGUOUS_LABELS),
            "later_iranian": sorted(cfg.II_IRANIAN_LATER_LABELS),
        },
        "total_ii_layer_borrowing_records": len(layer_records),
        "ii_layer_records_by_subgroup": dict(by_subgroup),
        "core_indo_iranian_records": len(core),
        "core_by_subgroup": dict(core_by_subgroup),
        "core_subgroups_reached": core_subs,
        "clear_core_subgroups_reached": clear_subs,
        "core_subgroups_by_likelihood": subs_by_likelihood,
        "core_cross_branch_cognate_sets": len(cross_branch),
        "widest_core_ii_sets": [
            {"cogset": c, "meaning": params[c.split("-")[0]]["Name"],
             "subgroups": subs, "n_subgroups": len(subs),
             "likelihood": lik_label(c),
             "languages": sorted(cogset_langs[c])}
            for c, subs in widest[:8]
        ],
        "samoyed_ii_layer_records": [
            {"language": r["language"], "meaning": r["meaning"], "cogset": r["cogset"],
             "source": r["source"], "likelihood": r["likelihood"], "layer": r["layer"]}
            for r in samoyed_layer
        ],
    }

    # ------------------------------------------------------------------ #
    # 4. Node determination + branch-specific-reflex evidence.            #
    # ------------------------------------------------------------------ #
    # Pull the 'horn' set (40-a) reflexes to CHARACTERISE the item (one
    # representative major language per subgroup, avoiding outliers like the
    # Livonian form which has lost -v-). NB: these are illustrative only; see the
    # direction reasoning for why regular reflexes do NOT date the borrowing.
    representative = {"Finnic": "Standard Finnish", "Saami": "North Saami",
                      "Mordvin": "Erzya", "Mari": "Meadow Mari",
                      "Permic": "Komi-Zyrian", "Ugric": "Hungarian"}
    horn = [r for r in core if r["cogset"] == "40-a" and not r["is_proto"]]
    horn_by_sub = collections.defaultdict(dict)
    for r in horn:
        horn_by_sub[r["subgroup"]][r["language"]] = r["form"]
    horn_reflexes = {}
    for subgrp_name, langs in horn_by_sub.items():
        pref = representative.get(subgrp_name)
        if pref and pref in langs:
            horn_reflexes[subgrp_name] = f"{langs[pref]} ({pref})"
        else:
            lang = sorted(langs)[0]
            horn_reflexes[subgrp_name] = f"{langs[lang]} ({lang})"

    fu_taxa = [v["name"] for v in tables["varieties"]
               if v["subgroup"] in cfg.FINNO_UGRIC_SUBGROUPS]
    finno_permic_subs = {"Finnic", "Saami", "Mordvin", "Mari", "Permic"}  # FU minus Ugric
    fp_taxa = [v["name"] for v in tables["varieties"]
               if v["subgroup"] in finno_permic_subs]

    calibrated_node = {
        "node_label": "Proto-Finno-Ugric (Finno-Ugric crown)",
        "definition": ("Most recent common ancestor (MRCA) of all sampled Uralic "
                       "varieties EXCEPT the Samoyedic branch; i.e. the node uniting "
                       "Finnic + Saami + Mordvin + Mari + Permic + Ugric."),
        "mrca_taxon_set": fu_taxa,
        "excluded_from_taxon_set": ["Proto-Uralic* (reconstruction, sits at/above the root)",
                                    "Samoyedic varieties (Nganasan, Tundra Nenets, Selkup)"],
        "monophyly_assumption": ("Requires Finno-Ugric to be monophyletic (Samoyedic as the "
                                 "outgroup / first split). Enforce as a monophyly constraint or "
                                 "define the calibration on this MRCA taxon set."),
        "support": ("The core Indo-Iranian layer reaches ALL SIX Finno-Ugric branches. Ugric's "
                    "participation rests chiefly on 'horn' 40-a (probable) and 'house' 26-b "
                    "(possible); no Ugric core-II loan is coded 'clear'. See the conservative "
                    "alternative node for the clear-only reading."),
    }
    alternative_node = {
        "node_label": "Proto-Finno-Permic (Finno-Ugric crown minus Ugric)",
        "when_to_prefer": ("Prefer this if you anchor ONLY on UraLex 'clear' loans and treat "
                           "Ugric's participation in the oldest Indo-Iranian layer as unproven."),
        "definition": ("MRCA of Finnic + Saami + Mordvin + Mari + Permic (Ugric and Samoyedic "
                       "excluded)."),
        "mrca_taxon_set": fp_taxa,
        "support": ("The set of UraLex 'clear' core Indo-Iranian loans collectively spans exactly "
                    "these five branches (e.g. 'good' 57-b: Saami/Mordvin/Mari/Permic; 'green' "
                    "138-a: Finnic/Mari/Permic), and none reaches Ugric or Samoyed."),
        "effect": ("Shifts the calibrated node one level shallower (drops Ugric). The ~4000 BP "
                   "minimum-age bound and its direction are UNCHANGED; only which taxa bound "
                   "the node moves."),
    }

    # ------------------------------------------------------------------ #
    # 5. Calibration constraint (direction + distribution).               #
    # ------------------------------------------------------------------ #
    calibration = {
        "anchor_event": "Proto-Indo-Iranian ('Aryan') loanword contact layer entering Finno-Ugric",
        "anchor_age_years_BP": 4000,
        "anchor_age_basis": (
            "Proto-Indo-Iranian is dated to c. 2000 BCE on independent archaeological "
            "(Sintashta c. 2100-1800 BCE, early Andronovo horizon) and historical-linguistic "
            "grounds; c. 2000 BCE ~= 4000 years before present."),
        "constraint_type": "minimum_age (hard lower bound)",
        "constraint_direction_reasoning": (
            "Direction (minimum vs maximum) turns on whether the loans entered BEFORE or AFTER "
            "Finno-Ugric began to diverge. We adopt the MINIMUM (lower-bound) reading, resting it "
            "on the DISTRIBUTIONAL HETEROGENEITY of the layer, not on sound reflexes: most core "
            "Indo-Iranian loans reach only a SUBSET of branches (e.g. 'good' 57-b "
            "Saami/Mordvin/Mari/Permic; 'green' 138-a Finnic/Mari/Permic; 'sister' 279-a "
            "Mordvin/Permic; 'root' 9-c Mordvin/Saami), which is the signature of prolonged areal "
            "contact with an ALREADY-DIFFERENTIATING dialect network rather than a single borrowing "
            "into one unified proto-language (which would give uniform pan-branch distribution). If "
            "the branches were already separating when they took up the layer, their common ancestor "
            "(the FU crown) had already split by contact, so age(FU crown) >= age(contact) ~= 4000 BP. "
            "IMPORTANT HONEST CAVEAT: regular branch-specific SOUND reflexes do NOT by themselves "
            "settle the direction -- a word borrowed into an undivided ancestor and then inherited "
            "acquires each branch's regular reflexes too. The single pan-distributed item 'horn' 40-a "
            "(reconstructible to one form *sarwi with regular reflexes in every branch) is in fact "
            "equally consistent with borrowing into a still-unified ancestor, which would make ~4000 BP "
            "a MAXIMUM. We therefore do NOT rest the minimum reading on any single etymon; see the "
            "'Direction sensitivity' caveat. A minimum-age bound is also the more conservative "
            "calibration choice."),
        "constraint_value_years_BP": 4000,
        "not_proto_uralic_because": (
            "The clear/core Indo-Iranian loans are confined to Finno-Ugric and are essentially "
            "absent from Samoyedic. The handful of Samoyed-touching records do not pattern as "
            "clean vertical inheritance (see caveats), so the contact does not reach below the "
            "Samoyed split, i.e. not the Uralic root."),
        "deeper_than_branch_protolanguages_because": (
            "The same loan layer is shared ACROSS the Finno-Ugric branches (Finnic, Saami, "
            "Mordvin, Mari, Permic, Ugric), so it constrains their common ancestor, which is "
            "deeper than any single branch proto-language (Proto-Finnic, Proto-Saami, ...)."),
    }

    # Recommended BEAST2 prior forms (a minimum-age / one-tailed constraint).
    beast2 = {
        "target": "tmrca of the Finno-Ugric crown node (see mrca_taxon_set)",
        "interpretation": "node age (time before present) >= 4000 years; true age older, tail open",
        "recommended_prior": {
            "distribution": "Exponential",
            "offset_years_BP": 4000,
            "mean_years_above_offset": 1500,
            "note": ("Hard minimum at 4000 BP with a decaying tail into older ages; encodes "
                     "'at least 4000, probably somewhat older, no hard maximum'. Mean above "
                     "offset is a soft modelling choice, not derived from the loan evidence."),
        },
        "alternatives": [
            {"distribution": "Uniform", "lower_years_BP": 4000, "upper_years_BP": 8000,
             "note": "Non-committal minimum; upper bound is an arbitrary loose cap, adjust to taste."},
            {"distribution": "Lognormal", "offset_years_BP": 4000, "note":
             "Use if you want most mass just above the bound with a long right tail."},
        ],
        "caution": ("Do NOT encode this as a point age or a two-sided normal centred on 4000: "
                    "the evidence gives a floor, not an estimate, of the node's age."),
        "ascertainment_note": ("The matrix contains only observed/variable cognate characters "
                               "(constant-in-all-taxa characters were dropped); use BEAST2's "
                               "binary model with ascertainment-bias correction accordingly."),
        "proto_uralic_tip_note": ("Proto-Uralic* is a partial reconstruction, not a contemporaneous "
                                  "tip. Prefer treating it as an ancestral/root constraint or drop it "
                                  "from tip-dating rather than dating it as a leaf."),
    }

    caveats = [
        {"issue": "Samoyed 'rain' set 13-a (Finnic + Samoyed only)",
         "detail": ("An Indo-Iranian-flagged set reaches Finnic and Samoyed but SKIPS every "
                    "intermediate Finno-Ugric branch (Saami, Mordvin, Mari, Permic, Ugric). A single "
                    "borrowing into undivided Proto-Uralic would predict intermediate reflexes; their "
                    "absence makes parallel/areal borrowing or a Wanderwort more likely. Marked "
                    "'probable', and the Nganasan form is not even loan-flagged. Hence it does not "
                    "license a Proto-Uralic-level (Samoyed-inclusive) calibration."),
         "effect_on_call": "Does not move the node below the Samoyed split."},
        {"issue": "Selkup 'salt' 94-d (Iranian, single language)",
         "detail": ("A single-language, later-'Iranian' (post-split) loan into Selkup; younger layer, "
                    "irrelevant to the deep node."),
         "effect_on_call": "None."},
        {"issue": "UraLex Proto-Uralic* reconstructions attached to II-loan sets (e.g. 40-a *sarwi)",
         "detail": ("The compilers attach a Proto-Uralic* reconstruction to some II-loan etyma. This "
                    "reflects their maximal etymological depth judgement, not proof of Samoyed-inclusive "
                    "inheritance; the attested reflex distribution (absent from Samoyed) is the primary "
                    "signal used here."),
         "effect_on_call": "Node kept at FU crown, not Uralic root."},
        {"issue": "Ugric 'Iranian' (not core Indo-Iranian) loans",
         "detail": ("Hungarian in particular has famous LATER Iranian/Alanic loans. Those are excluded "
                    "from the core-II anchor; Ugric still participates in the core Indo-Iranian layer "
                    "(e.g. shares 'horn' 40-a and 'house' 26-b), so the crown remains inclusive of Ugric."),
         "effect_on_call": "Ugric retained inside the calibrated clade."},
        {"issue": "Direction sensitivity (minimum vs maximum) -- the main limitation",
         "detail": ("Regular branch-specific sound reflexes do NOT discriminate the two scenarios: a "
                    "word borrowed into an undivided ancestor and then inherited would show the same "
                    "regular per-branch correspondences as one borrowed into already-separated branches. "
                    "The flagship pan-distributed item 'horn' 40-a even fits the UNDIVIDED-ancestor "
                    "reading (single reconstructible *sarwi, all branches), under which ~4000 BP would be "
                    "a MAXIMUM, not a minimum. We adopt the MINIMUM reading on the strength of the "
                    "LAYER's distributional heterogeneity (most core loans reach only a subset of "
                    "branches -> areal spread across an already-differentiating network) plus the "
                    "conservatism of a lower bound -- NOT on the reflex pattern of any single etymon. An "
                    "analyst who reads the layer as pre-divergence should flip this to a maximum-age "
                    "bound on the same node."),
         "effect_on_call": "Determines lower- vs upper-bound; we use a lower bound but flag this as interpretive."},
    ]

    scheme = {
        "title": "UraLex 2.0 — Indo-Iranian contact-layer calibration for Uralic (BEAST2)",
        "generated_by": "stages/stage5_calibration.py (no inference performed)",
        "dataset": {"name": "UraLex", "version": cfg.URALEX_VERSION,
                    "commit": cfg.URALEX_COMMIT, "doi": cfg.URALEX_DOI},
        "calibrated_node": calibrated_node,
        "alternative_conservative_node": alternative_node,
        "calibration": calibration,
        "beast2_prior": beast2,
        "branch_specific_reflex_evidence": {
            "example_set": "40-a 'horn' (Indo-Iranian loan)",
            "reflexes_by_subgroup": horn_reflexes,
            "point": ("The one loan surfaces with each branch's regular phonology (the differing "
                      "outcomes of Proto-Uralic *s and the branch vowel systems). This CHARACTERISES "
                      "the item and shows it is fully integrated into every branch -- but it does NOT, "
                      "on its own, date the borrowing relative to branch divergence: inheritance from a "
                      "unified ancestor and borrowing into already-separated branches BOTH yield regular "
                      "reflexes. Included for description, not as evidence for the minimum-age direction "
                      "(see constraint_direction_reasoning and the Direction sensitivity caveat)."),
        },
        "empirical_distribution": empirical,
        "caveats_and_sensitivity": caveats,
        "one_line_summary": (
            "The Indo-Iranian (Proto-Indo-Iranian, ~4000 BP) loan layer is shared across all six "
            "Finno-Ugric branches but essentially absent from Samoyedic, and -- distributed patchily "
            "over branch-subsets rather than as one uniform pan-branch stratum -- is read as areal "
            "contact with an already-differentiating Finno-Ugric; it therefore places a MINIMUM age of "
            "~4000 BP on the Finno-Ugric crown node (deeper than any branch proto-language, shallower "
            "than Proto-Uralic). The minimum-vs-maximum direction is interpretation-dependent (see "
            "caveats)."),
    }

    with open(os.path.join(cfg.ARTIFACTS_DIR, "calibration_scheme.json"), "w") as f:
        json.dump(scheme, f, indent=2, ensure_ascii=False)

    # Also a flat CSV of the core-II cross-branch sets for quick inspection.
    with open(os.path.join(cfg.ARTIFACTS_DIR, "indo_iranian_layer_sets.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["cogset", "meaning", "n_subgroups", "subgroups", "likelihood", "languages"])
        for c, subs in widest:
            w.writerow([c, params[c.split("-")[0]]["Name"], len(subs), "; ".join(subs),
                        lik_label(c), "; ".join(sorted(cogset_langs[c]))])

    print("[stage5] II-layer records:", len(layer_records), "| core:", len(core))
    print("[stage5] core II by subgroup:", dict(core_by_subgroup))
    print("[stage5] core subgroups reached:", core_subs)
    print("[stage5] clear-core subgroups reached:", clear_subs)
    print("[stage5] Samoyed II records:", len(samoyed_layer))
    print("[stage5] subgroups by likelihood:", subs_by_likelihood)
    print("[stage5] PRIMARY node:", calibrated_node["node_label"])
    print("[stage5] conservative alt:", alternative_node["node_label"])
    print("[stage5] constraint:", calibration["constraint_type"], "@", calibration["constraint_value_years_BP"], "BP")
    return scheme


if __name__ == "__main__":
    run()
