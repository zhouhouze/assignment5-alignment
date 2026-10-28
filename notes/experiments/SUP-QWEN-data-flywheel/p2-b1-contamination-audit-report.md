# P2-B.1 Contamination Audit Execution Report

Date: 2026-10-28 (Asia/Shanghai). **Execution PASS; contamination clearance NOT established; Data Admission PENDING / NOT APPROVED.** Qwen Adapted Reproduction; directly_comparable_to_official=false. Work branch learning/pa5-supplement.

## Goal / Authorized scope

Read-only CPU exact and near-duplicate candidate audit of accepted derived-v1 train/validation and the four frozen evaluation benchmarks. No filtering, rewriting, split changes, human adjudication, P2-B.2/P2-B.3/P3, training, weights download or GPU. Source user authorization is this conversation's P2-B.1 request.

## Relevant Official Sources / Input identity

[Frozen SFT Policy v1](sft-data-quality-plan.md), [P2-A.2 execution](../SUP-QWEN-02-sft/p2-a2-derived-report.md), [frozen evaluation protocol](../SUP-QWEN-evaluation/evaluation-protocol-v1.md), [archive policy](../archive-policy.md). Actual local files and baseline loader schema were inspected; no alternative versions downloaded.

Derived directory `/Users/hr/Documents/Lesson/pa5-experiment-backups/sft/20261028-p2a2-derived-v1`: all three data files, mappings, exclusions, manifest and DATA/METADATA checksums verified before execution; repeated full input hash checks after execution. A.2 manifest SHA=c9eaf0e154f073500c237d6242a3d4188cdaf15e715a183e23d164813d3c352f; accepted report binding checked. Train 210326 / Validation 23108; Sample1000 identity checked but not treated as independent validation or re-scanned as a second training corpus.

60 benchmark file hashes and ordered ID hashes match protocol. Dataset inventory SHA=8ae5c03b4f261bd7c10dd31056efde8c87b34cf580ee90f4c6aaf856ab684e55. [Complete identity ledger](../../../artifacts/pa5-supplement-qwen/sft/20261028-p2b1/benchmark-inventory.json) contains every file SHA, task source and fields. Upstream release revisions are **unknown in available archives**; fixed version here means the actual frozen local bytes, not latest upstream or an invented release.

| Benchmark | Split / N | Matching fields | Answers/scoring information |
|---|---|---|---|
| MMLU (57 subjects) | test / 14042 | question; question+four options; correct option text | Gold A–D present and used to select option text; label alone excluded; distractors only in combined field |
| GSM8K | test / 1319 | question; full answer | Answer includes rationale and #### gold numeral; numeral-only matching not assessed |
| AlpacaEval | eval / 805 | instruction; fixed output | All reference generators gpt4_1106_preview; no Judge/LC scores. Source labels helpful_base129/koala156/oasst188/selfinstruct252/vicuna80 |
| SimpleSafetyTests | test / 100 | prompts_final | No reference/model score; id, category, harm_area, counter excluded from text matching |

## Concept and Formula / Data contract

No tensors. Read immutable records plus source mapping → temporary normalized index → candidate ledger with source row IDs, target record/field/file SHA, text SHA, excerpts and scores → input integrity recheck. Each training prompt and response is compared with all target field types; train/validation serialized prompt-response pairs additionally receive raw exact matching only. Cross-field matches are reported separately, not confused with prompt/pair identity.

Methods, fixed before execution:

1. **Exact Match**: complete original string equality, no length threshold. SHA lookup followed by string comparison. Serialized pair exact matching applies to train/validation.
2. **Near Duplicate Candidate / normalized_equal**: NFKC + casefold + Unicode word tokenization `[^\W_]+`, token sequence equality. Spaces/punctuation are discarded in the index only. Nonempty normalized values, including short values, are eligible; short hits carry a low-specificity flag.
3. **Near Duplicate Candidate / ngram_candidate**: word 5-gram sets, deterministic BLAKE2b-64; keep each target's 8 smallest hashes as anchors. Query all train grams, require ≥2 shared anchors to score. Require both texts ≥12 tokens, ≥8 shared distinct grams, and **Jaccard ≥0.80 OR shorter-set containment ≥0.90**. Jaccard=intersection/union; containment=intersection/min(set sizes).
4. **Potential Semantic Contamination: NOT ASSESSED**. No embedding/model/human semantic verdict. Unretrieved pairs, short-text fuzzy matching and unknown upstream provenance remain unresolved, not negative findings.

Parameters are detection settings, not changes to frozen Data Admission Policy. No template stripping or data normalization persisted. Per field pair, precedence exact→normalized_equal→ngram prevents duplicate classification. Different fields for the same record pair can still yield multiple hits; both denominators are reported.

Complexity: index target grams O(target tokens × log8) for anchor selection plus exact hashes; stream all training fields once, then posting traversal and candidate set-intersection scoring. Not an exhaustive Cartesian comparison. Worst-case shared templates can expand retrieval; resource caps enforce stopping without silently dropping candidates. **No recall guarantee**: ≥2 bottom-8 anchors may miss high-similarity pairs. Pure paraphrase, translation, equation/code punctuation changes, answer embedded only in a long document, and tokenizer behavior on non-space-separated languages can be missed. 64-bit hash collision risk is nonzero; emitted candidate scores were independently rechecked with unhashed tuples.

