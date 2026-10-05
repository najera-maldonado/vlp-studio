---
title: 'VLP Studio: a four-gate computational funnel for designing enzyme-loaded virus-like particle nanocapsules'
tags:
  - Python
  - structural biology
  - virus-like particles
  - enzyme encapsulation
  - protein engineering
  - molecular dynamics
  - drug delivery
authors:
  # TODO (author): confirm the exact spelling of your full legal name before submission,
  # and add your ORCID — JOSS requires at least one author with an ORCID.
  - name: Lucio Nájera Maldonado
    # orcid: 0000-0000-0000-0000
    affiliation: 1
affiliations:
  # TODO (author): replace with your institution, or keep "Independent researcher".
  - name: Independent researcher
    index: 1
date: 4 October 2026
bibliography: paper.bib
---

# Summary

Virus-like particles (VLPs) are self-assembling protein shells that can be loaded with a
cargo enzyme to act as nanoreactors: the shell protects the enzyme and shields it from the
immune system, while its pores let substrate in and product out [@patterson2012; @comellas2007].
Designing such a particle is not one question but several independent ones, each able to kill
a candidate on its own — and the expensive questions are not the ones that eliminate most
candidates.

**VLP Studio** organises that design problem as a **four-gate funnel**. Each gate asks one
physical question — does the substrate fit *through* the pore, does the enzyme fit *inside*
the shell, can the enzyme be de-immunised to survive *outside*, does the assembly *survive*
molecular dynamics — and a candidate must pass each gate before the next, more expensive one
is attempted. The platform pairs a web interface and 3D viewer with four independently
versioned engines that wrap established scientific software: HOLE [@smart1996] for pore
geometry, PyMOL [@pymol] for mutagenesis, RDKit [@rdkit] for substrate geometry, AutoDock
Vina [@trott2010] and Open Babel [@oboyle2011] for docking, Packmol [@martinez2009] for
packing, and AMBER [@case2005] with the SIRAH coarse-grained force field
[@darre2015; @machado2019] for dynamics.

The driving use case is enzyme replacement therapy for **Gaucher disease**, in which
glucocerebrosidase [@dvir2003] is deficient and its substrate glucosylceramide accumulates
[@grabowski2008]. That enzyme's structure ships with the repository as the worked example.

# Statement of need

Each step of VLP nanocapsule design already has good software, but the steps have no shared
workflow. A researcher asking whether a given enzyme can be usefully encapsulated in a given
capsid must currently run HOLE by hand on a pore structure, build mutants in PyMOL, compute a
substrate cross-section in RDKit, dock with Vina or a comparable engine, pack with Packmol,
and build a coarse-grained system for AMBER or GROMACS [@abraham2015] — each with its own
input conventions, each producing output the next step cannot read directly. The glue is
invariably ad-hoc scripting, which is where reproducibility is lost: the numbers survive, but
the parameters, versions and random seeds that produced them usually do not.

VLP Studio addresses three gaps.

**It composes the engines into one workflow with a common vocabulary.** The funnel is not a
presentational device but the ordering principle: the cheap geometric filters come first,
so a candidate whose substrate cannot physically traverse the pore is eliminated
before any GPU time is spent on dynamics. Gate 1 makes that comparison quantitative — the
minimum cross-sectional radius of the substrate, from its SMILES string, against the minimum
pore radius measured by HOLE on the structure's own principal symmetry axis. When the native
pore is too narrow, the same gate screens a mutant library for variants that widen it,
applying mutations symmetrically across all chains as the assembly's symmetry requires, then
docks the substrate into each variant to check that a wider pore still binds it.

**It is built so that the geometric results can be made reproducible.** Packing is
stochastic in Packmol, so a single run is not an answer; VLP Studio runs a replicated
experiment and records the seed of every replica alongside its output, so that any past run
can be identified and repeated. The Python environment is pinned to exact versions, and the
same lock file is used by the container image and by continuous integration. A "golden"
regression test freezes known numerical results of the substrate cross-section calculation,
so a change to that geometry code is caught even when nothing crashes. Two limits of the
current release must be stated: the configured seed base is not yet honoured by the
production path (replicas draw random seeds, recorded after the fact), and the packing
engine itself has no automated tests; both are open items in the repository's repair plan.

