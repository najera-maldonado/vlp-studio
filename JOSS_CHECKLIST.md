# JOSS submission checklist — VLP Studio

Status of this repository against the Journal of Open Source Software submission
requirements and reviewer checklist, as of **2026-10-04**.

**How to read this.** Three markers are used throughout:

| Marker | Meaning |
|--------|---------|
| **DONE** | In the repository now, nothing further needed |
| **AUTHOR** | Blocked on Lucio: it needs an account, an identity, a judgement call or a scientific run that nobody else can supply |
| **OPEN** | Can be finished without Lucio, but is not done yet |

Nothing in the **AUTHOR** list can be done by a collaborator or an assistant. Everything in
that list is blocking except where it says otherwise.

---

## 0. Revision of 2026-10-05 — what the engine audits changed

This checklist was first written on 2026-10-04 **from the documentation**, before the four
independent engine audits of the same day had concluded. Several of its **DONE** marks were
not true of the code. They are corrected below; the evidence for each is in
[`CORRECCIONES_DOCUMENTACION.md`](CORRECCIONES_DOCUMENTACION.md), and the consolidated repair
plan is `HOJA_DE_RUTA.md` (branch `claude/consolidate-audit-roadmap-k82rek`).

| Earlier claim | Reality | Status now |
|---|---|---|
| "Reproducibility: fixed Packmol seeds, golden regression test" | The configured seed base is read by no module; production draws random seeds. The golden test covers gate 1's `substrate_section`, not packing. Packing-engine test coverage is zero | **OPEN** (PK-4, PK-5) |
| "Gates 1 and 2 are real" / "Functionality works as described" | Both engines run, but gate 2's acceptance criterion never fires and its fallback accepts the capsid alone (a Packmol double placing 0 enzymes yields "100, σ = 0"); gate 1's only committed result is the wild type measured off-axis | **OPEN**: either repair first (PK-1…PK-5, PO-1, PO-3, PO-6, PO-7: ~6 days) or submit with both gates labelled "engine wired, result under review", as the documentation now does. Decision DC-1, author only |
| "Licence is clearly stated" | `THIRD_PARTY.md` listed SIRAH among engines not redistributed; the repository versions 146 files of SIRAH 2.3 including GPL `tools/`. Now disclosed; the decision to keep or remove the bundle is open | **AUTHOR** (DC-5) |
| "No git tags exist in this clone" (§1.2) | Tags exist on the remote: `v0.1.0`, `studio/v0.1.0`, `poromania/v1.2.0`, `packman/v1.2.0`, `sustratinaitor/v0.1.0` (`git ls-remote --tags origin`). Only the Zenodo archive is pending | corrected in §1.2 |
| Gate 4 "complete, runnable protocol" | The committed inputs are 10 ps stubs titled 15/35 ns (≈ 240 ps total) plus eight all-atom files; the automated preparation path yields a topology without hydrogens or `TER`. Not runnable as committed | documented as such everywhere |

**Minimum before submitting**, whichever way DC-1 goes: this checklist, `paper.md`, the root
README and the engine READMEs must say the same thing, and today they do (this revision).
If the choice is to repair first, re-run this table after PK-5 and PO-7.

---

## 1. Blocking items — Lucio only

### 1.1 Zenodo archive and DOI — **AUTHOR, blocking**

JOSS will not accept a submission without a permanent archive DOI, and the archive has to
match the released version exactly.

1. Sign in at <https://zenodo.org> with the GitHub account and enable the integration for
   `najera-maldonado/vlp-studio` (Zenodo → GitHub → toggle the repository on). The
   repository is already public, which is the only precondition, so this is a two-minute
   step.
2. Create a **tagged GitHub release** (see 1.2). Zenodo then mints the DOI automatically for
   that tag.
3. On the Zenodo record, check that the **title, author name and licence match** `paper.md`
   and `CITATION.cff`. JOSS editors verify this, and a mismatch is the single most common
   cause of a submission being bounced before review.
4. Add the DOI badge to `README.md` and the `doi:` field to `CITATION.cff`.

### 1.2 Tagged release — **AUTHOR, partly done**