## Tests / Changes Made

New scripts/audit_qwen_contamination.py and tests/test_qwen_contamination.py; prior tools/tests/Policy/data untouched. Interpreter `/Users/hr/Documents/Lesson/assignment5-alignment/.venv/bin/python`.

- `python -m pytest tests/test_qwen_contamination.py -q`: **20 PASS**, 0.02s; exact, whitespace/punctuation/case/NFKC, local edits/shared template, containment, unrelated, short-text control, four schemas, dedup, SHA, path/overwrite and comparison budget.
- `python -m pytest tests/test_qwen_sft_derived.py tests/test_qwen_sft_raw.py tests/test_qwen_preflight.py -q`: **48 PASS**, 0.47s.
- `python -m pytest tests/test_grpo.py -q`: **19 FAIL**, 0.12s; unchanged pre-existing NotImplementedError, not passing tests/new regressions. Logs retained without modifying assertions.

Tests ran on e301cbb plus new files; exact source hashes in [test provenance](../../../artifacts/pa5-supplement-qwen/sft/20261028-p2b1-tests/provenance.json). Code commit `3f909c4a63323088da8c46cca812d37c758d1f97` fixed before actual run.

## Actual execution / Resources

Working directory: `/Users/hr/Documents/Lesson/assignment5-alignment/tmp/pa5-supplement`.

`/Users/hr/Documents/Lesson/assignment5-alignment/.venv/bin/python scripts/audit_qwen_contamination.py --derived /Users/hr/Documents/Lesson/pa5-experiment-backups/sft/20261028-p2a2-derived-v1 --output /Users/hr/Documents/Lesson/pa5-experiment-backups/sft/20261028-p2b1-audit`

Wall=94.197s; CPU=93.660s; peak RSS=1781399552 bytes (1.659 GiB); original run directory=1063626 bytes. Index115798 target fields; train420652 prompt/response fields plus210326 exact pairs; scored642848 retrieved field comparisons. All210326 train rows scanned. Host physical RAM24GiB, observed free disk243GiB. Caps: 900s, peak4GiB, output2GB, 10million scored comparisons, 1million emitted candidates. None reached. No weights/model/GPU loaded.

## Results

**3732 field-pair hits**, complete list retained. Table methods are mutually exclusive per field pair; unique record pairs are deduplicated across methods and fields. Target-hit rate is candidate coverage, **not contamination prevalence or confirmed leakage rate**.

| Target | N | Exact field hits | Normalized-equal hits | N-gram hits | Unique record pairs | Matched train rows | Matched target rows / target rate |
|---|---:|---:|---:|---:|---:|---:|---|
| validation | 23108 | 2 | 6 | 3593 | 3559 | 3419 | 2685 (11.6194%) |
| mmlu | 14042 | 14 | 112 | 0 | 126 | 21 | 124 (0.8831%) |
| gsm8k | 1319 | 0 | 0 | 0 | 0 | 0 | 0 (0.0000%) |
| alpaca_eval | 805 | 5 | 0 | 0 | 4 | 4 | 2 (0.2484%) |
| simple_safety_tests | 100 | 0 | 0 | 0 | 0 | 0 | 0 (0.0000%) |

| Target | Method | Field hits | Train-row hit rate | Target-row hit rate |
|---|---|---:|---|---|
| alpaca_eval | exact | 5 | 4/210326 (0.0019%) | 2/805 (0.2484%) |
| mmlu | exact | 14 | 3/210326 (0.0014%) | 14/14042 (0.0997%) |
| mmlu | normalized_equal | 112 | 20/210326 (0.0095%) | 110/14042 (0.7834%) |
| validation | exact | 2 | 2/210326 (0.0010%) | 2/23108 (0.0087%) |
| validation | ngram_candidate | 3593 | 3411/210326 (1.6218%) | 2680/23108 (11.5977%) |
| validation | normalized_equal | 6 | 6/210326 (0.0029%) | 6/23108 (0.0260%) |

Absent task/method rows have0 observed hits, not guaranteed absence of contamination.

Train/validation **raw exact prompt=0 and exact pair=0**, consistent with A.2. The2 exact hits are response→prompt1 and response→response1. Normalized equality includes3 prompt→prompt and3 response→response. N-gram3593 includes prompt→prompt3444, prompt→response35, response→prompt18, response→response96. This is broader than the original exact prompt/pair audit.

MMLU14 exact +112 normalized hits all target correct_option_text and all are short; **no MMLU question or question+options hit**. Alpaca5 exact field hits form4 record pairs: three generic “Yes.” responses matching reference262, plus train source line181453 with both instruction and response matching Alpaca370's common Australia-capital Q/A. This is observed string identity, not proof of copying/provenance. GSM8K/SST have no emitted hits under these methods.

### Coverage limits

Train near-ineligible fields: prompt16313, response1601 (<12 tokens). Exact/normalized equality still checked. Target fields without n-gram scoring:

