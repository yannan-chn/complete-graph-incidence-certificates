# Complete-graph incidence reconstruction package

Version 1.0.0-2026-10-10. All ten target grids are **VERIFIED** by actual
unsigned five-rule closure and independent verification of a finite proof.

`217.csv`, `288.csv` and `369.csv` transcribe Tables 10, 9 and 8 of the supplied
PDF. The seven other grids are independently searched replacement witnesses,
not asserted recovered originals. Table 7 diagnostics and some Table 1
restriction counts change for these replacement witnesses. Use the actual
counts below and in `verification_summary.csv`.

## Format and mathematics

Each CSV has no header, exactly m rows and n columns. Columns are vertices
1,...,n. Rows are the lexicographic pairs (1,2),(1,3),...,(n-1,n).
An empty field is a singleton, a positive integer occurs exactly twice and
specifies an unordered selected pair, and `.` is a hole. Labels are not
initial equivalences. Supports are disjoint because each cell has one token.
The singleton audit checks the actual K_n incidence matrix, the C4-free
column-pair count, and |E1|=2m=z(m,n), independently of expected table values.

For m=binom(n,2), the target is R=floor(n(n-1)(n+2)/4). All five rules are
implemented at their prescribed values. A hole never makes an opposite
selected pair orthogonal: it identifies that pair. No signed odd-cycle
inference is used. All selected pair ends must be identified, different
selected edges must remain in different classes, and their classes must be
pairwise orthogonal. Failure is UNVERIFIED, not proof of reducibility.

## Environment and working directory

Run from the extracted package root, which contains `ancillary`, `logs` and
`report`. The tested environment was Python 3.12.14, NumPy 2.3.5. Core
programs use only the Python standard library and NumPy. The slow reference
implementation is intended for small cases. Optional source re-extraction
requires the Poppler `pdftotext` executable; optional report compilation
requires pdflatex and the amsmath, amssymb, geometry, booktabs and hyperref
packages. No parallel random streams were used.

```bash
python -m pip install -r ancillary/requirements.txt
python ancillary/validate_all.py
python ancillary/test_checker.py
python ancillary/regenerate_all.py ../fresh_reconstruction
```

The validation command checks every CSV digest, independently reruns closure,
then verifies the finite saved proof with a different rectangle implementation.
Expected final line: `ALL TEN VERIFIED`. Nine tests must pass. Regeneration
requires a new destination, reconstructs the seven searched files in order,
and checks that all seven match the distributed CSV bytes exactly. Expected
final line: `ALL SEVEN SEARCHED GRIDS REPRODUCED BYTE FOR BYTE`.

## Per-sheet index and expected output

For each row below, replace STEM in these commands by its filename without
`.csv`:

```bash
python ancillary/certificate_checker.py ancillary/STEM.csv
python ancillary/verify_certificate.py ancillary/STEM.csv logs/STEM_certificate.npz
```

The closure command returns JSON status VERIFIED; the proof command returns
CERTIFICATE_VERIFIED. Every row has zero unresolved class pairs, no conflict,
all selected pairs identified, and exactly R occupied equivalence classes.

| File | m | n | E1 | E2 | H | R | Orthogonal class pairs | Closure rounds |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 217.csv | 21 | 7 | 42 | 52 | 1 | 94 | 4371 | 41 |
| 288.csv | 28 | 8 | 56 | 84 | 0 | 140 | 9730 | 39 |
| 369.csv | 36 | 9 | 72 | 126 | 0 | 198 | 19503 | 12 |
| 6612.csv | 66 | 12 | 132 | 330 | 0 | 462 | 106491 | 28 |
| 7813.csv | 78 | 13 | 156 | 429 | 0 | 585 | 170820 | 16 |
| 12016.csv | 120 | 16 | 240 | 840 | 0 | 1080 | 582660 | 18 |
| 13617.csv | 136 | 17 | 272 | 1020 | 0 | 1292 | 833986 | 14 |
| 15318.csv | 153 | 18 | 306 | 1224 | 0 | 1530 | 1169685 | 34 |
| 19020.csv | 190 | 20 | 380 | 1710 | 0 | 2090 | 2183005 | 16 |
| 21021.csv | 210 | 21 | 420 | 1995 | 0 | 2415 | 2914905 | 14 |

Actual per-sheet outputs: `logs/STEM.json`. Finite proofs:
`logs/STEM_certificate.npz`. Independent verification results:
`logs/STEM_certificate_verification.json`. Whole-package replay:
`logs/final_validation.txt`. Small-case and random tests: `logs/tests.txt`.
Successful regeneration of all seven: `logs/reproduction.json` and
`logs/reproduction_stdout.txt`. Times are measurements of this run, not
guaranteed runtimes. Closure seconds exclude proof compression.

## Finite proof format

The NPZ files contain no pickle objects. `shape` records m,n and
`holes_enabled` the zero-companion convention. `initial_equal` and
`initial_ortho` encode line and complementary initialization; `zero_equal`
and `zero_ortho` encode the hole stage. `orth_i` is the packed cell-level
orthogonality store after saturation and rectangle transfer in round i;
`merges_i` lists new selected-pair identifications, with zero-based label
indices. Matrices have (mn)^2 bits in row-major order; unpack with
`np.unpackbits(..., count=(mn)**2).reshape(mn,mn)`, default big bit order.
An occupied cell's self-equivalence is included; a hole is excluded.