The repository has a v0.1.0 GitHub release and the tags **do exist on the remote**
(`git ls-remote --tags origin`: `v0.1.0`, `studio/v0.1.0`, `poromania/v1.2.0`,
`packman/v1.2.0`, `sustratinaitor/v0.1.0`); an earlier version of this checklist said
otherwise because the clone it was written from had not fetched them. What remains is to
decide whether `v0.1.0` (which predates the documentation corrections of 2026-10-05) is the
version to archive, or whether to cut a new tag after the corrections and, if DC-1 says
"repair first", after the packing and pore repairs. The Zenodo archive must point at the tag
that is submitted.

### 1.3 Author identity — **AUTHOR, blocking**

`paper.md` currently carries two placeholders, both marked with `TODO` comments in the YAML
header:

- **Full legal name.** It is written as `Lucio Nájera Maldonado`, inferred from the GitHub
  handle and the project documents. **Confirm the exact spelling**, including accents and
  name order, before submission. The same name must appear identically in `paper.md`,
  `CITATION.cff` and the Zenodo record.
- **ORCID.** The field is commented out because an invented identifier is worse than a
  missing one. JOSS expects the submitting author to have an ORCID; register free at
  <https://orcid.org> and fill it in, in both `paper.md` and `CITATION.cff`.
- **Affiliation.** Currently `Independent researcher`. Replace it if there is an
  institutional affiliation to declare.

Also decide the **author list** itself. JOSS asks that it include everyone who made a
substantial contribution to the software. If the science was developed with advisors or
collaborators, that is a judgement only Lucio can make.

### 1.4 Statements at submission time — **AUTHOR, blocking**