**It is explicit about what is measured and what is not.** Research software in this area
frequently presents placeholder output indistinguishably from computed output. Here, every
API response that is illustrative carries an `"illustrative": true` flag, real measurements
name the engine that produced them, and the interface and documentation label the
distinction. The repository also carries, in its root and in each engine's README, the
findings of an independent audit of the engines (October 2026) and a list of every
documentation claim that audit overturned, with the evidence. Engines that cannot legally
be redistributed, such as HOLE and NetMHCIIpan [@reynisson2020], are documented as
user-supplied rather than quietly bundled.

# Software description

The platform is a monorepo of four independently versioned components.

**The Studio** (`nanocapsule-mvp`) is a Flask application with an NGL [@rose2015; @rose2018]
3D viewer, layered so that the HTTP routes contain no science: orchestration lives in one
service module per gate, with the domain logic below that. It exposes about thirty REST
endpoints, including a health endpoint reporting which engines and dependencies are actually
present, so a user always knows which gates will work in their installation.

**Poromania** is the gate 1 engine: it identifies pore-lining residues, generates mutants
systematically, measures each with HOLE under the same parameters, and docks a substrate
into every variant to correlate pore radius with binding affinity. It handles large flexible
ligands; glucosylceramide has 125 atoms. The Studio's own implementation of the same
analysis derives the pore axis from the structure's symmetry (second-moment tensor), which
is the definition the project is converging on.

**PackMan** is the gate 4 engine: scripts to prepare the enzyme-inside-capsid system for
coarse-grained MD (packing, conversion to SIRAH beads, system building with LEaP), the AMBER
input files for minimisation, equilibration and production, and a cpptraj analysis stage
emitting the trajectory observables the Studio is designed to display.

**sustratinaitor** parametrises the substrate — glucosylceramide had no SIRAH parameters, so
its all-atom model was parametrised with GAFF2 [@wang2004] and AM1-BCC charges via
antechamber [@wang2006] — converts the capsid to SIRAH beads, and packs 200 copies of the
substrate around the capsid as a starting configuration for dynamics.

# Current scope and limitations

The status below reflects an independent audit of the four engines carried out in October
2026, after the first draft of this paper; the earlier draft overstated what had been
validated, and the repository documents each correction.

Gates 1 and 2 have real engines wired end to end, but **neither has produced a validated
measurement yet**. In gate 2 the acceptance test that decides whether a packing converged
parses a Packmol log line that Packmol does not write, and its fallback accepts the capsid
alone, so the capacity the engine reports is not yet a measurement; the fix is a small,
identified change with a test double. In gate 1 the only pore profile committed to the
repository was measured on an unmutated structure with the HOLE seed point off the symmetry
axis, and is marked invalid in place. Gate 3 is a placeholder: no epitope predictor is wired
in, and its endpoint declares itself illustrative. Gate 4's **molecular dynamics has not
been executed, and the committed inputs do not constitute a runnable protocol**: the three
SIRAH stages are 10 ps test stubs (about 240 ps in total, against roughly 1 µs in the
reference SIRAH protocol), eight further inputs are all-atom files applied to a
coarse-grained topology, and the automated preparation path produces a topology without
hydrogens or chain terminators. The corresponding interface tab shows synthetic curves,
labelled as such; no dynamics result in this repository should be treated as validated.
Three scientific decisions are recorded as open rather than silently resolved — an
internal-radius safety margin, the coarse-grained versus all-atom resolution of the
substrate system, and the heating protocol — and the audit gives a recommendation for each.
The Studio is a single-user local research server, without authentication or a job queue.
It is research software, not a clinical tool.

The project's next steps, in the order the repair plan fixes them, are: a correct
acceptance criterion, seed handling and tests for the packing engine; a single, validated
definition of the pore channel with verified mutagenesis; and a system-preparation path and
SIRAH protocol for gate 4 that can actually be run. The software is published now because
the engine wrappers, the composed workflow, the pinned environment and the explicit status
reporting are useful on their own, and because publishing them — audit findings included —
makes the scientific work that follows auditable.

# Acknowledgements

VLP Studio coordinates established open scientific software rather than replacing it. The
author thanks the developers and maintainers of HOLE, PyMOL, Packmol, RDKit, Open Babel,
AutoDock Vina, AMBER, GROMACS, the SIRAH force field and NGL.

# References