The verifier independently enumerates rectangles and checks that every
claimed round is exactly the legal result of its previous-round premises.
It then independently checks all terminal conditions. It does not invoke
the main closure routine or trust R choose 2 as an observed count. Tampered
proofs are rejected. The full synchronous trace costs O(L(mn)^2) bits before
compression, and the dense verifier has O((mn)^2) working memory.

Rule diagnostics count pair identifications in priority order line,
complementary, zero companion, then iterative transfer. Orthogonality JSON
statistics separately count new unordered **cell** pairs by line, zero,
saturation and transfer; they differ from selected-edge class-pair counts.
The complementary rule identifies pairs; it directly adds no orthogonality.

## Search reconstruction

All successful searches use seed 20261010 with `numpy.random.default_rng`.
The implementation is `reconstruct.py`; the exact replay is
`regenerate_all.py`. n=13 and n=12 use the preserved basic strategy; the
others use the targeted strategy. Complete parent factor and inner-label
orders are specified in the report and generator. The q=9 parent uses the
cyclic Z17 factorization, not the exploratory composite bipyramidal attempt.
No inherited pair was deliberately broken in the successful searches.

| n | Parent | Retained pairs | Free cells | Strategy | Success attempt, zero-based |
|---:|---|---:|---:|---|---:|
| 12 | 7813.csv | 236 | 188 | basic | 244 |
| 13 | nested q=7 | 312 | 234 | basic | 67 |
| 16 | nested q=9 | 528 | 624 | targeted | 10 |
| 17 | nested q=9 | 816 | 408 | targeted | 7 |
| 18 | nested q=11 | 552 | 1344 | targeted | 25 |
| 20 | nested q=11 | 1200 | 1020 | targeted | 15 |
| 21 | nested q=11 | 1680 | 630 | targeted | 10 |

Detailed parameters and scores are in `logs/STEM_search.jsonl`. Each
original search had a 180-second budget and the recorded attempt cap.
For byte-for-byte replay the regeneration script disables the time cutoff
and preserves the attempt cap. Targeted proposals that repeat a pair block
are skipped; the loop's attempt index therefore need not equal the number
of scored candidates. Wall-clock times are not part of the deterministic
acceptance or hash comparison.

At n=7 the hole is row {2,7}, column 4. Run:

```bash
python ancillary/certificate_checker.py ancillary/217.csv --no-holes
python ancillary/grounded_components.py ancillary/217.csv --no-holes
```

Expected UNVERIFIED in the first experiment, with all 52 selected pairs
identified but 21 uncertified class pairs; this deliberate negative test
returns exit code 1. The quotient has 322 components, of which 16 are
ungrounded: twelve singleton components, three size-two components and
one size-three component. Enabling holes accepts all 4371 class pairs.
The q=9 cyclic parent leaves 7344 pairs uncertified, matching the supplied
manuscript. Failed exploratory inputs are retained under explicitly marked
`logs/exploratory_*` filenames and are not successful target witnesses.

To repeat PDF transcription, with the original supplied source file:

```bash
python ancillary/extract_printed.py '/path/to/more(5).pdf' ../printed_extraction
```

## Actual checksums

`ancillary/SHA256SUMS` covers all distributed files except itself and
transient bytecode. Verify from the package root:

```bash
sha256sum -c ancillary/SHA256SUMS
```

CSV digests, bound to the actual distributed bytes:

```text
e63ffcf8b8e1c11bdcfcda5353bbdfe1cf28fa69ebd466008b7497ad30659df5  ancillary/217.csv
f5ff5fe05f9c17a35e5b9c7709efc8d5cca0588bd4ae2dc55228c91ef55f13b3  ancillary/288.csv
5b2eea69bee35acd0abef992d91f7bf91cfd3705d3b2fa71ebc5fb97bd73aea5  ancillary/369.csv
2fc519a336bbec4f3ea2c4fe40b6807ae93db990ae06a6f5e3920c15625f1844  ancillary/6612.csv
618e00ba4e24ea16c1dd9297918b0aade6a24f745aacfbc19c7c1724c6429189  ancillary/7813.csv
1dd48846ca9d7270d197520aeb2e1d432453af65ae4054f9f4c6a6b110250981  ancillary/12016.csv
5e96d7e9b83abaded2596629e0a46de921e9b6fb931e55ef018b255a5debb2cf  ancillary/13617.csv
95e8793c5fc2a52cf5aaef5520f18cd00eb84a410ae0caa0ee2173587ab2779e  ancillary/15318.csv
749fd79aa1676ba237295446109ff0e638c786f283c116af949db2a68e087c79  ancillary/19020.csv
4f7f956078cb7cc7efcdebbf1367274aa5236eb7af752869a9fdad1890dace47  ancillary/21021.csv
```

`provenance.json` also records the input PDF digests, environment, sources,
search seeds and successful attempt indices. Do not describe these seven
new larger grids as the unpublished original sheets. For submission, attach
this actual package and revise the manuscript's provenance and replay tables.
Public reproducibility additionally requires depositing this package at an
immutable archive; no archive URL is asserted here. The unrelated flagged
seven-column cases with 9<=m<=16 remain outside this package's scope.