On the submission form, JOSS asks the author to confirm there is no conflict of interest
with the handling editor, and to state the development history. Both are one-line answers,
but see [§5](#5-what-a-reviewer-will-probably-raise) on the development history: it needs a
sentence, because the git log understates the work.

---

## 2. Submission prerequisites

| Requirement | Status | Note |
|-------------|--------|------|
| Public repository with version control | **DONE** | <https://github.com/najera-maldonado/vlp-studio> |
| OSI-approved open source licence | **DONE** | AGPLv3-or-later, `LICENSE` at the root, full text |
| Licence is clearly stated | **DONE, with an open item** | Root `README.md`, every engine README, `THIRD_PARTY.md`. **Open (DC-5, AUTHOR):** the repository versions a copy of SIRAH 2.3 (146 files, including GPLv2 `tools/`) while describing SIRAH as user-supplied. Either remove the bundle (and have `fetch_data.sh` download it) or verify SIRAH's academic terms and declare the redistribution. Disclosed in the README and `THIRD_PARTY.md` as of 2026-10-05 |
| `paper.md` in the repository | **DONE** | Repository root |
| `paper.bib` with references | **DONE** | Repository root; **DOIs need verifying**, see §4.1 |
| Obvious research application | **DONE** | Enzyme-loaded VLP design; Gaucher disease case study |
| Substantial scholarly effort | **DONE** | ~15,000 lines of the project's own code, see below |
| Not a minor utility or thin wrapper | **DONE** | Four engines, an integrating funnel abstraction and a web application |
| Version-tagged release | **partly DONE** | Tags exist on the remote; which one to archive is the author's call, §1.2 |
| Archive with DOI | **AUTHOR** | §1.1 |
| Author name and ORCID | **AUTHOR** | §1.3 |

**Code volume**, for the "substantial scholarly effort" question, excluding the bundled
third-party SIRAH directory:

| Component | Lines |
|-----------|-------|
| Studio Python (`src/`, `tests/`) | 4,387 |
| Studio web assets (JS, CSS, templates) | 2,919 |
| Engine Python (Poromania, PackMan, sustratinaitor) | 4,268 |
| Engine shell, PyMOL and LEaP scripts | 3,394 |
| **Total** | **~14,968** |

This is well above the roughly 1,000-line guideline JOSS uses as a rough floor.

---

## 3. Reviewer checklist

### General checks

| Item | Status | Note |
|------|--------|------|
| Repository is public and complete | **DONE** | |
| Licence present and OSI-approved | **DONE** | |
| Contribution and authorship | **DONE** | `CONTRIBUTING.md`; authorship pending §1.3 |
| Substantial scholarly effort | **DONE** | See §2 |
| Data sharing | **DONE, with a caveat** | Default structure library ships in the repository; the heavy P22 capsid is fetched from RCSB by `nanocapsule-mvp/scripts/fetch_data.sh`. Caveat: 3 of the 4 enzyme inputs in `Input/Enzimas/` were overwritten in place by the centring step (with `.original` backups); `GCase_1OGS` has no backup (audit P-17) |
| Reproducibility | **OPEN** | `requirements.lock` and CI are in place. **Not in place:** the Packmol seed base in `config/default.yaml` is not read (production seeds are random, recorded per replica after the fact); the golden regression test covers the gate 1 cross-section only; the packing engine has no tests. Tasks PK-4 and PK-5 |
| Human or animal research | **DONE** | Not applicable: no human or animal subjects, no patient data |

### Functionality

| Item | Status | Note |
|------|--------|------|
| Installation instructions | **DONE** | `docs/installation.md`: Docker and local routes, requirements, troubleshooting, uninstall |
| Functionality works as described | **OPEN** | Gates 3 and 4 are documented as illustrative / never run and flag themselves `"illustrative": true`. Gates 1 and 2 **run but do not yet deliver what the earlier description promised**: a reviewer with Packmol installed who runs gate 2 obtains a capacity number that the acceptance criterion cannot distinguish from "no enzyme placed", and seeds they cannot declare in advance. The description has been corrected to match (README, engine READMEs, `paper.md`); the behaviour is the repair plan's Fase 0 (PK-1…PK-5) and PO-1/PO-3/PO-6/PO-7. See §5.1 |
| Performance claims | **DONE** | No performance claims are made in the paper, so none need substantiating |
| Automated tests | **DONE, with a caveat** | 22 tests (17 smoke, 5 golden on `substrate_section`), run in CI on every push and pull request, plus a `compileall` pass over the other three engines. **Caveat a reviewer will see:** none of the 22 tests touches the packing engine, and all 22 pass with the audit's blocking defects present. Task PK-5 adds engine tests with a Packmol double |

### Documentation

| Item | Status | Note |
|------|--------|------|
| Statement of need | **DONE** | `paper.md`, and summarised in the root `README.md` |
| Installation instructions | **DONE** | `docs/installation.md`, including the non-redistributable engines |
| Example usage | **DONE** | `docs/usage.md`: gate-by-gate walkthrough on the Gaucher case with runnable commands |
| Functionality documentation | **DONE** | All ~30 REST endpoints documented in `nanocapsule-mvp/README.md`; each engine has its own README with pipeline and requirements |
| Automated tests documented | **DONE** | `docs/installation.md` and `CONTRIBUTING.md`, including an explicit statement of what the suite does **not** cover |
| Community guidelines | **DONE** | `CONTRIBUTING.md`: how to report a bug, how to contribute, scope boundaries, code of conduct |

### Software paper

| Item | Status | Note |
|------|--------|------|
| Summary for a non-specialist | **DONE** | |
| Statement of need | **DONE** | Names the gap: the engines exist, the composed workflow does not |
| State of the field | **DONE** | Each wrapped engine cited; the absence of an integrating tool stated |
| Quality of writing | **DONE** | English throughout; worth one read-through by Lucio for voice |
| References with DOIs | **OPEN** | 19 entries, every one cited and every citation resolved; DOIs need verifying, see §4.1 |
| Paper length | **DONE, slightly long** | ~1,060 words of body text against JOSS's 250–1,000 guideline. Within tolerance; the *Current scope and limitations* section is the one to trim if an editor asks, and it is the section least worth cutting |

---

## 4. Open items that do not need Lucio

### 4.1 Verify every DOI in `paper.bib` — **OPEN, blocking for the paper**

JOSS runs an automated Crossref check on every DOI and reviewers see the failures. The
bibliography holds 19 entries, all cited and all resolving to an entry, but the DOIs have
**not been resolved against Crossref**, and two should be checked with particular care:

- `smart1996` (HOLE) — the 1996 *Journal of Molecular Graphics* paper is sometimes indexed
  under a 1997 DOI prefix.
- `rose2018` (NGL viewer) — NGL has more than one publication and they are easy to mix up.

The two `@misc` entries, RDKit and PyMOL, have no Crossref DOI; that is correct, not an
omission.

### 4.2 Translation of the remaining Spanish — **OPEN, not blocking**

Now in English: the root README, all four engine READMEs, `docs/installation.md`,
`docs/usage.md`, `CONTRIBUTING.md`, `paper.md`.

Still in Spanish, deliberately: `ESTADO.md`, `PENDIENTES.md`, `BITACORA.md`,
`REVISION_MOTORES.md`, `INVESTIGACION_*.md`. These are the author's decision log and audit
trail rather than user documentation, and the root README says so. JOSS requires the
*documentation* to be in English, which it now is.

Still in Spanish and likely to draw a reviewer comment, though not a requirement:

- **The Studio interface.** Tab labels and messages are Spanish. A bilingual interface is
  already on the project's own task list.
- **Code comments, docstrings and API error messages.** JOSS does not require English code,
  but reviewers reading the source will notice.
`CITATION.cff` was in Spanish and has been translated as part of this preparation; see 4.3.

### 4.3 `CITATION.cff` — **partly DONE, rest AUTHOR**

**DONE:** `message` and `abstract` are now in English, the author entry is structured as a
person rather than a handle, and `gaucher-disease` was added to the keywords.

Still needed, all **AUTHOR**: confirm the name spelling and uncomment the `orcid:` field
(§1.3), add the Zenodo `doi:` once minted (§1.1), and update `date-released` to the date of
the tagged release. Both outstanding fields are marked with `TODO` comments in the file.

### 4.4 Documentation drift already fixed — **DONE**

Recorded here because the previous documentation was wrong in ways a reviewer would have
caught immediately, and the fixes are part of this preparation:

- The old Studio README documented five endpoints that **do not exist**
  (`/api/structures`, `/api/radius/{capsid}`, `/api/generate_pdb`, `/api/download/{exp_id}`)
  and none of the roughly thirty that do. Replaced with the real list.
- It pointed users at port 5001; the server runs on 5000.
- The Poromania README documented `clickaqui.sh` and `automated_test.py`, **neither of which
  is in the repository**, and carried placeholder contact details, a placeholder ORCID, a
  BibTeX entry reading `[Tu nombre]`, and a roadmap promising a mobile app and machine
  learning. All removed.
- `/api/pore/profile` was presented as a pore measurement. It is an analytic placeholder and
  is now documented as such, with `/api/pore/run_hole` identified as the real measurement.

Still-fossil documents **not** rewritten here, because they are internal and the root README
now points at `ESTADO.md` as authoritative: `nanocapsule-mvp/CLAUDE.md`,
`DEVELOPMENT_PLAN.md`, `TECHNICAL_IMPROVEMENTS.md`, `SESION_STUDIO.md`,
`BACKEND_FRONTEND_ARCHITECTURE.md`, `PLAN_POROMANIA.md`. `ESTADO.md` §4 records that
`TECHNICAL_IMPROVEMENTS.md` marks seven modules as done that were never created, and that
`SESION_STUDIO.md` cites a file that does not exist. **Consider deleting them before
submission** (**OPEN**): a reviewer who opens one will find claims that contradict the
software, and they serve no purpose now.

---

## 5. What a reviewer will probably raise

Prepared answers, so none of these is a surprise. All of them are honest positions rather
than things to hide.

### 5.1 "Two of your four gates do not work" — now: "none of the four is validated"

The accurate statement, after the audits of 2026-10-04, is: gates 1 and 2 have real engines
wired end to end whose headline numbers are **not yet validated** (gate 2's acceptance
criterion is broken and seeds are random; gate 1's only committed result is the wild type
measured off-axis and is marked invalid in place); gate 3 is a placeholder; gate 4 has never
run and its committed inputs are stubs. This is now stated consistently in the paper, the
README, every engine README, the usage documentation, and at runtime through the
`"illustrative": true` flag.

JOSS asks that functionality match its description, not that software be finished. The
defensible position is therefore one of two, and it is decision DC-1 of the repair plan:

- **Repair first** (recommended by the audits, ~6 days: PK-1…PK-5, PO-1, PO-3, PO-6, PO-7),
  then describe gates 1 and 2 as real; or
- **Submit now**, describing gates 1 and 2 as "engine wired, result under review" — which
  is what the documentation says today — and the engine wrappers, the composed workflow, the
  pinned environment and the explicit status reporting as the contribution.

What is no longer defensible is the earlier wording ("real, end to end", "deterministic
packing with golden test"), because the repository itself refutes it. Do not soften the
current labelling during review; it is the feature of the submission.

### 5.2 "The git history is two days long"

It is: 47 commits between 2026-09-17 and 2026-09-18, because the repository was created from
work that already existed. The science predates the repository by a long way. **Lucio should
state the real development timeline in the submission notes**, because a reviewer checking
"substantial scholarly effort" against the commit log alone will reach the wrong conclusion.
The ~15,000 lines in §2 are the better measure.

### 5.3 "I cannot run gate 1 — HOLE is not installed"

Expected, and it is a licensing constraint rather than an oversight: HOLE's academic licence
forbids redistribution, so bundling it in a public Docker image would violate its terms.
`docs/installation.md` explains how to obtain and mount it, `/api/health` reports its
absence explicitly, and `THIRD_PARTY.md` records the licence. Reviewers can still exercise
gate 2, the substrate cross-section calculation, Vina docking, the library and the whole test
suite without it.

A reviewer who wants to verify gate 1 must install HOLE themselves. **Consider offering to
walk the assigned reviewer through it** in the review thread.

### 5.4 "The same science is implemented twice"

True, and documented in `nanocapsule-mvp/README.md` and the Poromania README: the Studio
reimplemented in Python the pore, screening and docking logic that also exists in Poromania
as shell scripts, so the two can diverge. It is recorded as known architectural debt with a
rule attached — a correction must be made deliberately on one side — rather than presented
as a design.

### 5.5 "Why AGPLv3 for research software?"

Deliberate: the project anticipates being offered as a web service, and AGPL's network
clause keeps modified versions open in that case. It is OSI-approved, so it satisfies JOSS,
and it is compatible with the GPL and LGPL engines the project calls.

### 5.6 "No molecular dynamics results" — and "the inputs are stubs"

Correct on both counts, and the author's own standing instruction is that **no dynamics
result from this project should be treated as validated**. A reviewer who opens
`PackMan.v.1.2/archivos_dm_cg/*.in` will find `nstlim = 500` under titles reading "15ns" and
"35ns", and eight all-atom inputs in a coarse-grained protocol; the PackMan README now says
so first. The honest answer is that the committed files are the scaffold of a protocol, that
the audit identified exactly what is wrong (`AUDITORIA_MD.md`, tasks MD-1…MD-10 with the
corrected inputs written out in `PLAN_REPARACION_MD.md`), and that running it depends on
repairing the preparation path first and on GPU access second.

### 5.7 "Your own documentation contradicted your code"

It did, and the repository says so rather than hiding it: `CORRECCIONES_DOCUMENTACION.md`
lists every overturned claim with file, line, evidence and replacement. The audits were
commissioned by the author before the submission and their findings were applied to the
documentation before submitting. That is the defensible position; do not remove the record.

---

## 6. Suggested order of work

0. **Lucio:** decide DC-1 (repair gates 1 and 2 before submitting, or submit with them
   labelled "under review") and DC-5 (SIRAH bundle). Everything below is the same either way;
   only the timing changes.
1. **Lucio:** confirm the name, register or supply the ORCID, decide the affiliation and the
   author list (§1.3).
2. **Anyone:** verify the `paper.bib` DOIs against Crossref (§4.1).
3. **Anyone:** optionally delete the fossil planning documents (§4.4).
4. **Lucio:** read `paper.md` end to end. It is written in a voice that is not his, and the
   statement of need should be a claim he is willing to defend in review.
5. **Lucio:** tag the release (§1.2).
6. **Lucio:** enable Zenodo, confirm the archive metadata matches, add the DOI to the README
   and `CITATION.cff` (§1.1).
7. **Lucio:** submit at <https://joss.theoj.org/papers/new> with the repository URL, the
   archive DOI, the version tag and a note on the development timeline (§5.2).

Expect review to be public, conversational and iterative: reviewers open issues on this
repository, and responding to them is part of the process rather than a sign something went
wrong.
