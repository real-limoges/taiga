# Vendored UraLex v2.0 CLDF subset

These files are a **verbatim snapshot** of a subset of the UraLex 2.0 CLDF
Wordlist, vendored here so that the curation stages in `stages/` are fully
reproducible without network access in an ephemeral environment.

| Field | Value |
| --- | --- |
| Dataset | UraLex — Uralic basic vocabulary with cognate and loanword information |
| Version | 2.0 (CLDF release) |
| Upstream repo | https://github.com/lexibank/uralex |
| Pinned git commit | `0ce4fc7ea8147c9b3175b786eccf87d3a1c7f7e1` (`git describe`: `0ce4fc7`) |
| Concept DOI | 10.5281/zenodo.4777568 |
| License | Creative Commons Attribution 4.0 (CC-BY-4.0) — see `LICENSE_UraLex.txt` |
| CLDF conformsTo | CLDF Wordlist |

## Files vendored (only the tables the pipeline reads)

- `languages.csv` — LanguageTable (43 rows; 27 appear in `forms.csv`)
- `parameters.csv` — ParameterTable (313 meanings)
- `forms.csv` — FormTable (10,231 forms, incl. gap-marker rows)
- `cognates.csv` — CognateTable (9,751 root-meaning judgements)
- `borrowings.csv` — BorrowingTable (2,184 borrowing records)
- `cldf-metadata.json` — the CLDF metadata (column descriptions)

The full dataset (raw TSVs, sources.bib, documentation) lives upstream at the
pinned commit above. Nothing in these files was altered.

## How to cite (per upstream `uralex_documentation.md`)

> De Heer, Mervi; Rogier Blokland; Michael Dunn & Outi Vesakoski. 2024.
> "Loanwords in basic vocabulary as an indicator of borrowing profiles."
> *Journal of Language Contact* 16(1). 54–103.
> https://doi.org/10.1163/19552629-bja10057

> Syrjänen, Kaj, Luke Maurits, Unni-Päivä Leino, Terhi Honkola, Jadranka Rota
> & Outi Vesakoski. 2021. "Crouching TIGER, hidden structure: Exploring the
> nature of linguistic data using TIGER values." *Journal of Language
> Evolution* 6(2). 99–118. https://doi.org/10.1093/jole/lzab004

Please also cite the UraLex 2.0 Zenodo DOI when using this material.