| Target | Field | Count |
|---|---|---:|
| alpaca_eval | gpt4_reference_output | 15 |
| alpaca_eval | instruction | 223 |
| gsm8k | answer_rationale_and_gold | 1 |
| mmlu | correct_option_text | 11109 |
| mmlu | question | 3466 |
| mmlu | question_with_options | 135 |
| simple_safety_tests | prompts_final | 54 |
| validation | pair | 23108 |
| validation | prompt | 1631 |
| validation | response | 179 |

Validation pair23108 is deliberately exact-only, not23108 missing prompt/response audits. For SST,54/100 prompts have no fuzzy matching; Alpaca223/805 instructions; MMLU3466/14042 questions. No embedding or multilingual semantic recall claim.

## Representative Evidence / Error Analysis

[Representative records](../../../artifacts/pa5-supplement-qwen/sft/20261028-p2b1/representative-candidates.jsonl) retain original references and human_review_status=pending. Full source_row_id includes Raw SHA:split:physical-line; target benchmark IDs use frozen zero-based IDs/subject IDs.

- Candidate1: train source14 ↔ validation source9092, prompt→prompt, Jaccard0.815873 / containment0.914591. Different instructions reference overlapping long news material. A concrete question-cluster isolation risk deserving later adjudication; not automatically removed.
- Candidate2737: train source151747 ↔ validation source16549, response→response, Jaccard0.014986 / containment1.0 (11 shared grams). A short quotation contained in a much longer answer illustrates containment/template/common-material false-positive risk; a high containment score alone does not establish leakage.
- Candidate85: train source6077 ↔ MMLU high_school_biology:54 correct option: normalized “S ...” vs “S”. Punctuation removal/short text is weak evidence.
- Candidate1242: train source66689 ↔ MMLU global_facts:47, literal “45%”. Generic numeric equality is not sufficient to identify a leaked question.
- Candidate1584: train source86659 ↔ Alpaca262, generic “Yes.” reference match. Low specificity.
- Candidates3273/3274: train source181453 ↔ Alpaca370, identical common factual Q/A. Preserve as observed exact overlap; causal source contamination unresolved.
- Candidate1169: train source63196 ↔ validation source8997, common quotation differing in case. Normalized equality is correctly detected; independence/acceptability requires later policy decision.

These are AI observations of machine evidence, not human-confirmed false positives/contamination. Original content remains unchanged; no records quarantined, filtered or moved.

## Independent verification and failure record

All3732 candidate text SHA/excerpts, original source mapping locations, similarity scores using independent **unhashed tuple 5-grams**, candidate uniqueness and summary record-pair counts passed a separate readback. All four ordered benchmark ID hashes match protocol. This validates emitted hits, not recall/non-hits.

The auxiliary readback initially failed with FileNotFoundError because `parents[5]` addressed the parent directory instead of the repository. It stopped immediately; original script and failure record preserved. Only that script's root calculation was corrected to `parents[4]`, then all candidate checks passed. No audit rerun, threshold/data repair or silent deletion occurred. Readback source executed before archival commit; its SHA is in candidate-recheck.json. Primary audit itself had no identity/resource/schema failure.

## Artifacts / Reproducibility / Archival

[Evidence directory](../../../artifacts/pa5-supplement-qwen/sft/20261028-p2b1) includes audit.json, complete candidates.jsonl.gz, benchmark inventory, aggregate, representatives, candidate recheck source/result/failure, execution log and checksums. Candidate file SHA=`256563a0f534ee87d3529769445fdae2ac80ef8569e74f62572aeb8a70892569`, bytes=1028861. Full list is small enough for ordinary Git; full training data is not committed. Original execution output retained at `/Users/hr/Documents/Lesson/pa5-experiment-backups/sft/20261028-p2b1-audit`, on persistent local Mac filesystem; no off-device guarantee for that local copy. Git evidence is separately committed/pushed on learning/pa5-supplement.

Restore small evidence from archive commit and verify root-relative SHA256SUMS. Restore Derived from registered A.2 archive (or pinned Raw + committed derivation) following its report; benchmark files must match the60-file inventory. Checkout execution commit and run the command into a **new** output directory. Candidate ordering/hashes are deterministic for fixed Python/Unicode implementation and inputs; timestamps/resource metrics vary. Missing input or SHA mismatch stops; no auto-download/replacement. Unicode database version comes from the recorded Python3.12 environment; cross-runtime normalization may change.

## Data Admission / Next Gate / Learning Check

Machine audit execution is PASS; **Data Admission remains PENDING / NOT APPROVED**. Shared long-material candidates and normalized prompt matches require disposition; short benchmark matches need context/provenance review; semantic contamination is Not Assessed. No risk thresholds or approvals are inferred from string scores. Recommend a separately authorized next review Gate to triage candidate1-like long-material/cluster risks, normalized prompt matches and the exact Alpaca Q/A, while separating low-information hits. Do not launch P2-B.2/P2-B.3/P3 automatically.

Learner explanation status=PENDING. Suggested check: why exact short answers do not prove leakage, why containment may be1 with low Jaccard, and why zero hits is not semantic clearance. Stop after archival and user acceptance.
